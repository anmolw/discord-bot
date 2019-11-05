import sys
import traceback

import discord.ext
from discord.ext import commands


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


@commands.Cog.listener()
async def on_command_error(self, error, ctx):
    if isinstance(error, discord.ext.commands.CommandNotFound):
        return

    if isinstance(error, discord.ext.commands.DisabledCommand):
        try:
            await ctx.send(f"{ctx.command} has been disabled.")
        except:
            pass
        finally:
            return

    if isinstance(error, discord.ext.commands.NoPrivateMessage):
        try:
            await ctx.send(f"{ctx.command} cannot be used in Private Messages.")
        except:
            pass
        finally:
            return

    print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


@commands.Cog.listener()
async def on_error(self, error, ctx):
    print("Ignoring uncaught exception", file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
