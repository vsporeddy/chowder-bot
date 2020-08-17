"""
    Represents Chowder bot's personality
"""

import json
import random
import asyncio
import discord
import sqlite3 as sqlite
import nltk
from nltk.stem import WordNetLemmatizer
from datetime import datetime
from discord.ext import tasks, commands

with open("chowder/chowder_config.json", "r") as read_file:
    config = json.load(read_file)

with open("chowder/speech.json", "r") as read_file:
    speech = json.load(read_file)

channels = config["channels"]

nltk.download("wordnet")
tokenizer = nltk.tokenize.RegexpTokenizer(r"\w+")
lemmatizer = WordNetLemmatizer()


class Chowder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam.start()
        self.revive.start()
        self.fomo.start()

    def cog_unload(self):
        self.spam.cancel()
        self.revive.cancel()
        self.fomo.cancel()

    @tasks.loop(seconds=random.randrange(config["spam_cooldown"]))
    async def spam(self):
        """Chowder bot can't contain himself"""
        channel = self.get_default_channel()
        last_message = channel.last_message
        if not last_message or last_message.author == self.bot.user:
            return
        await channel.send(get_spam_quote())

    @tasks.loop(seconds=60)
    async def revive(self):
        """Chowder bot tries to revive the dead server"""
        channel = self.get_default_channel()
        last_message = channel.last_message
        names = get_collective_name()
        if not last_message or (datetime.utcnow() - channel.last_message.created_at).seconds < config["revive_cooldown"]:
            return
        boys = [user for user in channel.members if user.status == discord.Status.online
                and user.top_role.position >= config["role_req"]]
        if len(boys) < config["min_revival_users"]:
            return

        await channel.send(f"Time to revive this dead server, {names}, poll:")
        chosen_boys = random.sample(boys, 2)
        activity = get_activity()
        poll = await channel.send(
            f"Who's better at {activity}, {chosen_boys[0].mention} ({config['option_1']}) or "
            f"{chosen_boys[1].mention} ({config['option_2']})? Vote in the next {config['voting_time']} seconds."
        )

        await poll.add_reaction(config["option_1"])
        await poll.add_reaction(config["option_2"])

        await asyncio.sleep(config["voting_time"])
        poll = await channel.fetch_message(poll.id)
        votes1 = await discord.utils.find(lambda r: str(r.emoji) == config["option_1"], poll.reactions).users().flatten()
        votes2 = await discord.utils.find(lambda r: str(r.emoji) == config["option_2"], poll.reactions).users().flatten()

        if len(votes1) > len(votes2):
            winner = chosen_boys[0]
            loser = chosen_boys[1]
        else:
            winner = chosen_boys[1]
            loser = chosen_boys[0]

        tie = f"I voted for {winner.mention} btw" if len(votes1) == len(votes2) else None

        await channel.send(f"It's decided, {names}. {winner.mention} is the best at {activity}! (on paper)")
        await channel.send(
            f"{winner.mention} wins 5 ChowderCoin™️ and all voters get 1 each. {loser.mention} is "
            f"deducted 10 ChowderCoin™️."
        )
        # TODO @TimmahC award ChowderCoins
        if tie:
            await channel.send(tie)

    @tasks.loop(seconds=60)
    async def fomo(self):
        """Chowder bot doesn't want to miss out on the fun"""
        guild = self.get_default_guild()
        voice_channel = max(guild.voice_channels, key=lambda c: len(c.members))
        if len(voice_channel.members) < config["fomo_threshold"]:
            voice_channel = None
        text_channel = self.get_default_channel()
        voice = discord.utils.get(self.bot.voice_clients, guild=guild)
        names = get_collective_name()

        if not voice_channel and (not voice or not voice.is_connected()):
            return
        if not voice_channel and voice and voice.is_connected():
            print(f"No populated voice channels, disconnecting from {voice.channel.name}")
            await voice.disconnect()
            await text_channel.send(get_goodbye().format(name=names))
            return
        if voice_channel and voice and voice.channel == voice_channel:
            return
        elif voice_channel and voice and voice.is_connected():
            print(f"Moving from {voice.channel.name} to {voice_channel.name}")
            await voice.disconnect()
            voice = await voice_channel.connect()
            await voice.main_ws.voice_state(guild.id, voice_channel.id, self_mute=True)
            print(f"Successfully moved from {voice.channel.name} to {voice_channel.name}")
            return
        elif voice_channel:
            print(f"Connecting to voice channel {voice_channel.name}")
            voice = await voice_channel.connect()
            await voice.main_ws.voice_state(guild.id, voice_channel.id, self_mute=True)
            await text_channel.send(get_join_phrase().format(names=names))

    @spam.before_loop
    @revive.before_loop
    @fomo.before_loop
    async def before_spam(self):
        print('waiting...')
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id not in channels or message.author == self.bot.user:
            return
        name = get_name(message.author)
        await message.channel.send(f"Whoa {message.author.mention} why you deleting messages {name}? Sketch")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.channel.id not in channels or before.author == self.bot.user:
            return
        name = get_name(before.author)
        await before.channel.send(f"Whoa {before.author.mention} why you editing messages {name}? Sketch")

    """Chowder coin stuff"""
    @commands.command(name="balance", brief="Check current balance of Chowder coins.")
    async def balance(self, ctx):
        bal = get_balance(ctx.author.id)
        if (bal == None):
            await ctx.send(ctx.author.mention + " has no account. Making a new one for you.")
            new_account(ctx.author.id, ctx.author.name)
        else:
            await ctx.send(ctx.author.mention + f" currrently has {bal} coins.")

    @commands.command(name="give", brief="Transfer coins from one user to another.")
    async def give(self, ctx, *args):
        sender = ctx.author
        if (get_balance(sender.id) == None):
            await ctx.send(ctx.author.mention + " You don't have an account. Go make one first.")
            return
        mentions = ctx.message.mentions
        if (len(args) != 2 or len(mentions) != 1):
            await ctx.send("You seem a bit confused, " + get_condescending_name() + ". Maybe you should look for help.")
            return
        rec = getUserFromMention(self, args[0])
        if (rec != None):
            response = give_checker(sender.id, rec, args[1])
            amount = args[1]
        else:
            rec = getUserFromMention(self, args[1])
            response = give_checker(sender.id, rec, args[0])
            amount = args[0]
        if (response[0] == 1):
            if(transfer(sender.id, rec, int(amount))):
                await ctx.send(f"<@{sender.id}> has sent some coins to <@{rec}>")
        else:
            await ctx.send(response[1])

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.get_default_channel()
        await channel.send(f"{get_collective_name()}, please welcome {member.mention} {get_emote()}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id not in channels or message.author == self.bot.user:
            return
        name = get_name(message.author)
        comment = message.content.strip().lower()

        if comment == "chowder pls":
            return f"You seem confused {name}, try *chowder pls help*"

        prev_message = (await message.channel.history(limit=1, before=message).flatten())
        addressing_chowder = prev_message and prev_message[0].author == self.bot.user \
            or ("chowder" in comment and "pls" not in comment)
        if addressing_chowder:
            if message.content.isupper():
                await message.channel.send(get_caps_response().format(name=name))
                return
            tokens = tokenizer.tokenize(comment)
            lemmas = [lemmatizer.lemmatize(t) for t in tokens]

            for lemma in lemmas:
                if lemma in speech["triggers"]:
                    intent = speech["triggers"][lemma]
                    response = random.choice(speech['responses'][intent]).format(name=name, word=lemma)
                    await message.channel.send(response)
                    return

    def get_default_channel(self):
        return self.bot.get_channel(config["default_channel"])

    def get_default_guild(self):
        return self.bot.get_guild(config["guild_id"])


def get_name(author):
    name = get_respectful_name() if author.top_role.position >= config["respect_req"] else get_condescending_name()
    return name


def get_condescending_name():
    return random.choice(speech["condescending_names"])


def get_activity():
    return random.choice(speech["activities"])

def getUserFromMention(self, mention):
    if (not mention):
        return
    if (mention.startswith('<@') and mention.endswith('>')):
        mention = mention[2:-1]
        if (mention.startswith('!')):
            mention = mention[1:]
        return int(mention)

"""Use this method to get the current balance of any user, based on id"""
def get_balance(id):
    conn = sqlite.connect(config["DATABASE"])
    c = conn.cursor()
    query = f"SELECT balance FROM accounts WHERE id = {id}"
    bal = c.execute(query).fetchone()
    conn.close()
    if (bal == None):
        return None
    else:
        return int(bal[0])

def new_account(id, name, balance=0):
    conn = sqlite.connect(config["DATABASE"])
    c = conn.cursor()
    c.execute(f"INSERT INTO accounts('id', 'name', 'balance') VALUES ('{id}', '{name}', 0)")
    conn.commit()
    conn.close()

def give_checker(send_id, rec_id, amount):
    response = [-1, "Default error"]
    if (send_id == rec_id):
        response = [-1, "Sending money to yourself? That's sad."]
    elif (get_balance(rec_id) == None):
        response = [-1, "You're sending coins to someone who doesn't have an account."]
    elif (amount.isdigit()):
        amount = int(amount)
        if (amount < 1):
            response = [-1, "Invalid amount of coins."]
        elif (amount > get_balance(send_id)):
            response = [-1, "Looks like you don't have enough coins, " + get_condescending_name() + "."]
        else:
            response = [1, "Success"]
    return response

"""Updates the balance of both sender and receiver and leaves a record in transactions."""
def transfer(send_id, rec_id, amount):
    if (rec_id == 1):
        #transfer to and from nothing
        update_balance(send_id, amount)
    else:
        update_balance(send_id, -1*amount)
        update_balance(rec_id, amount)
    conn = sqlite.connect(config["DATABASE"])
    c = conn.cursor()
    c.execute(f"INSERT INTO TRANSACTIONS (receiver_id, amount, sender_id) \
                    VALUES ({rec_id}, {amount}, {send_id})")
    conn.commit()
    conn.close()
    return 1

"""Update user's balance by 'x' amount. 'x' can be positive or negative"""
def update_balance(id, amount):
    conn = sqlite.connect(config["DATABASE"])
    c = conn.cursor()
    new_bal = get_balance(id) + amount
    c.execute(f"UPDATE accounts SET balance = {new_bal} where id = {id}")
    conn.commit()
    conn.close()

def get_respectful_name():
    return random.choice(speech["respectful_names"])


def get_join_phrase():
    return random.choice(speech["join_phrases"])


def get_spam_quote():
    return random.choice(speech["spam_quotes"])


def get_goodbye():
    return random.choice(speech["spam_quotes"])


def get_collective_name():
    return random.choice(speech["collective_names"])


def get_emote():
    return random.choice(speech["emotes"])


def get_caps_response():
    return random.choice(speech["caps_responses"])


def setup(bot):
    bot.add_cog(Chowder(bot))
