from discord.ext import commands
from .utils import checks
import config


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.restricted_channels = set()
        for channel in config.restricted_channels:
            self.restricted_channels.add(channel)

    @commands.is_owner()
    @commands.command()
    async def restrict(self, ctx, state: bool):
        if state:
            if ctx.message.channel.id not in self.restricted_channels:
                self.restricted_channels.add(ctx.message.channel.id)
                await ctx.message.channel.send(
                    "Deleting all non-bot/webhook messages in this channel"
                )
        else:
            if ctx.message.channel.id in self.restricted_channels:
                self.restricted_channels.remove(ctx.message.channel.id)
                await ctx.message.channel.send("Channel restrictions turned off")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id in self.restricted_channels:
            if (
                message.author.id == self.bot.owner_id
                or message.author.bot
                or message.webhook_id is not None
            ):
                return
            await message.delete()


def setup(bot):
    bot.add_cog(Moderation(bot))
