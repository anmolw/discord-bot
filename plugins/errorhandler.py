import sys
import traceback
import discord.ext


class CommandErrorHandler:
    def __init__(self, bot):
        self.bot = bot


async def on_command_error(self, error, ctx):
    if isinstance(error, discord.ext.commands.CommandNotFound):
        return

    if isinstance(error, discord.ext.commands.DisabledCommand):
        try:
            await self.bot.send_message(ctx.message.channel, f'{ctx.command} has been disabled.')
        except:
            pass
        finally:
            return

    if isinstance(error, discord.ext.commands.NoPrivateMessage):
        try:
            await self.bot.send_message(ctx.message.channel, f'{ctx.command} cannot be used in Private Messages.')
        except:
            pass
        finally:
            return

    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
