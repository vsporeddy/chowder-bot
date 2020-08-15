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

tokenizer = nltk.tokenize.RegexpTokenizer(r"\w+")
lemmatizer = WordNetLemmatizer()

class Chowder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam.start()
        self.revive.start()
        self.fomo.start()
        self.promotions = {}
        self.demotions = {}

    def cog_unload(self):
        self.spam.cancel()
        self.revive.cancel()
        self.fomo.cancel()

    @tasks.loop(seconds=60)
    async def spam(self):
        """Chowder bot can't contain himself"""
        channel = self.bot.get_channel(config["default_channel"])
        last_message = channel.last_message
        if not last_message or last_message.author == self.bot.user:
            return
        if (datetime.utcnow() - channel.last_message.created_at).seconds >= config["spam_cooldown"]:
            await channel.send(get_spam_quote())

    @tasks.loop(seconds=60)
    async def revive(self):
        """Chowder bot tries to revive the dead server"""
        channel = self.bot.get_channel(config["default_channel"])
        last_message = channel.last_message
        if not last_message or (datetime.utcnow() - channel.last_message.created_at).seconds < config["revive_cooldown"]:
            return
        boys = [user for user in channel.members if user.status == discord.Status.online \
                and user.top_role.position >= config["role_req"]]
        if len(boys) < config["min_revival_users"]:
            return

        await channel.send("Time to revive this dead server boys, poll:")
        chosen_boys = random.sample(boys, 2)
        activity = get_activity()
        poll = await channel.send(f"Who's better at {activity}, {chosen_boys[0].mention} ({config['option_1']}) or \
{chosen_boys[1].mention} ({config['option_2']})? Vote in the next {config['voting_time']} seconds.")

        await poll.add_reaction(config["option_1"])
        await poll.add_reaction(config["option_2"])

        await asyncio.sleep(config["voting_time"])
        poll = await channel.fetch_message(poll.id)
        votes1 = await discord.utils.find(lambda r: str(r.emoji) == config["option_1"], poll.reactions).users().flatten()
        votes2 = await discord.utils.find(lambda r: str(r.emoji) == config["option_2"], poll.reactions).users().flatten()

        winner, loser = chosen_boys[0], chosen_boys[1] if len(votes1) > len(votes2) else chosen_boys[1], chosen_boys[0]
        tie = f"I voted for {winner.mention} btw" if len(votes1) == len(votes2) else None

        await channel.send(f"It's decided, {winner.mention} is the best on paper at {activity}!")
        await channel.send(f"{winner.mention} wins 5 ChowderCoin™️ and all voters get 1 each. {loser.mention} is \
deducted 10 ChowderCoin™️")
        # TODO @TimmahC award ChowderCoins
        if tie:
            await channel.send(tie)

    @tasks.loop(seconds=60)
    async def fomo(self):
        """Chowder bot doesn't want to miss out on the fun"""
        guild = self.bot.get_guild(config["guild_id"])
        channel = discord.utils.find(lambda c: len(c.members) >= config["fomo_threshold"], guild.voice_channels)
        voice = discord.utils.get(self.bot.voice_clients, guild=guild)
        if not channel and (not voice or not voice.is_connected()):
            return
        if not channel and voice and voice.is_connected():
            await voice.disconnect()
            await self.bot.get_channel(config["default_channel"]).send(f"{config['rip_emote']} uh, bye?")
            return
        if channel and voice and voice.channel == channel:
            return
        if channel and voice and voice.is_connected():
            await voice.move_to(channel)
        elif channel:
            voice = await channel.connect()
            await voice.main_ws.voice_state(guild.id, channel.id, self_mute=True)
        await self.bot.get_channel(config["default_channel"]).send(f"{config['happy_emote']} {get_join_phrase()} \
{get_condescending_name()}s?")

    @spam.before_loop
    @revive.before_loop
    @fomo.before_loop
    async def before_spam(self):
        print('waiting...')
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id not in config["channels"] or message.author == self.bot.user:
            return
        name = get_name(message.author)
        await message.channel.send(f"Whoa {message.author.mention} why you deleting messages {name}? Sketch")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.channel.id not in config["channels"] or before.author == self.bot.user:
            return
        name = get_name(before.author)
        await before.channel.send(f"Whoa {before.author.mention} why you editing messages {name}? Sketch")

    @commands.command(name="promote", brief="Nominate a user for promotion.")
    async def promote(self, ctx):
        await self.nomination_helper(ctx, True)

    @commands.command(name="demote", brief="Nominate a user for demotion.")
    async def demote(self, ctx):
        await self.nomination_helper(ctx, False)

    async def nomination_helper(self, ctx, is_promotion):
        if ctx.channel.id not in config["channels"] or ctx.author == self.bot.user:
            return
        nominator = ctx.author
        name = get_name(nominator)
        if not ctx.message.mentions:
            await ctx.send(f"Gotta mention someone to nominate them, {name}")
            return
        nominee = ctx.message.mentions[0]
        if nominee.id == nominator.id:
            simps = "symphs" if is_promotion else "haters"
            await ctx.send(f"Can't nominate yourself {name}, get one of your {simps} to do it.")
            return
        if nominee == self.bot.user:
            message = "I appreciate the thought but I'm happy at my rank, " if is_promotion else \
                        "Nice try, can't demote me "
            await ctx.send(f"{message} {name}")
            return
        if (is_promotion and nominee.top_role.position + 1 >= config["promotion_cap"]) or \
            (not is_promotion and nominee.top_role.position >= config["promotion_cap"]):
            await ctx.send(f"Sorry {name}, no democratic promotions/demotions at **{nominee.top_role.name}** \
rank. Please contact a board member for a manual review.")
            return
        if not is_promotion and nominee.top_role.position <= config["promotion_floor"]:
            await ctx.send(f"Leave poor {nominee.mention} alone, they're only **{nominee.top_role.name}** rank.")
            return
        nominees = self.promotions if is_promotion else self.demotions
        promotion_str = "promotion" if is_promotion else "demotion"
        if nominee.id not in nominees:
            nominees[nominee.id] = set([nominator.id])
        elif nominator.id in nominees[nominee.id]:
            await ctx.send(f"Settle down {name}, you already nominated {nominee.mention} for a {promotion_str}")
            return
        else:
            nominees[nominee.id].add(nominator.id)

        noms_needed = config["min_nominations"] - len(nominees[nominee.id])
        if noms_needed > 0:
            await ctx.send(f"Hey {get_condescending_name()}s, {nominator.mention} has nominated {nominee.mention} \
for a {promotion_str}. They need {noms_needed} more nominations.")
            return
        else:
            current_rank = nominee.top_role
            increment = 1 if is_promotion else -1
            roles = self.bot.get_guild(config["guild_id"]).roles
            new_rank = discord.utils.find(lambda r: r.position == current_rank.position + increment, roles)
            nominees[nominee.id] = set([])

            await nominee.add_roles(new_rank)
            await nominee.remove_roles(current_rank)

            if is_promotion:
                await ctx.send(f"{config['happy_emote']} Congratulations {nominee.mention}, you just got promoted from \
**{current_rank.name}** to **{new_rank.name}**!")
            else:
                await ctx.send(f"{config['rip_emote']} Yikes {nominee.mention}, by popular demand you've been demoted \
down to **{new_rank.name}** rank.")

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
    async def on_message(self, message):
        if message.channel.id not in config["channels"] or message.author == self.bot.user:
            return
        name = get_name(message.author)
        comment = message.content.strip().lower()

        if comment == "chowder pls":
            return f"You seem confused {name}, try *chowder pls help*"

        if "chowder" in comment and "pls" not in comment:
            tokens = tokenizer.tokenize(comment)
            lemmas = [lemmatizer.lemmatize(t) for t in tokens]

            for lemma in lemmas:
                if lemma in speech["triggers"]:
                    intent = speech["triggers"][lemma]
                    response = random.choice(speech['responses'][intent]).format(name=name, word=lemma)
                    await message.channel.send(response)
                    return
            await message.channel.send(f"Uhh what? Speak up {name}, or say *chowder pls help*")

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

def setup(bot):
    bot.add_cog(Chowder(bot))
