"""
    Handles items
"""

import discord
import json
import persistence

from chowder import chowder
from discord.ext import commands


with open("games/items.json", "r") as read_file:
    item_config = json.load(read_file)


class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_items(self, player):
        items = await persistence.db.all(persistence.Items.query.where(persistence.Items.id == player.id))
        return items

    async def check_if_owns(self, player, item_id):
        item = await persistence.Items.get({"id": player.id, "item": item_id})
        return item is not None

    async def add_item(self, player, item_id):
        await persistence.Items.create(id=player.id, item=item_id)

    async def remove_item(self, player, item_id):
        await persistence.Items.delete.where(id=player.id, item=item_id)

    async def get_display_text(self, player):
        items = await self.get_items(player)
        description = f"You don't have any items yet, {chowder.get_name(player)}" if not items else ""
        for i in items:
            item = item_config[i.item]
            description += f"{item['emote']} **{item['name']}**\n"
        return description

    @commands.command(name="items", brief="Check your inventory")
    async def display_items(self, ctx):
        description = await self.get_display_text(ctx.author)
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s items",
            description=description,
            color=ctx.author.color
        )
        embed.set_thumbnail(url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Inventory(bot))
