"""
    Hang Chowder from a rope
"""
import json
import random
import discord
from chowder import chowder

with open("games/hangman/hangman_config.json", "r") as read_file:
    config = json.load(read_file)

async def start(bot, ctx, players):
    await ctx.send(f"Starting a game of **hangman** with {', '.join([p.mention for p in players])}")
    word = get_word()
    victory = await play(bot, ctx, players, word)
    if victory:
        await ctx.send(get_victory_message().format(word=word))
    else:
        await ctx.send(get_defeat_message().format(word=word))
    return victory

async def play(bot, ctx, players, word):
    wordset = set(word.replace(" ", ""))
    guesses = set()
    strikes = config["strikes"]
    check = lambda m: "$stop" in m.content or "chowder pls stop" in m.content or \
                      m.author in players and \
                      (len(m.content) == 1 and m.content.isalpha()) or \
                      m.content.upper() == word
    player_str = ', '.join([p.nick if p.nick else p.name for p in players])
    title = get_title()
    await display(ctx, word, guesses, strikes, player_str, title)

    while strikes:
        guess = (await bot.wait_for("message", check=check)).content.upper()
        if guess == word:
            return True
        # hack for now, TODO rework this trash
        if "$STOP" in guess or "CHOWDER PLS STOP" in guess:
            return False
        if guess in guesses:
            await ctx.send(f"You already guessed **{guess}**, {chowder.get_condescending_name()}")
            continue
        guesses.add(guess)
        if guess not in word:
            await ctx.send(get_strike_message().format(guess=guess))
            strikes -= 1
        elif wordset.issubset(guesses):
            return True
        await display(ctx, word, guesses, strikes, player_str, title)

    return False

def get_display_word(word, guesses):
    letters = ""
    for letter in word:
        if letter == " ":
            letters += "\n"
        elif letter in guesses:
            letters += f"{letter} "
        else:
            letters += f"__ __ "
    return letters

async def display(ctx, word, guesses, strikes, players, title):
    embed = discord.Embed(
            title = get_display_word(word, guesses),
            color = discord.Colour.dark_red()
        )
    guess_str = ', '.join(guesses) if guesses else config["emote"]
    embed.set_image(url = config["gallows"][strikes])
    embed.set_author(name = title)
    embed.add_field(name="Guesses", inline=True, value=guess_str)
    embed.add_field(name="Strikes left", inline=True, value=strikes)
    embed.set_footer(text=f"Players: {players}")
    await ctx.send(embed=embed)

def get_word():
    return random.choice(config["words"])

def get_title():
    return random.choice(config["titles"])

def get_victory_message():
    return random.choice(config["victory_messages"])

def get_defeat_message():
    return random.choice(config["defeat_messages"])

def get_strike_message():
    return random.choice(config["strike_messages"])