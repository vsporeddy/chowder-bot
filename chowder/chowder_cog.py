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
        poll = await channel.send(f"Who's better at {activity}, {chosen_boys[0].mention} ({config['option_1']}) or "
                                    f"{chosen_boys[1].mention} ({config['option_2']})? Vote in the next "
                                    f"{config['voting_time']} seconds.")

        await poll.add_reaction(config["option_1"])
        await poll.add_reaction(config["option_2"])

        await asyncio.sleep(config["voting_time"])
        poll = await channel.fetch_message(poll.id)
        votes1 = await discord.utils.find(lambda r: str(r.emoji) == config["option_1"], poll.reactions).users().flatten()
        votes2 = await discord.utils.find(lambda r: str(r.emoji) == config["option_2"], poll.reactions).users().flatten()

        winner, loser = chosen_boys[0], chosen_boys[1] if len(votes1) > len(votes2) else chosen_boys[1], chosen_boys[0]
        tie = f"I voted for {winner.mention} btw" if len(votes1) == len(votes2) else None

        await channel.send(f"It's decided, {winner.mention} is the best on paper at {activity}!")
        await channel.send(f"{winner.mention} wins 5 ChowderCoin™️ and all voters get 1 each. {loser.mention} is "
                            f"deducted 10 ChowderCoin™️")
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
        await self.bot.get_channel(config["default_channel"]).send(f"{config['happy_emote']} {get_join_phrase()} "
                                                                    f"{get_condescending_name()}s?")

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

def get_respectful_name():
    return random.choice(speech["respectful_names"])

def get_join_phrase():
    return random.choice(speech["join_phrases"])

def get_spam_quote():
    return random.choice(speech["spam_quotes"])

def setup(bot):
    bot.add_cog(Chowder(bot))
