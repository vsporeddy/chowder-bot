"""
    Starts and rallies games
"""

import discord
import asyncio
import json
import random

from discord.ext import commands, tasks
from chowder import chowder
from games.hangman import hangman
from games.telewave import telewave

with open("games/games_config.json", "r") as read_file:
    config = json.load(read_file)
    game_config = config["games"]

games = list(game_config.keys())


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.in_game = False
        self.current_game_name = None
        self.update_status.start()
        self.current_game_task = None

    def cog_unload(self):
        self.update_status.cancel()

    async def rally_helper(self, ctx, game, initiator, wait_time=0, min_players=0):
        """Rallies people for a game."""
        await self.set_game_status(game)
        if game in games:
            emote = game_config[game]['emote']
            wait_time = game_config[game]['wait_time']
            min_players = game_config[game]['min_players']
        else:
            emote = config['default_emote']

        message = await ctx.send(
            f"Yo, {chowder.get_collective_name()}, **{initiator.mention}** is tryna play "
            f"**{game}**. React here with {emote} in the next {wait_time} seconds if you're in"
        )
        await message.add_reaction(emote)
        # Wait for people to join
        await asyncio.sleep(wait_time)
        # If the game was stopped while rallying, end
        if not self.in_game:
            return []

        message = await ctx.channel.fetch_message(message.id)
        reaction = discord.utils.find(lambda r: str(r.emoji) == emote, message.reactions)
        players = await reaction.users().flatten()
        players.remove(self.bot.user)
        if initiator not in players:
            players.append(initiator)

        if min_players and len(players) < min_players:
            await ctx.send(f"Dead game, we need at least {min_players} people")
            await self.clear_game_status()
            return []
        return players

    async def start_game(self, ctx, game_name, players, initiator):
        winners = []
        cc_cog = self.bot.get_cog("ChowderCoin")
        pot = 0.0

        if game_name == "hangman":
            pot = game_config[game_name]["ai_win_reward"] * len(players)
            winners = await hangman.start(self.bot, ctx, players)
        elif game_name == "telewave":
            if len(players) < game_config["telewave"]["min_players_vs"]:
                game_mode = "coop"
            else:
                msg = await ctx.send(f"{initiator.mention} y'all tryna play `coop` or `vs`?")
                game_mode = (await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == initiator and m.content.lower() in ["coop", "vs"] and m.channel == msg.channel
                )).content.lower()
            if game_mode == "vs":
                buyin = await self.get_buyin(ctx, cc_cog, initiator, players)
                for player in players:
                    await cc_cog.subtract_coin(player, buyin)
                    pot += buyin
            else:
                pot = game_config[game_name]["ai_win_reward"] * len(players)
            winners = await telewave.start(self.bot, ctx, players, game_mode)

        winnings = pot / len(winners) if winners else 0
        for winner in winners:
            await ctx.send(f"{winner.mention} wins {winnings} {config['coin_emote']}")
            await cc_cog.add_coin(winner, winnings)
        if not winners:
            await ctx.send(f"No {config['coin_emote']} for losers.")
        return winners

    async def get_buyin(self, ctx, cc_cog, initiator, players):
        done = False
        max_buyin = min([(await cc_cog.get_balance(p)).balance for p in players])
        buyin = 0
        await ctx.send(f"{initiator.mention}, what is the buy-in {config['coin_emote']} for this game?")

        def check(m):
            return m.author == initiator and \
                m.channel == ctx.channel and \
                m.content.replace('.', '', 1).isdigit()
        while not done:
            buyin = float((await self.bot.wait_for("message",  check=check)).content)
            if buyin > max_buyin or buyin < 0:
                await ctx.send(f"Sorry, the buy-in must be between 0 and {max_buyin:.2f} {config['coin_emote']}")
            else:
                done = True
        return buyin

    @commands.group(name="play", brief="Initiate a discord game", aliases=games)
    async def play(self, ctx, game: str = None):
        name = chowder.get_name(ctx.author)
        if ctx.invoked_with in games:
            game = ctx.invoked_with
        elif not game:
            await ctx.send(f"Uhh hello? What game {name}?")
            return
        elif game not in games:
            await ctx.send(
                f"Wtf is **{game}**? I only know these games: **[{', '.join([g for g in games])}]**. "
                f"If you're trying to rally people for an different game use *rally*, {name}."
            )
            return
        initiator = ctx.author
        start_req = game_config[game]["start_req"]
        if initiator.top_role.position < start_req:
            await ctx.send(
                f"Sorry {name}, you're not high enough rank to start a game of **{game}**. Try getting promoted."
            )
            return
        if self.in_game:
            await ctx.send(f"Sorry {name}, I'm in a game of {self.current_game_name} already")
            return
        players = await self.rally_helper(ctx, game, initiator)
        if players:
            self.current_game_task = asyncio.create_task(self.start_game(ctx, game, players, initiator))
            await self.current_game_task
            winners = self.current_game_task.result()
            await self.clear_game_status()

    @commands.command(name="stop", brief="Stop in-progress game or rally")
    async def stop(self, ctx):
        name = chowder.get_name(ctx.author)
        if not self.in_game:
            await ctx.send(f"Stop what? I'm not doing anything {name}")
            return
        game = self.current_game_name
        if game in games and ctx.author.top_role.position < game_config[game]["stop_req"]:
            await ctx.send(
                f"Sorry {name}, you're not high enough rank to stop a game of {game}. Try getting promoted."
            )
            return
        if self.current_game_task:
            self.current_game_task.cancel()
        await ctx.send(f"Rip {game}")
        await self.clear_game_status()

    @commands.command(name="rally", brief="Rally players for an actual game")
    async def rally(self, ctx, game: str = None, wait_time: int = 60):
        name = chowder.get_name(ctx.author)
        if not game:
            await ctx.send(f"Uhh hello? What game {name}?")
            return
        players = await self.rally_helper(ctx, game, ctx.author, wait_time)
        if len(players) <= 0:
            await ctx.send(
                f"Sorry {ctx.author.mention}, no one wants to play **{game}** with you, {name}. Dead server."
            )
        else:
            await ctx.send(f"Aite {', '.join([p.mention for p in players])}, time to play some **{game}**")
        await self.clear_game_status()

    @tasks.loop(seconds=3600)
    async def update_status(self):
        if not self.in_game:
            await self.set_new_status()

    @update_status.before_loop
    async def before_status(self):
        await self.bot.wait_until_ready()

    async def clear_game_status(self):
        self.in_game = False
        self.current_game_name = None
        self.current_game_task = None
        await self.set_new_status()

    async def set_game_status(self, game):
        self.in_game = True
        self.current_game_name = game
        await self.bot.change_presence(activity=discord.Game(name=game))

    async def set_new_status(self):
        activity = random.choice([
                discord.Activity(name="hentai", type=discord.ActivityType.watching),
                discord.Game(name="with myself"),
                discord.Activity(type=discord.ActivityType.listening, name="a banger")
            ])
        await self.bot.change_presence(activity=activity)


def setup(bot):
    bot.add_cog(Games(bot))
