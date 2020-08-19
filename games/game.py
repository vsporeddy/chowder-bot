"""
    Starts and rallies games
"""

import discord
import asyncio
import random
import json
import random
from math import ceil, pow
from discord.ext import commands, tasks
from chowder import chowder
from games.hangman import hangman
from games.telewave import telewave

with open("games/game_config.json", "r") as read_file:
    config = json.load(read_file)
    game_config = config["games"]

games = list(game_config.keys())


class Game(commands.Cog):
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

    async def start_game(self, ctx, game_name, players):
        if game_name == "hangman":
            self.current_game_task = asyncio.create_task(hangman.start(self.bot, ctx, players))
        elif game_name == "telewave":
            self.current_game_task = asyncio.create_task(telewave.start(self.bot, ctx, players))
        await self.current_game_task
        winners = self.current_game_task.result()
        # TODO call ChowderCoin stuff here with result
        await ctx.send(f"Winners: {', '.join([w.mention for w in winners])} earn ChowderCoin™️ (coming soon)")
        await self.clear_game_status()

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
            await self.start_game(ctx, game, players)

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

    @commands.group(name="slots", brief="Try your luck at the slots.")
    async def slots(self, ctx, *args):
        bal = chowder_cog.get_balance(ctx.author.id)
        if (bal == None):
            await ctx.send("You need an account to play slots, " + ctx.author.mention + ".")
            return
        game = config["games"]["slots"]
        emotes = game["emotes"]
        reels = game["reels"]
        wildcard = game["wildcard"]
        if (len(args) == 0):
            embed = discord.Embed(
                title = "help",
                description = "$slots [bet number]"
            )
            embed.add_field(name="Payouts", inline=True, value=f"""
                1 pair = **1.5x**
                2 pair = **3x**
                3 in a row = **5x**
                4 in a row = **20x**
                5 in a row = **50x**
                Full House = **10x**
                {emotes.get(str(wildcard))} wildcard counts as any symbol. Winnings are also doubled per wildcard.
            """)
            await ctx.send(embed=embed)
            return
        elif (len(args) != 1):
            await ctx.send("Invalid input.")
            return
        bet = args[0]
        if (isinstance(bet, str) and bet.lower() == "all" and bal > 0):
            bet = bal
        elif (bet.isdigit()):
            bet = int(bet)
            if (bet > bal):
                await ctx.send("You don't have enough coin to play, " + \
                                chowder_cog.get_condescending_name() + ".")
                return
        else:
            await ctx.send("Invalid bet input.")
            return
        rolls = []
        symbols = game["symbols"]
        weight = game["weights"]
        for i in range(reels):
            roll = random.choices(symbols, weights=weight)[0]
            rolls.append(roll)
            if (game["scam"] and roll != wildcard):
                weight[roll] *= game["scam_value"]
        result = check_slots(rolls, game["wildcard"])
        msg, mult = get_hand(result)
        if (mult > 0):
            winnings = ceil(bet*(1+mult))
        else:
            winnings = 0
        roll_str = "**------------------------------**\n**| **"
        for i in rolls:
            roll_str += emotes.get(str(i))
            roll_str += "** | **"
        roll_str += "\n**------------------------------**"
        roll_str += "\n" + msg
        if (result[1] > 0):
            multiplier =  pow(2, result[1])
            roll_str += f"""\n **{result[1]} wildcards in your roll = {multiplier}x.**"""
            winnings *= multiplier
        embed = discord.Embed(
            title = "Slots | Player: " + ctx.author.name + "#" + ctx.author.discriminator,
            color = 4188997,
            description = roll_str
        )
        diff = int(winnings-bet)
        new_bal = bal+diff
        chowder_cog.transfer(ctx.author.id, 1, diff)
        embed.add_field(name="Winnings", inline=True, value=diff)
        if (diff > 0):
            diff = "+" + str(diff)
        embed.add_field(name="Balance", inline=True, value=f"{bal}({diff})")
        await ctx.send(embed=embed)

    async def set_new_status(self):
        activity = random.choice([
                discord.Activity(name="hentai", type=discord.ActivityType.watching),
                discord.Game(name="with myself"),
                discord.Activity(type=discord.ActivityType.listening, name="a banger")
            ])
        await self.bot.change_presence(activity=activity)

"""Checks to see what streaks showed up in a slot roll. Returned as a list of tuples.
    Additional bonus field if there is a wildcard
"""
def check_slots(roll, wildcard=None):
    prev = roll[0]
    streak = 1
    stats = []
    prev_wildcard = False
    bonus = 0
    if (roll[0] == wildcard):
        bonus += 1
        roll[0] = roll[1]
    if (roll[-1] == wildcard):
        bonus += 1
        roll[-1] = roll[-2]
    for i in range(1, len(roll)):
        if (roll[i] == wildcard):
            bonus += 1
        if (roll[i] == prev or roll[i] == wildcard or prev == wildcard):
            streak += 1
            if (prev == wildcard):
                prev = roll[i]
        else:
            tup = [prev, streak]
            stats.append(tup)
            prev = roll[i]
            streak = 1
        if (i == (len(roll)-1)):
            stats.append([roll[i], streak])
    return [stats, bonus]

def get_hand(result):
    triple = False
    pair = 0
    mult = 0
    msg = ""
    for streak in result[0]:
        if (streak[1] == 5):
            mult = 50
            msg = "**FIVE IN A ROW!!!**"
        elif (streak[1] == 4):
            mult = 20
            msg = "**FOUR IN A ROW!!**"
        elif (streak[1] == 3):
            triple = True
        elif (streak[1] == 2):
            pair += 1
    if (mult == 0):
        if (triple):
            if (pair == 1):
                mult= 10
                msg = "**FULL HOUSE!!**"
            else:
                mult = 5
                msg = "**THREE IN A ROW!**"
        elif (pair == 2):
            mult = 3
            msg = "**TWO PAIR**"
        elif (pair == 1):
            mult = 1.5
            msg = "**YOU WON!**"
        else:
            msg = "**YOU LOST. TOO BAD**"
    return [msg, mult]

def setup(bot):
    bot.add_cog(Game(bot))
