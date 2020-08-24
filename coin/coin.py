"""
    ChowderCoin makes the world go round
"""

import discord
import json
import persistence

from chowder import chowder
from discord.ext import commands
from decimal import Decimal


with open("coin/coin_config.json", "r") as read_file:
    config = json.load(read_file)

with open("games/items.json", "r") as read_file:
    item_config = json.load(read_file)
    items = list(item_config.keys())


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
        player = ctx.message.mentions[0] if ctx.message.mentions else ctx.author
        cc = await self.get_balance(player)
        embed = discord.Embed(
            title=f"  {cc.balance:.2f}",
            color=player.color
        )
        embed.set_thumbnail(url=config["image"])
        embed.set_author(name=f"{player.display_name}'s ChowderCoin™️:", icon_url=player.avatar_url)
        embed.set_footer(
            text="Play games against Chowdertron to earn ChowderCoin™️.\nWager ChowderCoin™️ against other players in vs. games."
        )
        await ctx.send(embed=embed)

    @commands.command(name="store", brief="Browse the ChowderCoin™️ store")
    async def store(self, ctx):
        embed = discord.Embed(title="ChowderCoin™️ Store")
        for item in items:
            item = item_config[item]
            embed.add_field(
                name=f"{item['emote']} {item['name']}",
                value=f"`{item['price']:.2f}`" if item["for_sale"] else "`OUT OF STOCK`"
            )
        await ctx.send(embed=embed)

    @commands.command(name="check", brief="Examine an item in the store")
    async def check_item(self, ctx, *, item: str = None):
        item = item.strip().lower().replace(' ', '_') if item else None
        if not await self.validate_item(ctx, item):
            return
        item = item_config[item]
        embed = discord.Embed(title=item["name"])
        embed.set_thumbnail(url=item["image"])
        if "stats" in item:
            stats = item["stats"]
            text = []
            for stat in stats.keys():
                text.append(f"`{'+' if stats[stat] > 0 else ''}{stats[stat]}` {stat.capitalize()}")
            embed.add_field(name="Stats", value='\n'.join(text), inline=True)
        if "active" in item:
            active = item["active"]
            embed.add_field(name=f"__Active__: {active['name']}", value=active['text'], inline=True)
        if "passive" in item:
            passive = item["passive"]
            embed.add_field(name=f"__Passive__: {passive['name']}", value=passive['text'], inline=True)
        if "stats" not in item and "active" not in item and "passive" not in item:
            embed.add_field(name="???", value="???")
        await ctx.send(embed=embed)

    @commands.command(name="buy", brief="Make a purchase with ChowderCoin™️")
    async def buy(self, ctx, *, item: str = None):
        item_id = item.strip().lower().replace(' ', '_') if item else None
        if not await self.validate_item(ctx, item_id):
            return
        inv_cog = self.bot.get_cog("Inventory")
        item = item_config[item_id]
        if await inv_cog.check_if_owns(ctx.author, item_id):
            await ctx.send(f"You already have a **{item['name']}**, {chowder.get_name(ctx.author)}")
            return
        cc = await self.get_balance(ctx.author)
        if item["price"] > cc.balance:
            await ctx.send(f"You're too broke to buy **{item['name']}**, {chowder.get_name(ctx.author)}")
            return
        await self.subtract_coin(ctx.author, item["price"])
        await inv_cog.add_item(ctx.author, item_id)
        await ctx.send(f"Thanks for the coin {ctx.author.mention}, you now own **{item['name']}**")

    async def validate_item(self, ctx, item):
        if not item:
            await ctx.send(f"Uhh hello? What item {chowder.get_name(ctx.author)}?")
            return False
        if item not in items:
            await ctx.send(f"I don't know that item {chowder.get_name(ctx.author)}, check the `$store`.")
            return False
        return True


def setup(bot):
    bot.add_cog(ChowderCoin(bot))
