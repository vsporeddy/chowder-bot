"""
    Sneaky sneaky
"""
import asyncio
import discord
import json
import random
from collections import deque
from chowder import chowder

with open("games/chameleon/chameleon_config.json", "r") as read_file:
    config = json.load(read_file)


async def start(bot, ctx, players):
    await ctx.send(f"Starting a game of **chameleon** with {', '.join([p.mention for p in players])}")
    winner = await play(bot, ctx, players)
    await ctx.send(f"GG EZ, {winner.mention} wins")
    cgr_cog = bot.get_cog("Cgr")
    await cgr_cog.update_ratings_chameleon(ctx, players, winner)
    return [winner]


async def play(bot, ctx, players):
    players = deque(players)
    scores = {player: 0 for player in players}
    top_score = 0
    num_guesses = 1 if len(players) > 3 else 2
    while top_score < config["max_score"]:
        await ctx.send(f"Round boutta start in **{config['wait_time']}** seconds")
        await asyncio.sleep(config["wait_time"])
        category = random.choice(list(config["categories"].keys()))
        words = config["categories"][category]
        word = random.choice(words)
        chameleon = random.choice(players)
        responses = {}

        await display(ctx, category, words, scores)
        await send_clues(players, chameleon, word)
        await ctx.send(f"Y'all got **{config['thinking_time']}** seconds to think")
        await asyncio.sleep(config["thinking_time"])
        await get_responses(bot, ctx, players, responses)
        await display(ctx, category, words, scores, responses)
        target = await get_target(bot, ctx, players)

        if target != chameleon:
            await ctx.send(
                f"Get rekt, y'all voted for {target.mention} but the chameleon was {chameleon.mention}!\n"
                f"{chameleon.mention} gets 2 points. Also the word was **{word}** lol"
            )
            scores[chameleon] += 2
        else:
            await ctx.send(f"Sorry {chameleon.mention} ya got caught {chowder.get_name(chameleon)}.")
            if await get_guess(bot, ctx, chameleon, num_guesses, word):
                await ctx.send(f"Lucky guess, yeah the word was **{word}**")
                scores[chameleon] += 1
            else:
                await ctx.send(f"Sorry {chowder.get_name(chameleon)} the word was **{word}**")
                for player in scores.keys():
                    if player != chameleon:
                        scores[player] += 2

        leader = max(scores, key=scores.get)
        top_score = scores[leader]
        dealer = players.popleft()
        players.append(dealer)
    return leader


async def send_clues(players, chameleon, word):
    for player in players:
        if player == chameleon:
            await player.send(f"You're the **chameleon** {chowder.get_name(player)}")
        else:
            await player.send(f"Word: **{word}**")


async def get_responses(bot, ctx, players, responses):
    for player in players:
        await ctx.send(f"{player.mention}: type `$say [word]` {chowder.get_name(player)}")
        m = await bot.wait_for("message", check=lambda m: m.author == player and m.channel == ctx.channel and m.content.startswith("$say "))
        responses[player] = m.content[5:]


async def display(ctx, category, words, scores, clues=None):
    embed = discord.Embed(
        title=f"Category: {category}",
        description=f"Words: ```{', '.join(word for word in words)}```"
    )
    for player in scores.keys():
        text = f"`{scores[player]}` points"
        if clues:
            text += f" | word: `{clues[player]}`"
        embed.add_field(name=player.display_name, value=text)
    await ctx.send(embed=embed)


async def get_target(bot, ctx, players):
    await ctx.send(f"Time to vote on the chameleon {chowder.get_collective_name()}, respond to the DM with a number (can't vote for yourself)")
    numbers = {n: players[n] for n in range(len(players))}
    channels = set()
    text = ""
    for n in numbers:
        text += f"`{n}` `{numbers[n]}`\n"
    for player in players:
        m = await player.send(text)
        channels.add(m.channel)

    def check(m):
        return m.content.isnumeric() and m.author in players and m.channel in channels and numbers[int(m.content)] != m.author
    votes = {}
    while len(votes) < len(players):
        m = await bot.wait_for("message", check=check)
        votes[m.author.id] = numbers[int(m.content)]
    results = {}
    for vote in votes.values():
        results[vote] = results[vote] + 1 if vote in results else 1
    return max(results, key=results.get)


async def get_guess(bot, ctx, chameleon, num_guesses, word):
    await ctx.send(f"You get {num_guesses} chances to guess the right word")
    while num_guesses > 0:
        m = await bot.wait_for("message", check=lambda m: m.author == chameleon and m.channel == ctx.channel)
        if m.content.strip().lower() == word.strip().lower():
            return True
        num_guesses -= 1
    return False
