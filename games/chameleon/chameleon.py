"""
    Sneaky sneaky
"""
import discord
import json
import random

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
    scores = {player: 0 for player in players}
    top_score = 0
    num_guesses = 1 if len(players) > 3 else 2
    while top_score < config["max_score"]:
        random.shuffle(players)
        category = random.choice(list(config["categories"].keys()))
        words = config["categories"][category]
        word = random.choice(words)
        chameleon = random.choice(players)

        await display(ctx, category, words, scores)
        await send_clues(players, chameleon, word)
        await get_responses(bot, ctx, players)
        target = await get_target(bot, ctx, players)

        if target != chameleon:
            await ctx.send(
                f"Get rekt, y'all voted for {target.mention} but the chameleon was {chameleon.mention}!\n"
                f"{chameleon.mention} gets 2 points"
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
                        scores[player] += 1

        leader = max(scores, key=scores.get)
        top_score = scores[leader]
    return leader


async def send_clues(players, chameleon, word):
    for player in players:
        if player == chameleon:
            await player.send(f"You're the chameleon {chowder.get_name(player)}")
        else:
            await player.send(f"Word: **{word}**")


async def get_responses(bot, ctx, players):
    for player in players:
        await ctx.send(f"{player.mention}: say a related word {chowder.get_name(player)}")
        await bot.wait_for("message", check=lambda m: m.author == player and m.channel == ctx.channel)


async def display(ctx, category, words, scores):
    embed = discord.Embed(
        title=f"Category: {category}",
        description=f"Words: ```{', '.join(word for word in words)}```"
    )
    for score in scores.keys():
        embed.add_field(name=score.display_name, value=f"{scores[score]} points")
    await ctx.send(embed=embed)


async def get_target(bot, ctx, players):
    await ctx.send(f"Time to vote on the chameleon {chowder.get_collective_name()}. Take your time, ties are resolved RANDOMLY")

    def check(m):
        return len(m.mentions) >= 1 and m.mentions[0] in players and m.author in players and m.channel == ctx.channel
    votes = {}
    while len(votes) < len(players):
        m = await bot.wait_for("message", check=check)
        votes[m.author.id] = m.mentions[0]
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
