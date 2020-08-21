"""
    Handles Chowder Game Ratings
"""

import discord
import json
import math
import persistence
from discord.ext import commands
from chowder import chowder
from games.telewave.telewave import TelewaveTeam


with open("cgr/cgr_config.json", "r") as read_file:
    config = json.load(read_file)


class Cgr(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_ratings_coop(self, team: TelewaveTeam):
        r2 = math.pow(10, config["telewave"]["ai_rating"]/400)
        s = team.score / config["telewave"]["max_score"]
        await self.update_ratings_helper(team.get_players(), r2, s, "telewave")

    async def update_ratings_vs(self, team1: TelewaveTeam, team2: TelewaveTeam):
        r2 = math.pow(10, team2.cgr/400)
        s = 1 if team1.score > team2.score else 0 if team2.score > team1.score else 0.5
        await self.telewave_ratings_helper(team1.get_players(), r2, s, "telewave")
        r2 = math.pow(10, team1.cgr/400)
        s = 1 - s
        await self.update_ratings_helper(team2.get_players(), r2, s, "telewave")

    async def update_ratings_hangman(self, players, won):
        r2 = math.pow(10, config["hangman"]["ai_rating"]/400)
        s = 1 if won else 0
        await self.update_ratings_helper(players, r2, s, "hangman")

    async def update_ratings_helper(self, team, r2, s, game):
        for player in team:
            cgr = await self.get_rating(player, game)
            r1 = math.pow(10, cgr.rating/400)
            e1 = r1 / (r1 + r2)
            k = config[game]["k_factor"] / cgr.rating
            await cgr.update(rating=cgr.rating + k * (s - e1), games_played=cgr.games_played+1).apply()

    async def get_rating(self, player, game):
        cgr = await persistence.Rating.get({"id": player.id, "game": game})
        if cgr:
            return cgr
        return await self.create_new_rating(player.id, game)

    async def create_new_rating(self, id, game):
        cgr = await persistence.Rating.create(id=id, game=game, rating=config[game]["base_rating"], games_played=0)
        return cgr

    async def get_all_game_ratings(self, player):
        cgrs = await persistence.db.all(persistence.Rating.query.where(persistence.Rating.id == player.id))
        return cgrs

    async def get_average_rating(self, players, game):
        avg_rating = 0
        for player in players:
            avg_rating += (await self.get_rating(player, game)).rating
        return avg_rating / len(players)

    @commands.command(name="cgr", brief="Get your Chowder game ratings")
    async def display_ratings(self, ctx):
        cgrs = await self.get_all_game_ratings(ctx.author)
        text = '\n'.join([f"{cgr.game.capitalize()}: `{cgr.rating}`" for cgr in cgrs]) if cgrs \
               else f"Sorry {chowder.get_name(ctx.author)} you don't have any ratings yet. Play some games."
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s CGRs:",
            description=text,
            color=ctx.author.color
        )
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(
            text="CGR is an experimental rating system optimized for asymmetrical games with elements of luck."
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Cgr(bot))
