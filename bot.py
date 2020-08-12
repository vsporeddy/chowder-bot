import os
import discord
import asyncio
import json
import random

from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands import CommandNotFound

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

with open("config.json", "r") as read_file:
    config = json.load(read_file)

def get_prefix(bot, message):
    prefixes = config["prefixes"]
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(command_prefix=get_prefix)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error

extensions = ['games.game_cog', 'chowder.chowder_cog']

if __name__ == '__main__':
    for extension in extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=config["guild"])
    await bot.change_presence(activity=None)

    print(
        f'{bot.user.name} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

bot.run(TOKEN, bot=True, reconnect=True)
