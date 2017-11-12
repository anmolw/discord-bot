from discord.ext import commands
import asyncio
import aiohttp
import config
import io
import re
from .utils import checks


class RocketLeague:
    def __init__(self, bot):
        self.bot = bot
        self.api_baseurl = "https://api.rocketleaguestats.com/v1/"
        self.api_header = {
            'authorization': config.rlstats_key
        }

    @commands.command(pass_context=True)
    async def rl(self, ctx, reference: str = None):
        """
        Retrieves a user's stats summary from rocketleaguestats.com
        """
        if not reference:
            await self.bot.say(f'{ctx.message.author.mention} Please specify steamid64 as a parameter')
            return
        async with self.bot.http_session.get(self.api_baseurl + 'player?unique_id=' + str(reference) + '&platform_id=1',
                                             headers=self.api_header) as response:
            json_response = await response.json()
            image_response = await aiohttp.get(json_response['signatureUrl'])
            image_data = io.BytesIO(await image_response.read())
            await self.bot.send_file(ctx.message.channel, image_data, filename='stats.png')
            print(json_response)

    async def api_player_lookup(self, player, platform):
        pass

    async def get_platform_list(self):
        pass


def setup(bot):
    bot.add_cog(RocketLeague(bot))
