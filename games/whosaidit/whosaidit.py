"""
    Who said that quote?
"""
import datetime
import json
import random
import discord
from chowder import chowder
from collections import defaultdict

with open("games/whosaidit/whosaidit_config.json", "r") as read_file:
    config = json.load(read_file)

async def start(bot, ctx, players):
    await ctx.send(f"Starting a game of **Who said it?** with {', '.join([p.mention for p in players])}")
    winners = await play(bot, ctx, players)
    # cgr_cog = bot.get_cog("Cgr")
    # await cgr_cog.update_ratings_whosaidit(ctx, players, winner)
    await ctx.send(f"Winners: {', '.join([w.mention for w in winners])}")
    return winners


async def play(bot, ctx, players):
    """
    play is the main gameplay loop.

    It randomly selects from config["channels"] a config["history_limit"]
    number of messages, somewhere between the channel's creation time and
    now.
    
    All messages that have an author of config["required_role"] and a message
    length greater than config["min_num_words"] are added for contention.

    Then, for all members in config["author_channel"], randomly select 4,
    and add the message's author to choose from.
    """
    messages = list()
    authors = set()

    target_channel = bot.get_channel(random.choice(config["channels"]))
    target_created_at = target_channel.created_at
    current_time = datetime.datetime.now(tz=None)
    random_time = target_created_at + \
        datetime.timedelta(seconds=random.randint(0,
        int((current_time - target_created_at).total_seconds())))

    async for message in target_channel.history(limit = config["history_limit"], after=random_time, oldest_first=True):
        if bot.get_guild(config["guild_id"]).get_role(config["required_role"]) in message.author.roles and len(message.content.split(" ")) >= config["min_num_words"]:
            messages.append(message)

    message_to_guess = random.choice(messages)
    channel_members = set(bot.get_channel(config["author_channel"]).members)
    channel_members = set([member for member in channel_members if not member.bot])
    channel_members.remove(message_to_guess.author)
    authors.update(random.sample(channel_members, 4))
    authors.add(message_to_guess.author)
    random.shuffle(list(authors))

    choices = {choice + 1: author for choice, author in enumerate(authors)}
    answer = list(choices.keys())[list(choices.values()).index(message_to_guess.author)]

    await display(ctx, message_to_guess, choices)
    guesses = await get_choice(bot, ctx, choices, players)
    winners = []
    for player, guess in guesses.items():
        if guess == answer:
            winners.append(bot.get_user(player))

    await ctx.send(f"This quote was from {message_to_guess.author.name} on {message_to_guess.created_at}!")

    return winners


async def get_choice(bot, ctx, choices, players):
    def check_guess(guess):
        return guess.author in players and \
                guess.channel == bot.get_channel(config["game_channel"]) and \
                guess.content.isnumeric() and \
                int(guess.content) in range(1, 5)
    guesses = {}
    while len(guesses) < len(players):
        # TODO: config["thinking_time"] ?
        guess = await bot.wait_for("message", check=check_guess)
        guesses[guess.author.id] = int(guess.content)

    return guesses


async def display(ctx, msg, choices):
    embed = discord.Embed(
        title="Who said this?",
        description=f'"{msg.content}"'
    )
    choice_list = [f"{number}. {user.name}" for number, user in choices.items()]
    embed.add_field(name="Choices", inline=False, value='\n'.join(choice_list))
    await ctx.send(embed=embed)