import json
import random
import discord
from math import ceil, pow
from chowder import chowder
from bank import bank

with open("games/slots/slots_config.json", "r") as read_file:
    config = json.load(read_file)

async def roll(ctx, bet):
    emotes = config["emotes"]
    reels = config["reels"]
    wildcard = config["wildcard"]
    symbols = config["symbols"]
    weight = config["weights"]
    payout_str = f"""
        1 pair = **1.5x**
        2 pair = **3x**
        3 in a row = **5x**
        4 in a row = **20x**
        5 in a row = **50x**
        Full House = **10x**
    """
    if (wildcard != None and wildcard not in symbols):
        weight.append(config["wildcard_weight"])
        emotes[wildcard] = config["wildcard_emote"]
        symbols.append(wildcard)
        payout_str += f"{emotes.get(wildcard)} wildcard counts as any symbol. Winnings are also doubled per wildcard."
    if (bet == None):
        embed = discord.Embed(
            title = "help",
            description = "$slots [bet number]"
        )
        embed.add_field(name="Payouts", inline=True, value=payout_str)
        await ctx.send(embed=embed)
        return
    bal = bank.get_balance(ctx.author.id)
    if (bal == None):
        await ctx.send("You need an account to play slots, " + ctx.author.mention + ".")
        return

    if (isinstance(bet, str) and bet.lower() == "all" and bal > 0):
        bet = bal
    elif (bet.isdigit()):
        bet = int(bet)
        if (bet > bal):
            await ctx.send("You don't have enough coin to play, " + \
                            chowder.get_condescending_name() + ".")
            return
    else:
        await ctx.send("Invalid bet input.")
        return
    rolls = []
    for i in range(reels):
        roll = random.choices(symbols, weights=weight)[0]
        rolls.append(roll)
        if (config["scam"] and roll != wildcard):
            weight[roll] *= config["scam_value"]
    result = check_slots(rolls, config["wildcard"])
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
    bank.transfer(ctx.author.id, 1, diff)
    embed.add_field(name="Winnings", inline=True, value=diff)
    if (diff > 0):
        diff = "+" + str(diff)
    embed.add_field(name="Balance", inline=True, value=f"{bal}({diff})")
    await ctx.send(embed=embed)

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
    sad = config["rip_emote"]
    nbad = cofig["nbad_emote"]
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
            msg = f"**Two pair. {nbad}**"
        elif (pair == 1):
            mult = 1.5
            msg = f"**Not bad, {chowder.get_condescending_name()}.**"
        else:
            msg = f"{sad}  **You hate to see that.**"
    return [msg, mult]
