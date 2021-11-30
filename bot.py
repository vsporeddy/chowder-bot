import os
import discord
import json
import persistence
import random

from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands import CommandNotFound

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

with open("config.json", "r") as read_file:
    config = json.load(read_file)


def get_prefix(bot, message):
    prefixes = config["prefixes"]
    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix)
channels = set(config["channels"])


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error

extensions = [
    "games.games",
    "chowder.chowder",
    "governance.governance",
    "games.gamble.gamble",
    "cgr.cgr",
    "coin.coin",
    "games.inventory"
]

if __name__ == "__main__":
    for extension in extensions:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=config["guild"])
    await persistence.initialize()
    print("Connected to ChowderDB")


@bot.check
async def check_commands(ctx):
    if ctx.channel.id not in channels or ctx.author == bot.user:
        return False
    if ctx.invoked_with != "help" and random.random() <= config["insubordination_rate"]:
        await ctx.send(random.choice(config["insubordination_messages"]))
        return False
    return True

bot.run(TOKEN, bot=True, reconnect=True)
