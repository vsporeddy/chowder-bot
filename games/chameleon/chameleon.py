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
    numbers = {n: players[n] for n in range(len(players))}
    top_score = 0
    num_guesses = 1 if len(players) > 3 else 2
    while top_score < config["max_score"]:
        await ctx.send(f"Round boutta start in **{config['wait_time']}** seconds")
        await asyncio.sleep(config["wait_time"])
        category = get_category()
        words = config["categories"][category]
        word = random.choice(words)
        chameleon = random.choice(players)
        responses = {}

        await display(ctx, category, words, scores)
        await send_clues(players, chameleon, word)
        await ctx.send(f"Y'all got **{config['thinking_time']}** seconds to think")
        await asyncio.sleep(config["thinking_time"])
        for player in players:
            await get_response(bot, ctx, player, responses)
            await display(ctx, category, words, scores, responses)
        target = await get_target(bot, ctx, numbers)

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

        leader = await get_leader(ctx, scores)
        top_score = scores[leader] if leader else 0
        dealer = players.popleft()
        players.append(dealer)
        del config["categories"][category]
    return leader


async def get_leader(ctx, scores):
    top = 0
    leader = None
    for player, score in scores.items():
        if score > top:
            top = score
            leader = player
        elif score == top:
            top = 0
            leader = None
    if scores[max(scores, key=scores.get)] >= config["max_score"] and top == 0:
        await ctx.send(f"Can't end on a tie {chowder.get_collective_name()}, the game goes on...")
    return leader


async def send_clues(players, chameleon, word):
    for player in players:
        if player == chameleon:
            await player.send(f"You're the **chameleon** {chowder.get_name(player)}")
        else:
            await player.send(f"Word: **{word}**")


async def get_response(bot, ctx, player, responses):
    await ctx.send(f"{player.mention} is thinking of a clue...")
    await player.send(f"What's your clue {chowder.get_name(player)}?")
    m = await bot.wait_for("message", check=lambda m: m.author == player)
    responses[player] = m.content


async def display(ctx, category, words, scores, clues=None):
    embed = discord.Embed(
        title=f"Category: {category}",
        description=f"Words: ```{', '.join(word for word in words)}```"
    )
    for player in scores.keys():
        text = f"score: `{scores[player]}`"
        if clues and player in clues:
            text += f" | clue: `{clues[player]}`"
        embed.add_field(name=player.display_name, value=text)
    await ctx.send(embed=embed)


async def get_target(bot, ctx, numbers):
    await ctx.send(f"Time to vote on the chameleon {chowder.get_collective_name()}, respond to the DM with a number (can't vote for yourself)")
    channels = set()
    text = ""
    for n in numbers:
        text += f"`{n}` `{numbers[n]}`\n"
    for player in numbers.values():
        m = await player.send(text)
        channels.add(m.channel)

    def check(m):
        return m.content.isnumeric() and m.author in numbers.values() and m.channel in channels and numbers[int(m.content)] != m.author
    votes = {}
    while len(votes) < len(numbers):
        m = await bot.wait_for("message", check=check)
        votes[m.author.id] = numbers[int(m.content)]
    results = {}
    for vote in votes.values():
        results[vote] = results[vote] + 1 if vote in results else 1
    return max(results, key=results.get)


async def get_guess(bot, ctx, chameleon, num_guesses, word):
    await ctx.send(f"You got {num_guesses} chance(s) to guess the right word")
    while num_guesses > 0:
        m = await bot.wait_for("message", check=lambda m: m.author == chameleon)
        if m.content.strip().lower() == word.strip().lower():
            return True
        num_guesses -= 1
    return False


def get_category():
    global config
    if not config["categories"]:
        with open("games/chameleon/chameleon_config.json", "r") as read_file:
            config = json.load(read_file)
    return random.choice(list(config["categories"].keys()))
