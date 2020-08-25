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
    game_config = config["games"]

games = list(game_config.keys())


class Cgr(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_ratings_coop(self, ctx, team: TelewaveTeam):
        r2 = math.pow(10, game_config["telewave"]["ai_rating"]/400)
        s = team.score / game_config["telewave"]["max_score"]
        await self.update_ratings_helper(ctx, team.get_players(), r2, s, "telewave")

    async def update_ratings_vs(self, ctx, team1: TelewaveTeam, team2: TelewaveTeam):
        r2 = math.pow(10, team2.cgr/400)
        s = 1 if team1.score > team2.score else 0 if team2.score > team1.score else 0.5
        await self.update_ratings_helper(ctx, team1.get_players(), r2, s, "telewave")
        r2 = math.pow(10, team1.cgr/400)
        s = 1 - s
        await self.update_ratings_helper(ctx, team2.get_players(), r2, s, "telewave")

    async def update_ratings_ai(self, ctx, players, won, game):
        r2 = math.pow(10, game_config[game]["ai_rating"]/400)
        s = 1 if won else 0
        await self.update_ratings_helper(ctx, players, r2, s, game)

    async def update_ratings_helper(self, ctx, team, r2, s, game):
        for player in team:
            cgr = await self.get_rating(player, game)
            r1 = math.pow(10, cgr.rating/400)
            e1 = r1 / (r1 + r2)
            k = self.get_k_factor(cgr, game)
            prev_rank = self.get_rank(cgr)
            await cgr.update(rating=cgr.rating + k * (s - e1), games_played=cgr.games_played+1).apply()
            new_rank = self.get_rank(cgr)
            if prev_rank != new_rank:
                await ctx.send(f"Dang {player.mention} just ranked up to **{new_rank}**")

    async def get_rating(self, player, game):
        cgr = await persistence.Rating.get({"id": player.id, "game": game})
        if cgr:
            return cgr
        return await self.create_new_rating(player.id, game)

    async def create_new_rating(self, id, game):
        cgr = await persistence.Rating.create(id=id, game=game, rating=game_config[game]["base_rating"], games_played=0)
        return cgr

    async def get_all_game_ratings(self, player):
        cgrs = await persistence.db.all(persistence.Rating.query.where(persistence.Rating.id == player.id))
        return cgrs

    async def get_average_rating(self, players, game):
        avg_rating = 0
        for player in players:
            avg_rating += (await self.get_rating(player, game)).rating
        return avg_rating // len(players)

    async def get_top_players(self):
        cgrs = {}
        for game in games:
            cgr = await persistence.db.all(
                persistence.Rating.query.where(persistence.Rating.game == game).order_by(persistence.Rating.rating.desc())
            )
            cgrs[game] = cgr[0]
        return cgrs

    def get_rank(self, cgr):
        if cgr.games_played < 5:
            return "Provisional"
        if cgr.rating < 1100:
            return "Bronze"
        if cgr.rating < 1400:
            return "Silver"
        if cgr.rating < 1700:
            return "Gold"
        if cgr.rating < 2000:
            return "Platinum"
        if cgr.rating < 2300:
            return "Diamond"
        return "Challenger"

    def get_k_factor(self, cgr, game):
        if cgr.games_played <= 10:
            return 100 - 3 * cgr.games_played
        return game_config[game]["k_factor"] / cgr.rating

    async def get_display_text(self, player):
        cgrs = await self.get_all_game_ratings(player)
        text = '\n'.join(
            [f"{cgr.game.capitalize()}: `{cgr.rating}` CGR | **{self.get_rank(cgr)}** | `{cgr.games_played}` games" for cgr in cgrs]) \
            if cgrs else f"Sorry {chowder.get_name(player)} you don't have any ratings yet. Play some games."
        return text

    @commands.command(name="cgr", brief="Get your Chowder game ratings")
    async def display_ratings(self, ctx):
        player = ctx.message.mentions[0] if ctx.message.mentions else ctx.author
        cgrs = await self.get_all_game_ratings(player)
        text = await self.get_display_text(player)
        embed = discord.Embed(
            description=text,
            color=player.color
        )
        best_rank = self.get_rank(max(cgrs, key=lambda c: c.rating)) if cgrs else "Provisional"
        embed.set_thumbnail(url=config["ranks"][best_rank])
        embed.set_author(name=f"{player.display_name}'s CGR:", icon_url=player.avatar_url)
        embed.set_footer(
            text="CGR (Chowder Game Rating) is an experimental rating system \n" +
                 "optimized for asymmetrical games with elements of luck."
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Cgr(bot))
