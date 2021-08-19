import asyncio
import datetime
import sys
import traceback

import aiohttp
import discord
import discord.ext.commands

import config
from cogs.utils import checks, common

load_cogs = [
    "cogs.core",
    "cogs.trivia",
    "cogs.misc",
    "cogs.errorhandler",
    "cogs.markov",
    "cogs.moderation",
    "cogs.connectfour",
    "cogs.xkcd",
]


class Aimbot(discord.ext.commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        super().__init__(command_prefix="!", intents=intents)
        self.http_session = aiohttp.ClientSession(loop=self.loop)
        self.startup_time = datetime.datetime.utcnow()

    async def on_message(self, message) -> None:
        if message.author.bot:
            return
        await self.process_commands(message)

    async def on_ready(self) -> None:
        print("Logged in as", self.user.name)
        print("User ID:", self.user.id)
        print("Invite URL: " + discord.utils.oauth_url(client_id=self.user.id))


def setup(bot: Aimbot) -> None:
    for plugin in load_cogs:
        try:
            bot.load_extension(plugin)
        except Exception as e:
            print(f"Could not load {plugin}: {type(e).__name__}")
            traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    bot = Aimbot()
    setup(bot)
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot.start(config.bot_token))
        # bot.run(config.bot_token)
    except KeyboardInterrupt:
        print("Received keyboard interrupt, terminating")
        loop.run_until_complete(bot.logout())
    finally:
        loop.close()
