"""
    Represents Chowder bot's personality
"""

import json
import random
import asyncio
import discord
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
nltk.download("words")
tokenizer = nltk.tokenize.RegexpTokenizer(r"\w+")
lemmatizer = WordNetLemmatizer()


class Chowder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam.start()
        self.revive.start()

    def cog_unload(self):
        self.spam.cancel()
        self.revive.cancel()

    @tasks.loop(seconds=config["spam_cooldown"])
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
                and user.roles[-1].position >= config["role_req"]]
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
            f"{winner.mention} wins 0.10 ChowderCoin™️ and. {loser.mention} is deducted 0.05 ChowderCoin™️."
        )
        cc_cog = self.bot.get_cog("ChowderCoin")
        await cc_cog.add_coin(winner, 0.1)
        await cc_cog.subtract_coin(loser, 0.05)
        if tie:
            await channel.send(tie)

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
            #If current voice channel has same amount of members do not switch
            if len(voice.channel.members) == len(voice_channel.members):
                return
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

        #Stop spamming when someone posts a link
        #Only send message if edited 5 seconds or more after original 
        time_cutoff = before.created_at + datetime.timedelta(seconds = 5)
        if before.edited_at and before.edited_at <= time_cutoff:
            return
            
        name = get_name(before.author)
        await before.channel.send(f"Whoa {before.author.mention} why you editing messages {name}? Sketch")

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
            or (self.bot.user in message.mentions or "chowder" in comment and "pls" not in comment)
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
    name = get_respectful_name() if author.roles[-1].position >= config["respect_req"] else get_condescending_name()
    return name


def get_condescending_name():
    return random.choice(speech["condescending_names"])


def get_activity():
    return random.choice(speech["activities"])


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


def get_greeting():
    return random.choice(speech["responses"]["greeting"])


def setup(bot):
    bot.add_cog(Chowder(bot))
