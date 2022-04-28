"""
    Who posted that?
"""
import datetime
import json
import random
import discord
from chowder import chowder
from collections import defaultdict, OrderedDict

with open("games/whosaidit/whopostedit_config.json", "r") as read_file:
    config = json.load(read_file)

async def start(bot, ctx, players):
    await ctx.send(f"Starting a game of **Who posted it?** with {', '.join([p.mention for p in players])}")
    winners = await play(bot, ctx, players)

    cgr_cog = bot.get_cog("Cgr")
    await cgr_cog.update_ratings_whopostedit(ctx, players, winners)
    
    if winners:
        winners = [winners[0]]
        await ctx.send(f"👑 {winners[0].mention}")
    return winners


async def play(bot, ctx, players):
    messages = list()
    authors = set()

    possible_channels = [(int(channel), weight) for channel, weight in config["channels"].items()]
    # random.choices() returns a k-sized list. We only want one, so we select the first element.
    # Since these channels are stored as tuples for (channel, weight), we select the first element.
    target_channel = bot.get_channel(random.choices(possible_channels, weights=[c[1] for c in possible_channels], k=1)[0][0])
    target_created_at = target_channel.created_at
    current_time = datetime.datetime.now(tz=None)

    # If there's ever a case that history() will return 0 messages,
    # we need to randomly choose another time and do the same calculation.
    while len(messages) == 0:
        random_time = target_created_at + \
            datetime.timedelta(seconds=random.randint(0,
            int((current_time - target_created_at).total_seconds())))
        async for message in target_channel.history(limit = config["history_limit"], after=random_time, oldest_first=True):
            try:
                if bot.get_guild(config["guild_id"]).get_role(config["required_role"]) in message.author.roles:
                    if message.attachments and len(message.attachments) > 0:
                        messages.append(message)
            except Exception as e:
                print(f"Failed polling message: {e}")
                continue

    message_to_guess = random.choice(messages)
    channel_members = set(bot.get_channel(config["author_channel"]).members)
    channel_members = set([member for member in channel_members if not member.bot])
    channel_members.remove(message_to_guess.author)
    authors.update(random.sample(channel_members, min(9, max(4, len(players) + 1))))
    authors.add(message_to_guess.author)
    authors = list(authors)
    random.shuffle(authors)

    choices = {choice + 1: author for choice, author in enumerate(authors)}
    answer = list(choices.keys())[list(choices.values()).index(message_to_guess.author)]

    await display(ctx, message_to_guess, choices)
    guesses = await get_choice(bot, ctx, choices, players)
    winners = []
    for player, guess in guesses.items():
        if guess == answer:
            winners.append(bot.get_user(player))

    await display_answer(ctx, message_to_guess)
    return winners


async def get_choice(bot, ctx, choices, players):
    def check_guess(guess):
        return guess.author in players and \
                guess.channel == bot.get_channel(config["game_channel"]) and \
                guess.content.isnumeric() and \
                int(guess.content) in range(1, len(choices) + 1)

    guesses = OrderedDict()
    while len(guesses) < len(players):
        guess = await bot.wait_for("message", check=check_guess)
        if guess.author.id not in guesses:
            guesses[guess.author.id] = int(guess.content)

    return guesses


async def display(ctx, msg, choices):
    embed = discord.Embed(
        title="Who posted this?",
        description=msg.attachments[0].proxy_url
    )
    choice_list = [f"{number}. {user.name}" for number, user in choices.items()]
    embed.add_field(name="Choices", inline=False, value='\n'.join(choice_list))
    embed.set_thumbnail(url=random.choice(config["thinking_images"]))
    await ctx.send(embed=embed)

async def display_answer(ctx, msg):
    embed = discord.Embed(
        title="The answer is...",
        description=f'{msg.attachments[0].proxy_url}\n\t - {msg.author.mention}, circa <t:{int(msg.created_at.timestamp())}:d>',
        color=msg.author.color
    )
    embed.set_thumbnail(url=str(msg.author.avatar_url))
    await ctx.send(embed=embed)
