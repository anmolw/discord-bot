import discord
import random
import datetime
import typing
from discord.ext import commands


class XKCD(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.latestComicID = None
        self.latestComicTimestamp = None

    @commands.command()
    async def xkcd(self, ctx, id: typing.Optional[int] = 0, *args) -> None:
        """
        Fetch the latest xkcd comic. Can also be passed an id to fetch a specific comic
        """
        json = {}
        if "random" in args:
            json = await self.getRandomComic()
        else:
            json = await self.fetchComic(id)
        embed = self.createEmbed(json)
        await ctx.send(embed=embed)

    def fetchCooldownElapsed(self) -> bool:
        if self.latestComicTimestamp is None:
            return True
        else:
            delta = datetime.datetime.utcnow() - self.latestComicTimestamp
            return (delta.total_seconds() // 3600) > 6

    async def updateLatestComic(self) -> None:
        if self.latestComicID is None or self.fetchCooldownElapsed():
            latestComic = await self.fetchComic(0)
            latestID = int(latestComic["num"])
            self.latestComicID = latestID
            self.latestComicTimestamp = datetime.datetime.utcnow()

    async def getRandomComic(self) -> dict:
        await self.updateLatestComic()
        randomID = random.randint(1, self.latestComicID)
        json = await self.fetchComic(randomID)
        return json

    async def fetchComic(self, id: int) -> dict:
        response = {}
        if id < 0:
            await self.updateLatestComic()
            id = self.latestComicID - abs(id)
        if id == 0:
            response = await self.bot.http_session.get("https://xkcd.com/info.0.json")
        else:
            response = await self.bot.http_session.get(
                f"https://xkcd.com/{id}/info.0.json"
            )
        json = await response.json()
        return json

    def createEmbed(self, json: dict) -> discord.Embed:
        title = f"#{json['num']}: {json['title']}"
        embed = discord.Embed(
            title=title,
            timestamp=datetime.datetime(
                year=int(json["year"]), month=int(json["month"]), day=int(json["day"])
            ),
            url=f"https://xkcd.com/{json['num']}/",
        )
        embed.set_footer(text=json["alt"])
        embed.set_image(url=json["img"])
        # embed.add_field(name="Alt", value=json["alt"])
        return embed


def setup(bot):
    bot.add_cog(XKCD(bot))