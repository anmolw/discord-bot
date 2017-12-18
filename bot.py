import asyncio
import datetime
import sys
import traceback

import aiohttp
import discord
import discord.ext.commands

import config
from plugins.utils import checks, common

try:
    import uvloop
except ImportError:
    print('Using default asyncio event loop')
else:
    print('Using uvloop')
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

load_plugins = [
    "plugins.core",
    "plugins.trivia",
    "plugins.rocketleague",
    "plugins.misc",
    "plugins.errorhandler",
    "plugins.music"
]


class Aimbot(discord.ext.commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!")
        self.http_session = aiohttp.ClientSession(loop=self.loop)
        self.startup_time = datetime.datetime.utcnow()


bot = Aimbot()


@bot.event
async def on_ready():
    print('Logged in as', bot.user.name)
    print('User ID:', bot.user.id)
    print('Invite URL: ' + discord.utils.oauth_url(client_id=bot.user.id))


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


@bot.command()
async def time():
    """
    Displays the bot's local time
    """
    localtime = str(datetime.datetime.now())
    await bot.say('The bot\'s local time is ' + localtime)


if __name__ == '__main__':
    for plugin in load_plugins:
        try:
            bot.load_extension(plugin)
        except Exception as e:
            print(f"Could not load {plugin}: {type(e).__name__}")
            traceback.print_exc(file=sys.stdout)

    bot.run(config.bot_token)
