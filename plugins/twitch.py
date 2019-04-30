import asyncio
import datetime
import sys

import discord
from discord.ext import commands

import config

from .utils import checks
from typing import NamedTuple


class Streamer(NamedTuple):
    login: str
    user_id: int
    profile_image_url: str
    last_stream_start: int = None


class Twitch(commands.Cog):
    """Plugin that polls the twitch API and sends notifications when certain channels go live"""

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.poll_task = None
        self.streamers = {}

    @commands.Cog.listener()
    async def on_ready(self):
        if self.poll_task is None:
            self.announce_channel = self.bot.get_channel(config.stream_channel)
            self.bot.loop.create_task(self.initialize_streamers())

    # @commands.is_owner()
    # @commands.command(name="ttest", hidden=True)
    async def initialize_streamers(self):
        headers = {"Client-ID": f"{config.twitch_client_id}"}
        users_endpoint = "https://api.twitch.tv/helix/users"
        params = [("login", channel) for channel in config.streams]
        try:
            async with self.bot.http_session.get(
                users_endpoint, params=params, headers=headers
            ) as response:
                response_json = await response.json()
                for channel in response_json["data"]:
                    self.streamers[channel["id"]] = Streamer(
                        channel["login"], channel["id"], channel["profile_image_url"]
                    )
            if self.poll_task is None:
                self.poll_task = self.bot.loop.create_task(self.poll())
        except Exception as e:
            print(f"{type(e).__name__}: {e}", file=sys.stderr)

    # @commands.is_owner()
    # @commands.command(hidden=True)
    async def poll(self):
        while True:
            headers = {"Client-ID": f"{config.twitch_client_id}"}
            streams_endpoint = "https://api.twitch.tv/helix/streams"
            params = [
                ("user_login", channel.login) for channel in self.streamers.values()
            ]
            try:
                async with self.bot.http_session.get(
                    streams_endpoint, params=params, headers=headers
                ) as response:
                    response_json = await response.json()
                    for stream in response_json["data"]:
                        if (
                            stream["started_at"]
                            != self.streamers[stream["user_id"]].last_stream_start
                        ):
                            self.streamers[
                                stream["user_id"]
                            ].last_stream_start = stream["started_at"]
                            await self.announce_stream(
                                self.streamers[stream["user_id"]],
                                stream["title"],
                                stream["thumbnail_url"],
                                stream["viewer_count"],
                            )
            except Exception as e:
                print(f"{type(e).__name__}: {e}", file=sys.stderr)
            await asyncio.sleep(30)

    async def announce_stream(self, streamer, title, thumbnail_url, viewers):
        # login_escaped = streamer.login.replace("_", "\_")
        # await self.bot.send_message(discord.Object(id=config.stream_channel), f"{login_escaped} just went live! Watch the stream at http://twitch.tv/{login_escaped}")
        embed = discord.Embed(
            title=title,
            url=f"http://twitch.tv/{streamer.login}",
            colour=0x6441A4,
            timestamp=datetime.datetime.utcnow(),
        )

        embed.set_author(
            name=streamer.login,
            url=f"http://twitch.tv/{streamer.login}",
            icon_url=streamer.profile_image_url,
        )
        embed.set_thumbnail(url=streamer.profile_image_url)
        embed.set_image(url=thumbnail_url.format(width=480, height=320))
        embed.add_field(name="Viewers", value=str(viewers), inline=True)
        await self.announce_channel.send(
            f"{streamer.login} is live on twitch!", embed=embed
        )

    def cog_unload(self):
        if self.poll_task is not None:
            self.poll_task.cancel()


def setup(bot):
    bot.add_cog(Twitch(bot))
