import json
import random
import copy
import discord
from math import ceil, pow
from chowder import chowder


with open("games/slots/slots_config.json", "r") as read_file:
    config = json.load(read_file)

emotes = config["emotes"]
reels = config["reels"]
wildcard = config["wildcard"]
symbols = config["symbols"]
win_hands = config["winning_hands"]

async def roll(self, ctx, bet):
    cc_cog = self.bot.get_cog("ChowderCoin")
    weight = copy.deepcopy(config["weights"])
    if (wildcard != None and wildcard not in symbols):
        weight.append(config["wildcard_weight"])
        emotes[wildcard] = config["wildcard_emote"]
        symbols.append(wildcard)   
    if (bet == None):
        await display_payouts(ctx)
        return
    bal = (await cc_cog.get_balance(ctx.author)).balance
    bet = await check_bet(ctx, bet, bal)
    if (bet == None):
        return
    rolls = roll_slots(weight)
    result = check_slots(rolls, config["wildcard"])
    status = get_hand(result)
    mult = config["winning_hands"][status]["payout"]
    winnings = 0
    if (mult > 0):
        winnings = bet*(1+mult)
    wc_multiplier = None
    if (result[1] > 0):
        wc_multiplier =  pow(2, result[1])
        winnings *= wc_multiplier
    diff = round(winnings-bet, 2)
    await cc_cog.add_coin(ctx.author, diff)
    bal = (await cc_cog.get_balance(ctx.author)).balance
    await display(ctx, rolls, status, result[1], wc_multiplier, bal, diff)

"""
    Check if user bet is valid and displays message if not
"""
async def check_bet(ctx, bet, bal):
    if (isinstance(bet, str) and bet.lower() == "all" and bal > 0):
        bet = bal
    elif (bet.replace('.', '', 1).isdigit()):
        bet = float(bet)
        if (bet > bal):
            await ctx.send("You don't have enough coin to play, " + \
                            chowder.get_condescending_name() + ".")
            return None
        elif (bet < config['min_bet']):
            await ctx.send(f"Bro, you can't bet less than {config['min_bet']}.")
            return None
        return bet
    else:
        await ctx.send("Invalid bet input.")
        return None

"""
    Display all winning hands and their payouts in an Embed
"""
async def display_payouts(ctx):
    payout_str = """```ini\n"""
    for k, v in win_hands.items():
        if (k != "RIP"):
            label = v["label"]
            payout = v["payout"]
            payout_str += f"'{label}' = {payout}x\n"
    if (wildcard != None and wildcard not in symbols):
        payout_str += f"{emotes.get(wildcard)} wildcard counts as any symbol. \
                        Winnings are also doubled per wildcard."
    payout_str += "```"
    embed = discord.Embed(
        title = "__Slots | Help__",
        description = "```$slots [bet number]```"
    )
    embed.add_field(name="__Payouts__", inline=True, value=payout_str)
    await ctx.send(embed=embed)

"""
    Gathers all final information and displays in an Embed
"""
async def display(ctx, rolls, status, num_wcs, multiplier, bal, diff):
    coin = config["coin_emote"]
    msg = config["winning_hands"][status]["message"]
    win_color = config["winning_hands"][status]["color"]
    diff_str = format(diff, '.2f')
    if (diff > 0):
        diff = "+" + diff_str
    roll_str = "**------------------------------**\n**| **"
    for i in rolls:
        roll_str += emotes.get(str(i))
        roll_str += "** | **"
    roll_str += "\n**------------------------------**"
    roll_str += "\n" + msg
    if (num_wcs > 0):
        roll_str += f"""\n **{num_wcs} wildcards in your roll = {multiplier}x.**"""
    embed = discord.Embed(
        color = win_color,
        description = roll_str,
    )
    #embed.add_field(name="Winnings", inline=True, value=f"{diff}")
    embed.add_field(name="__Balance__", inline=True, value=f"**{bal:.2f}**({diff}) {coin}")
    #embed.set_thumbnail(url=str(ctx.author.avatar_url))
    embed.set_author(name= "Slots | Player: " + ctx.author.name + "#" + ctx.author.discriminator, icon_url=str(ctx.author.avatar_url))
    await ctx.send(embed=embed)

"""
    Roll it, Chowder!
"""
def roll_slots(weight):
    rolls = []
    for i in range(reels):
        roll = random.choices(symbols, weights=weight)[0]
        rolls.append(roll)
        if (config["scam"] != None and roll != wildcard):
            tmp = weight[roll-1] * config["scam"]
            if (tmp < config["scam_threshold"]):
                weight[roll-1] = config["scam_threshold"] 
            else:
                weight[roll-1] = tmp
    return rolls

"""
    Checks to see what streaks showed up in a slot roll. Returned as a list of tuples.
    Additional bonus field if there is a wildcard
"""
def check_slots(roll, wildcard=None):
    prev = roll[0]
    streak = 1
    stats = []
    bonus = 0
    for i in range(1, len(roll)):
        if (roll[i] == prev):
            streak += 1
        else:
            tup = [prev, streak]
            stats.append(tup)
            prev = roll[i]
            streak = 1
        if (i == (len(roll)-1)):
            stats.append([roll[i], streak])
    return [stats, bonus]

"""
    Given a roll, finds the highest winning hand and returns it
"""
def get_hand(result):
    triple = False
    pair = 0
    status = "RIP"
    for streak in result[0]:
        if (streak[1] == 5):
            status = 'E'
        elif (streak[1] == 4):
            status = 'D'
        elif (streak[1] == 3):
            triple = True
        elif (streak[1] == 2):
            pair += 1
    if (triple):
        if (pair == 1):
            status = 'F'
        else:
            status = 'C'
    elif (pair == 2):
        status = 'B'
    elif (pair == 1):
        status = 'A'
    return status
