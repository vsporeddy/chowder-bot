import os
import discord
import asyncio
import json
import sqlite3 as sqlite

from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands import CommandNotFound

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

with open("config.json", "r") as read_file:
    config = json.load(read_file)

def create_db():
    if os.path.isfile(config["DATABASE"]):
        print("Database file found.")
    else:
        print("Database not found. Creating...")
        conn = sqlite.connect(config["DATABASE"])
        c = conn.cursor()
        c.execute("""CREATE TABLE accounts
                    (id text NOT NULL PRIMARY KEY, name text, balance integer)""")
        c.execute("""CREATE TABLE transactions
                    (receiver_id text NOT NULL, amount integer, sender_id text,
                    FOREIGN KEY(receiver_id) REFERENCES accounts(id))""")
        c.execute("INSERT INTO accounts VALUES ('1', 'BANK', 1)")
        conn.commit()
        conn.close()
        print("Done.")

def get_prefix(bot, message):
    prefixes = config["prefixes"]
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(command_prefix=get_prefix)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error

extensions = ["games.game_cog", "chowder.chowder_cog", "governance.governance_cog"]

if __name__ == "__main__":
    for extension in extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    create_db()
    guild = discord.utils.get(bot.guilds, name=config["guild"])

    print(
        f"{bot.user.name} is connected to the following guild:\n"
        f"{guild.name}(id: {guild.id})"
    )

bot.run(TOKEN, bot=True, reconnect=True)
