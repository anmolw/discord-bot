import asyncio
import io
import re

import discord
import aiohttp
from discord.ext import commands

import config

from .utils import checks


class RocketLeague:
    def __init__(self, bot):
        self.bot = bot
        self.api_baseurl = "https://api.rocketleaguestats.com/v1/"
        self.api_header = {'authorization': config.rlstats_key}

    @commands.command()
    async def rl(self, ctx, reference: str = None):
        """
        Retrieves a user's stats summary from rocketleaguestats.com
        """
        if not reference:
            await self.bot.say(f'{ctx.message.author.mention} Please specify steamid64 as a parameter')
            return
        async with self.bot.http_session.get(
                self.api_baseurl + 'player?unique_id=' + str(reference) + '&platform_id=1',
                headers=self.api_header) as response:
            json_response = await response.json()
            image_response = await self.bot.http_session.get(json_response['signatureUrl'])
            image = discord.File(fp=io.BytesIO(await image_response.read()), filename='stats.png')
            await ctx.send(file=image)
            print(json_response)

    async def api_player_lookup(self, player, platform):
        pass

    async def get_platform_list(self):
        pass


def setup(bot):
    bot.add_cog(RocketLeague(bot))
