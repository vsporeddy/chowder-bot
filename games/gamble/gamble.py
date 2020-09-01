"""
    Roll your life away
"""

import json
import random
from chowder import chowder
from games.slots import slots
from discord.ext import commands

with open("games/gamble/gamble_config.json", "r") as read_file:
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

    @commands.command(name="slots", brief="Try your hand at the slots and get rich.")
    async def slots(self, ctx, *args):
        if (len(args) == 0):
            bet = None
        elif (len(args) != 1):
            await ctx.send("Invalid input.")
            return
        else:
            bet = args[0]
        await slots.roll(self, ctx, bet)


def setup(bot):
    bot.add_cog(Gamble(bot))
