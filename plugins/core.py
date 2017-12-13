import asyncio
import discord
from discord.ext import commands
import traceback
import sys
import re
import inspect
import datetime
from .utils import common
from .utils import checks


class Core:
    def __init__(self, bot):
        self.bot = bot

    @checks.is_owner()
    @commands.command(hidden=True)
    async def load(self, plugin: str = None):
        if plugin:
            await self.bot.say(f'Attempting to load {plugin}')
            try:
                self.bot.load_extension('plugins.' + plugin)
            except Exception as e:
                await self.bot.say(f'Could not load {plugin}')
                traceback.print_exc(file=sys.stdout)
            else:
                await self.bot.say('\N{WHITE HEAVY CHECK MARK}')

    @checks.is_owner()
    @commands.command(hidden=True)
    async def reload(self, plugin: str = None):
        if plugin:
            await self.bot.say(f'Attempting reload of {plugin}')
            try:
                self.bot.unload_extension('plugins.' + plugin)
                self.bot.load_extension('plugins.' + plugin)
            except Exception as e:
                await self.bot.say(f'Could not load {plugin}')
                traceback.print_exc(file=sys.stdout)
            else:
                await self.bot.say('\N{WHITE HEAVY CHECK MARK}')

    @checks.is_owner()
    @commands.command(hidden=True)
    async def unload(self, plugin: str = None):
        if plugin:
            await self.bot.say(f'Attempting to unload {plugin}')
            try:
                self.bot.unload_extension('plugins.' + plugin)
            except Exception as e:
                await self.bot.say(f'Could not unload {plugin}')
                traceback.print_exc(file=sys.stdout)
            else:
                await self.bot.say('\N{WHITE HEAVY CHECK MARK}')

    @checks.is_owner()
    @commands.command(hidden=True)
    async def td(self, time_delta: int):
        await self.bot.say(common.pretty_print_time(time_delta))

    @checks.is_owner()
    @commands.command(hidden=True, pass_context=True)
    async def cleanup(self, ctx, expression: str, num_messages: int = 100):
        # pattern = re.compile(expression)
        delete_list = []
        async for message in self.bot.logs_from(ctx.message.channel, limit=num_messages):
            # if pattern.match(message):
            if expression.lower() == message.content.lower().strip():
                delete_list.append(message)
        if len(delete_list) >= 1:
            delete_list.append(ctx.message)
            await self.bot.delete_messages(delete_list)


    @checks.is_owner()
    @commands.command(hidden=True)
    async def game(self, *, game_name):
        await self.bot.change_presence(game=discord.Game(name=game_name))

    @checks.is_owner()
    @commands.command(hidden=True, pass_context=True, name="eval")
    async def evaluate(self, ctx, *, expression):
        env = {
            'bot': self.bot,
            'message': ctx.message,
            'channel': ctx.message.channel,
            'author': ctx.message.author,
            'server': ctx.message.server
            }
        env.update(globals())
        result = eval(expression, env)
        if inspect.isawaitable(result):
            result = await result
        await self.bot.say(f'Result: {result}')

    @checks.is_owner()
    @commands.command(hidden=True, pass_context=True, name="exec")
    async def execute(self, ctx, *, expression):
        env = {'bot': self.bot}
        result = exec(expression)
        if result:
            await self.bot.say(f'Result: {result}')

    @checks.is_owner()
    @commands.command(hidden=True)
    async def uptime(self):
        # uptime_result = str(system('uptime'))
        # await self.bot.say('System uptime: '+uptime_result)
        curr = datetime.datetime.utcnow()
        await self.bot.say(f"Bot uptime: {common.pretty_print_time((curr - self.bot.startup_time).total_seconds())}")

    @checks.is_owner()
    @commands.group(pass_context=True, hidden=True)
    async def set(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.say("Error: No property specified")

    @checks.is_owner()
    @set.command()
    async def name(self, new_username: str):
        await self.bot.edit_profile(username=new_username)


def setup(bot):
    bot.add_cog(Core(bot))
