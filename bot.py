import asyncio
import datetime
import sys
import traceback

import aiohttp
import discord
import discord.ext.commands

import config
from cogs.utils import checks, common

try:
    import uvloop
except ImportError:
    print("Using default asyncio event loop")
else:
    print("Using uvloop")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

load_cogs = [
    "cogs.core",
    "cogs.trivia",
    "cogs.misc",
    "cogs.errorhandler",
    "cogs.markov",
    "cogs.moderation",
    "cogs.thonk",
    "cogs.connectfour",
]


class Aimbot(discord.ext.commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!")
        self.http_session = aiohttp.ClientSession(loop=self.loop)
        self.startup_time = datetime.datetime.utcnow()


bot = Aimbot()


@bot.event
async def on_ready():
    print("Logged in as", bot.user.name)
    print("User ID:", bot.user.id)
    print("Invite URL: " + discord.utils.oauth_url(client_id=bot.user.id))


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


@bot.command()
async def time(ctx):
    """
    Displays the bot's local time
    """
    localtime = str(datetime.datetime.now())
    await ctx.send("The bot's local time is " + localtime)


if __name__ == "__main__":
    for plugin in load_cogs:
        try:
            bot.load_extension(plugin)
        except Exception as e:
            print(f"Could not load {plugin}: {type(e).__name__}")
            traceback.print_exc(file=sys.stdout)
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot.start(config.bot_token))
        # bot.run(config.bot_token)
    except KeyboardInterrupt:
        print("Received keyboard interrupt, terminating")
        loop.run_until_complete(bot.logout())
    finally:
        loop.close()
