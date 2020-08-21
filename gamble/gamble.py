"""
    Handles promotions, etc.
"""

import json
import random
from chowder import chowder
from discord.ext import commands

with open("gamble/gamble_config.json", "r") as read_file:
    config = json.load(read_file)


class Gamble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", brief="Woll dat shit", aliases=["woll", "wolldatshit"])
    async def roll(self, ctx, max_roll: int = 6):
        name = chowder.get_name(ctx.author)
        roll_value = random.randint(1, max_roll)
        if roll_value >= max_roll / 2:
            await ctx.send(f"Not bad {name}, you rolled a **{roll_value}**")
        else:
            await ctx.send(f"Get rekt {name}, you rolled a **{roll_value}**")

    @commands.command(name="flip", brief="Flip a coin", aliases=["coin", "flipdatshit"])
    async def flip(self, ctx):
        await ctx.send(random.choice([config["heads"], config["tails"]]))


def setup(bot):
    bot.add_cog(Gamble(bot))
