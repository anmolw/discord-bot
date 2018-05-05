import asyncio
import datetime
import inspect
import re
import sys
import traceback

import discord
from discord.ext import commands

from .utils import checks, common


class Core:
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(hidden=True)
    async def load(self, ctx, plugin: str = None):
        if plugin:
            await ctx.send(f'Attempting to load {plugin}')
            try:
                self.bot.load_extension('plugins.' + plugin)
            except Exception as e:
                await ctx.send(f'Could not load {plugin}')
                traceback.print_exc(file=sys.stdout)
            else:
                await ctx.send('\N{WHITE HEAVY CHECK MARK}')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def reload(self, ctx, plugin: str = None):
        if plugin:
            await ctx.send(f'Attempting reload of {plugin}')
            try:
                self.bot.unload_extension('plugins.' + plugin)
                self.bot.load_extension('plugins.' + plugin)
            except Exception as e:
                await ctx.send(f'Could not load {plugin}')
                traceback.print_exc(file=sys.stdout)
            else:
                await ctx.send('\N{WHITE HEAVY CHECK MARK}')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def unload(self, ctx, plugin: str = None):
        if plugin:
            await ctx.send(f'Attempting to unload {plugin}')
            try:
                self.bot.unload_extension('plugins.' + plugin)
            except Exception as e:
                await ctx.send(f'Could not unload {plugin}')
                traceback.print_exc(file=sys.stdout)
            else:
                await ctx.send('\N{WHITE HEAVY CHECK MARK}')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def td(self, ctx, time_delta: int):
        await ctx.send(common.pretty_print_time(time_delta))

    @commands.is_owner()
    @commands.command(hidden=True)
    async def cleanup(self, ctx, expression: str, num_messages: int = 100):
        # pattern = re.compile(expression)
        delete_list = []
        async for message in self.bot.logs_from(ctx.channel, limit=num_messages):
            # if pattern.match(message):
            if expression.lower() == message.content.lower().strip():
                delete_list.append(message)
        if len(delete_list) >= 1:
            delete_list.append(ctx.message)
            await ctx.channel.delete_messages(delete_list)

    @commands.is_owner()
    @commands.command(hidden=True)
    async def game(self, ctx, *, game_name):
        await self.bot.change_presence(game=discord.Game(name=game_name))

    @commands.is_owner()
    @commands.command(hidden=True, name="eval")
    async def evaluate(self, ctx, *, expression):
        env = {
            'bot': self.bot,
            'message': ctx.message,
            'channel': ctx.channel,
            'author': ctx.message.author,
            'guild': ctx.guild
        }
        env.update(globals())
        result = eval(expression, env)
        if inspect.isawaitable(result):
            result = await result
        await ctx.send(f'Result: {result}')

    @commands.is_owner()
    @commands.command(hidden=True, name="exec")
    async def execute(self, ctx, *, expression):
        env = {'bot': self.bot}
        result = exec(expression)
        if result:
            await ctx.send(f'Result: {result}')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def uptime(self, ctx):
        # uptime_result = str(system('uptime'))
        # await ctx.send('System uptime: '+uptime_result)
        curr = datetime.datetime.utcnow()
        await ctx.send(f"Bot uptime: {common.pretty_print_time((curr - self.bot.startup_time).total_seconds())}")

    @commands.is_owner()
    @commands.group(hidden=True)
    async def set(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Error: No property specified")

    @commands.is_owner()
    @set.command()
    async def name(self, new_username: str):
        await self.bot.edit_profile(username=new_username)


def setup(bot):
    bot.add_cog(Core(bot))
