"""
    Represents Chowder bot's personality
"""

import json
import random
import discord
from datetime import datetime
from discord.ext import tasks, commands

with open("chowder/chowder_config.json", "r") as read_file:
    config = json.load(read_file)

class ChowderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam.start()

    def cog_unload(self):
        self.spam.cancel()

    @tasks.loop(seconds=60)
    async def spam(self):
        """Chowder bot tries to revive the dead server"""
    
        channel = self.bot.get_channel(config["default_channel_id"])
        if channel.last_message:
            time_since_last_message = datetime.utcnow() - channel.last_message.created_at
            if time_since_last_message.seconds > config["spam_cooldown"]:
                await self.bot.get_channel(config["default_channel_id"]).send(random.choice(config["spam_quotes"]))

    @spam.before_loop
    async def before_spam(self):
        print('waiting...')
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        await message.channel.send("Whoa " + message.author.mention + " why you deleting messages " + get_condescending_name() + " ? Sketch.") 

    @commands.Cog.listener()
    async def on_message_edit(self, message):
        await message.channel.send("Whoa " + message.author.mention + " why you editing messages " + get_condescending_name() + " ? Sketch.") 

    @commands.command(name="promote", brief="Coming soon - Nominate a user for promotion.")
    async def promote(self, ctx, args):
        await ctx.send("Promotion features coming soon, sit tight " + get_condescending_name())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != config["default_channel_id"] or message.author == self.bot.user:
            return
            
        comment = message.content.lower()
        if "chowder" in comment:
            if message.author.top_role.position < config["role_req"]:
                await message.channel.send("You're only a " + message.author.top_role.name + ", don't even talk to me " + get_condescending_name())
                return

            words = comment.strip().split(' ')
            
            greetings = [word for word in words if word in config["greetings"]]
            if greetings:
                await message.channel.send(get_random_greeting() + " " + get_condescending_name())
                return

            trigger_words = [word for word in words if word in config["trigger_words"]]
            if trigger_words:
                await message.channel.send(trigger_words[0] + "? " + get_random_tilt_response())
                return

            if any(insult_word in words for insult_word in config["insult_words"]):
                await message.channel.send(get_random_insult_response() + " " + get_condescending_name())
                return

            happy_words = [word for word in words if word in config["happy_words"]]
            if any(happy_word in words for happy_word in config["happy_words"]):
                await message.channel.send(happy_words[0] + "? " + get_random_happy_response())
                return

            if "pls" in words:
                await message.channel.send("That's not how you spell please")
                return

            if "please" in words:
                await message.channel.send("No")
                return

            if "rope" in words:
                await message.channel.send("kms")
                return
            
            if "pin" in words:
                await message.channel.send("Yeah that is a pen in my mouth. What's it to you?")
                return

def get_condescending_name():
    return random.choice(config["condescending_names"])

def get_random_greeting():
    return random.choice(config["chowder_greetings"])

def get_random_tilt_response():
    return random.choice(config["tilt_responses"])

def get_random_insult_response():
    return random.choice(config["insult_responses"])

def get_random_happy_response():
    return random.choice(config["happy_responses"])

def setup(bot):
    bot.add_cog(ChowderCog(bot))
