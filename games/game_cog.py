"""
    Starts and rallies games
"""

import discord
import asyncio
import random
import json
from discord.ext import commands
from math import ceil
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

        message = await ctx.send("Yo, **" + initiator.mention + "** is tryna play **" + game + "**. React here with " \
                                    + game_config[game]["emote"] + " in the next " + str(game_config[game]["wait_time"]) \
                                    + " seconds if you're in")
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
            await ctx.send("Dead game, we need at least " + str(game_config[game]["min_players"]) + " people")
            await self.clear_game_status()
            return

        return players

    @commands.group(name="play", brief="Initiates a game.")
    async def play(self, ctx, game:str = None):
        if ctx.channel.id not in config["channels"] or ctx.author == self.bot.user:
            return
        name = chowder_cog.get_name(ctx.author)

        if not game:
            await ctx.send("Uhh hello? What game " + name + "?")
            return

        games = game_config.keys()
        if game not in games:
            await ctx.send("Wtf is " + game + "? I only know these games: " + ', '.join([g for g in games]))
            return

        initiator = ctx.author
        start_req = game_config[game]["start_req"]
        if initiator.top_role.position < start_req:
            await ctx.send("Sorry " + name + \
                            + ", you're not high enough rank to start a game of " + game + ". Try getting promoted.")
            return
        if self.in_game:
            await ctx.send("Sorry " + name + ", I'm in a game of " + self.current_game + " already")
            return

        players = await self.rally(ctx, game, initiator)

        # TODO actually start the game

    @commands.command(name="stop", brief="Stops game if there's a game in progress.")
    async def stop(self, ctx):
        if ctx.channel.id not in config["channels"] or ctx.author == self.bot.user:
            return
        name = chowder_cog.get_name(ctx.author)

        if not self.in_game:
            await ctx.send("Stop what? I'm not doing anything " + name)
            return

        game = self.current_game

        if ctx.author.top_role.position < game_config[game]["stop_req"]:
            await ctx.send("Sorry " + name + ", you're not high enough stop a game of " \
                            + game + ". Try getting promoted.")
            return

        await ctx.send("Rip " + game)
        await self.clear_game_status()


    async def clear_game_status(self):
        self.in_game = False
        self.current_game = None
        await self.bot.change_presence(activity=None)

    async def set_game_status(self, game):
        self.in_game = True
        self.current_game = game
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
        if (len(args) == 0):
            embed = discord.Embed(
                title = "help",
                description = "$slots [bet number]"
            )
            embed.add_field(name="Payouts", inline=True, value="""
                1 pair = 1.5x
                2 pair = 3x
                3 in a row = 5x
                4 in a row = 20x
                5 in a row = 50x
                Full House = 10x
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
        wildcard = game["wildcard"]
        for i in range(reels):
            roll = random.choices(symbols, weights=weight)[0]
            rolls.append(roll)
            if (game["scam"] and roll != wildcard):
                weight[roll] *= game["scam_value"]
        triple = False
        pair = 0
        win = False
        winnings = 0
        msg = ""
        for streak in check_slots(rolls, game["wildcard"]):
            if (streak[1] == 5):
                winnings = bet*51
                msg = "**FIVE IN A ROW!!!**"
            elif (streak[1] == 4):
                winnings = bet*21
                msg = "**FOUR IN A ROW!!**"
            elif (streak[1] == 3):
                triple = True
            elif (streak[1] == 2):
                pair += 1
        if (triple):
            if (pair == 1):
                winnings = bet*11
                msg = "**FULL HOUSE!!**"
            else:
                winnings = bet*6
                mgs = "**YOU WON**"
        elif (pair == 2):
            winnings = bet*4
            msg = "**TWO PAIR**"
        elif (pair == 1):
            winnings = ceil(bet*2.5)
            msg = "**YOU WON**"
        else:
            msg = "**YOU LOST. TOO BAD**"
        roll_str = "**------------------------------**\n**| **"
        for i in rolls:
            roll_str += emotes.get(str(i))
            roll_str += "** | **"
        roll_str += "\n**------------------------------**"
        roll_str += "\n" + msg
        embed = discord.Embed(
            title = "Slots | Player: " + ctx.author.name + "#" + ctx.author.discriminator,
            color = 4188997,
            description = roll_str
        )
        diff = winnings-bet
        if (diff > 0):
            diff = "+" + str(diff)
        embed.add_field(name="Winnings", inline=True, value=winnings)
        embed.add_field(name="Balance", inline=True, value="{}({})".format(bal, diff))
        await ctx.send(embed=embed)

"""Checks to see what streaks showed up in a slot roll. Returned as a list of tuples"""
def check_slots(roll, wildcard=None):
    temp = roll[0]
    streak = 1
    stats = []
    for i in range(1, len(roll)):
        if (roll[i] == temp):
            streak += 1
        else:
            tup = [temp, streak]
            stats.append(tup)
            temp = roll[i]
            streak = 1
        if (i == (len(roll)-1)):
            stats.append([roll[i], streak])
    return stats


def setup(bot):
    bot.add_cog(Game(bot))
