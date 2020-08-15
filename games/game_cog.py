"""
    Starts and rallies games
"""

import discord
import asyncio
import json
from discord.ext import commands
from chowder import chowder_cog

with open("games/game_config.json", "r") as read_file:
    config = json.load(read_file)
    game_config = config["games"]

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.in_game = False
        self.current_game = None

    async def rally(self, ctx, game, initiator):
        """Rallies people for a game."""
        await self.set_game_status(game)

        message = await ctx.send(f"Yo, **{initiator.mention}** is tryna play **{game}**. React here with \
{game_config[game]['emote']} in the next {game_config[game]['wait_time']} seconds if you're in")
        await message.add_reaction(game_config[game]["emote"])

        # Wait for people to join
        await asyncio.sleep(game_config[game]["wait_time"])

        # If the game was stopped while rallying, end
        if not self.in_game:
            return

        message = await ctx.channel.fetch_message(message.id)
        reaction = discord.utils.find(lambda r: str(r.emoji) == game_config[game]["emote"], message.reactions)

        players = await reaction.users().flatten()
        players.remove(self.bot.user)
        if initiator not in players:
            players.append(initiator)

        if len(players) < game_config[game]["min_players"]:
            await ctx.send(f"Dead game, we need at least {game_config[game]['min_players']} people")
            await self.clear_game_status()
            return

        return players

    @commands.group(name="play", brief="Initiates a game.")
    async def play(self, ctx, game:str = None):
        if ctx.channel.id not in config["channels"] or ctx.author == self.bot.user:
            return
        name = chowder_cog.get_name(ctx.author)

        if not game:
            await ctx.send(f"Uhh hello? What game {name}?")
            return

        games = game_config.keys()
        if game not in games:
            await ctx.send(f"Wtf is {game}? I only know these games: {', '.join([g for g in games])}")
            return

        initiator = ctx.author
        start_req = game_config[game]["start_req"]
        if initiator.top_role.position < start_req:
            await ctx.send(f"Sorry {name}, you're not high enough rank to start a game of {game}. Try getting promoted.")
            return
        if self.in_game:
            await ctx.send(f"Sorry {name}, I'm in a game of {self.current_game} already")
            return

        players = await self.rally(ctx, game, initiator)
        # TODO actually start the game

    @commands.command(name="stop", brief="Stops game if there's a game in progress.")
    async def stop(self, ctx):
        if ctx.channel.id not in config["channels"] or ctx.author == self.bot.user:
            return
        name = chowder_cog.get_name(ctx.author)

        if not self.in_game:
            await ctx.send(f"Stop what? I'm not doing anything {name}")
            return
        
        game = self.current_game

        if ctx.author.top_role.position < game_config[game]["stop_req"]:
            await ctx.send(f"Sorry {name}, you're not high enough stop a game of {game}. Try getting promoted.")
            return

        await ctx.send(f"Rip {game}")
        await self.clear_game_status()


    async def clear_game_status(self):
        self.in_game = False
        self.current_game = None
        await self.bot.change_presence(activity=None)

    async def set_game_status(self, game):
        self.in_game = True
        self.current_game = game
        await self.bot.change_presence(activity=discord.Game(name=game))

def setup(bot):
    bot.add_cog(Game(bot))