"""
    Hang Chowder from a rope
"""
import json
import random
import discord
from chowder import chowder
from nltk.corpus import words

with open("games/hangman/hangman_config.json", "r") as read_file:
    config = json.load(read_file)

global word
global player_str
global title


async def start(bot, ctx, players, difficulty):
    global player_str
    global title
    player_str = ', '.join([p.display_name for p in players])
    title = random.choice(config["titles"])

    await ctx.send(f"Starting a game of **{difficulty} hangman** with {', '.join([p.mention for p in players])}")
    cgr = bot.get_cog("Cgr")

    if difficulty == "normal":
        global word
        word = random.choice(config["words"] + config["insane_words"])
        victory = await play(bot, ctx, players, config["strikes"], set())
        await cgr.update_ratings_ai(ctx, players, victory, "hangman", config["normal_rating"])
    else:
        victory = await play_insane(bot, ctx, players, config["insane_strikes"])
        await cgr.update_ratings_ai(ctx, players, victory, "hangman", config["insane_rating"])
    if victory:
        await ctx.send(get_victory_message().format(word=word))
    else:
        await ctx.send(get_defeat_message().format(word=word))
    return players if victory else []


async def play_insane(bot, ctx, players, strikes):
    global word
    word_length = random.randint(4, 10)
    wordlist = filter(lambda w: len(w) == word_length, words.words())
    wordlist = [w.upper() for w in wordlist]
    word = random.choice(wordlist)
    guesses = set()

    await display(ctx, word, guesses, strikes, player_str, title)

    while strikes:
        guess = await get_guess(bot, players)
        if guess in guesses:
            await ctx.send(f"You already guessed **{guess}**, {chowder.get_condescending_name()}")
            continue
        guesses.add(guess)

        remaining_words = await get_remaining_words(guess, wordlist)
        if len(remaining_words) <= 1:
            if guess not in word:
                await ctx.send(get_strike_message().format(guess=guess))
                strikes -= 1
            return await play(bot, ctx, players, strikes, guesses)
        wordlist = remaining_words
        word = random.choice(wordlist)

        if guess not in word:
            await ctx.send(get_strike_message().format(guess=guess))
            strikes -= 1
        await display(ctx, word, guesses, strikes, player_str, title)

    return False


async def play(bot, ctx, players, strikes, guesses):
    wordset = set(word.replace(" ", ""))

    await display(ctx, word, guesses, strikes, player_str, title)

    while strikes:
        guess = await get_guess(bot, players)
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


async def get_remaining_words(guess, words):
    families = {}

    for word in words:
        family = get_family(word, guess)
        families[family] = families[family] + [word] if family in families else [word]

    return families[max(families, key=lambda k: len(families[k]))]


async def get_guess(bot, players):
    def check(m):
        return m.author in players and \
            (len(m.content) == 1 and m.content.isalpha())

    guess = (await bot.wait_for("message", check=check)).content.upper()
    return guess


def get_family(word, guess):
    family = ""
    for letter in word:
        if(letter == guess):
            family += guess
        else:
            family += "-"
    return family


def get_display_word(word, guesses):
    letters = ""
    for letter in word:
        if letter == " ":
            letters += "\n"
        elif letter in guesses:
            letters += f"{letter} "
        else:
            letters += "__ __ "
    return letters


async def display(ctx, word, guesses, strikes, players, title):
    embed = discord.Embed(
            title=get_display_word(word, guesses),
            color=discord.Colour.dark_red()
        )
    guess_str = ', '.join(guesses) if guesses else config["emote"]
    embed.set_image(url=config["gallows"][strikes])
    embed.set_author(name=title)
    embed.add_field(name="Guesses", inline=True, value=guess_str)
    embed.add_field(name="Strikes left", inline=True, value=strikes)
    embed.set_footer(text=f"Players: {players}")
    await ctx.send(embed=embed)


def get_victory_message():
    return random.choice(config["victory_messages"])


def get_defeat_message():
    return random.choice(config["defeat_messages"])


def get_strike_message():
    return random.choice(config["strike_messages"])
