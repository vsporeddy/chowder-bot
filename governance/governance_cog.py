"""
    Handles promotions, etc.
"""

import discord
import json
import asyncio
from discord.ext import commands
from chowder import chowder_cog

with open("governance/governance_config.json", "r") as read_file:
    config = json.load(read_file)

class Governance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.promotions = {}
        self.demotions = {}

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
        name = chowder_cog.get_name(nominator)
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
            await ctx.send(f"Sorry {name}, no democratic promotions/demotions at **{nominee.top_role.name}** "
                            f"rank. Please contact a board member for a manual review.")
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
            await ctx.send(f"Hey {chowder_cog.get_condescending_name()}s, {nominator.mention} has nominated "
                            f"{nominee.mention} for a {promotion_str}. They need {noms_needed} more nominations.")
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
                await ctx.send(f"{config['promotion_emote']} Congratulations {nominee.mention}, you just got promoted "
                                f"from **{current_rank.name}** to **{new_rank.name}**!")
            else:
                await ctx.send(f"{config['demotion_emote']} Yikes {nominee.mention}, by popular demand you've been "
                                f"demoted down to **{new_rank.name}** rank.")

def setup(bot):
    bot.add_cog(Governance(bot))
