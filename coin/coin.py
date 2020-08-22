"""
    ChowderCoin makes the world go round
"""

import discord
import json
import persistence

from discord.ext import commands
from decimal import Decimal


with open("coin/coin_config.json", "r") as read_file:
    config = json.load(read_file)


class ChowderCoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_balance(self, user):
        cc = await persistence.Coin.get({"id": user.id})
        if cc:
            return cc
        return await self.create_new_account(user)

    async def create_new_account(self, user):
        cc = await persistence.Coin.create(id=user.id, balance=config["starting_coin"])
        return cc

    async def add_coin(self, user, amount):
        cc = await self.get_balance(user)
        await cc.update(balance=cc.balance + Decimal(amount)).apply()

    async def subtract_coin(self, user, amount):
        cc = await self.get_balance(user)
        if cc.balance == 0:
            return False
        await cc.update(balance=cc.balance - Decimal(amount)).apply()
        return True

    @commands.command(name="balance", brief="Check your ChowderCoin™️ balance")
    async def display_balance(self, ctx):
        cc = await self.get_balance(ctx.author)
        embed = discord.Embed(
            title=f"  {cc.balance:.2f}",
            color=ctx.author.color
        )
        embed.set_thumbnail(url=config["image"])
        embed.set_author(name=f"{ctx.author.display_name}'s ChowderCoin™️:", icon_url=ctx.author.avatar_url)
        embed.set_footer(
            text="Play games against Chowdertron to earn ChowderCoin™️.\nWager ChowderCoin™️ against other players in vs. games."
        )
        await ctx.send(embed=embed)

    @commands.command(name="store", brief="Browse the ChowderCoin™️ store")
    async def store(self, ctx):
        await ctx.send("Store coming soon")

    @commands.command(name="buy", brief="Make a purchase with ChowderCoin™️")
    async def buy(self, ctx):
        await ctx.send("Store coming soon")


def setup(bot):
    bot.add_cog(ChowderCoin(bot))
