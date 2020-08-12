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
        self.promotion_nominees = {}

    def cog_unload(self):
        self.spam.cancel()

    @tasks.loop(seconds=60)
    async def spam(self):
        """Chowder bot tries to revive the dead server"""
        channel = self.bot.get_channel(config["default_channel_id"])
        last_message = channel.last_message
        if last_message and last_message.author != self.bot.user:
            time_since_last_message = datetime.utcnow() - channel.last_message.created_at
            if time_since_last_message.seconds > config["spam_cooldown"]:
                await self.bot.get_channel(config["default_channel_id"]).send(random.choice(config["spam_quotes"]))

    @spam.before_loop
    async def before_spam(self):
        print('waiting...')
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id != config["default_channel_id"] or message.author == self.bot.user:
            return
        await message.channel.send("Whoa " + message.author.mention + " why you deleting messages " + get_condescending_name() + "? Sketch.") 

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.channel.id != config["default_channel_id"] or before.author == self.bot.user:
            return
        await before.channel.send("Whoa " + before.author.mention + " why you editing messages " + get_condescending_name() + "? Sketch.") 

    @commands.command(name="promote", brief="Nominate a user for promotion.")
    async def promote(self, ctx):
        if ctx.channel.id != config["default_channel_id"] or ctx.author == self.bot.user:
            return

        nominator = ctx.author
        nominees = ctx.message.mentions
        if not nominees:
            await ctx.send("Gotta mention someone to nominate them, " + get_condescending_name())
            return
        nominee = nominees[0]
        if nominee.top_role.position >= config["promotion_cap"]:
            await ctx.send("Sorry " + get_condescending_name() + ", no democratic promotions at " + nominee.top_role.name + " rank. Please contact a board member for a manual review.")
            return
        if nominee.id == nominator.id:
            await ctx.send("Can't nominate yourself " + get_condescending_name() + ", get one of your simps to do it.")
            return
        if nominee == self.bot.user:
            await ctx.send("I appreciate the thought but I'm happy at my rank, " + get_condescending_name())
            return
        if nominee.id not in self.promotion_nominees:
            self.promotion_nominees[nominee.id] = set([nominator.id])
        elif nominator.id in self.promotion_nominees[nominee.id]:
            await ctx.send("Settle down " + get_condescending_name() + ", you already nominated " + nominee.mention + " for a promotion.")
            return
        else:
            self.promotion_nominees[nominee.id].add(nominator.id)

        noms_needed = config["min_nominations"] - len(self.promotion_nominees[nominee.id])
        if noms_needed > 0:
            await ctx.send("Hey " + get_condescending_name() + "s, " + nominator.mention + " has nominated " + nominee.mention + " for a promotion." + \
                            "They still need " + str(noms_needed) + " more nominations though.")
            return
        else:
            # TODO maybe actually promote them instead
            self.promotion_nominees[nominee.id] = set([])
            await ctx.send("Congratulations " + nominee.mention + ", you just got promoted from " + nominee.top_role.name + \
                            " to--Sike! Y'all thought this was a democracy? It's a dictatorship " + get_condescending_name() + \
                            "s. Maybe buy me a drink and I'll think about promoting you.")

    @commands.command(name="demote", brief="Nominate a user for demotion.")
    async def demote(self, ctx):
        await ctx.send("Demotion features coming soon, sit tight " + get_condescending_name())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != config["default_channel_id"] or message.author == self.bot.user:
            return
            
        comment = message.content.lower()
        words = comment.strip().split(' ')

        if "brendan" in comment:
            await message.channel.send("Who's Brendan? He sounds like a real " + get_condescending_name())
            return

        if "stfu" in comment or "shut" in comment:
            await message.channel.send("Freedom of speech, " + get_condescending_name())
            return

        trigger_words = [word for word in words if word in config["trigger_words"]]
        if trigger_words:
            await message.channel.send(trigger_words[0] + "? " + get_random_tilt_response())
            return

        if "chowder" in comment and "pls" not in comment:
            if message.author.top_role.position < config["role_req"]:
                await message.channel.send("You're only a " + message.author.top_role.name + ", don't even talk to me " + get_condescending_name())
                return
            
            greetings = [word for word in words if word in config["greetings"]]
            if greetings:
                await message.channel.send(get_random_greeting() + " " + get_condescending_name())
                return

            if any(insult_word in words for insult_word in config["insult_words"]):
                await message.channel.send(get_random_insult_response() + " " + get_condescending_name())
                return

            happy_words = [word for word in words if word in config["happy_words"]]
            if any(happy_word in words for happy_word in config["happy_words"]):
                await message.channel.send(happy_words[0] + "? " + get_random_happy_response())
                return

            suicide_words = [word for word in words if word in config["suicide_words"]]
            if any(suicide_word in words for suicide_word in config["suicide_words"]):
                await message.channel.send(get_random_suicide_response())
                return

            if "please" in words:
                await message.channel.send("That's not how you spell pls")
                return

            if "pin" in words:
                await message.channel.send("Yeah that is a pen in my mouth. What's it to you?")
                return

            if "life" in words:
                await message.channel.send("Bro you think I have a life? I just sit in this server all day")
                return

            if "kys" in words:
                await message.channel.send("I'm trying " + get_condescending_name())
                return

            if "think" in words:
                await message.channel.send("Thinking is not my strong suit")
                return

            if "rank" in words:
                await message.channel.send("I deserve to be plat goddammit")
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

def get_random_suicide_response():
    return random.choice(config["suicide_responses"])

def setup(bot):
    bot.add_cog(ChowderCog(bot))
