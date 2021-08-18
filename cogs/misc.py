import asyncio
import datetime
import random
import re

import discord
from discord.ext import commands

import config
from random import choice

from .utils import checks, common


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.is_owner()
    @commands.command()
    async def joined(self, ctx, member: discord.Member = None):
        """
        Displays a user's join date for the current server. Defaults to the invoker of the command.
        """
        if member is None:
            member = ctx.message.author
        await ctx.send("{0} joined at {0.joined_at}".format(member))

    @commands.is_owner()
    @commands.command(hidden=True)
    async def globalnick(self, ctx, nickname: str):
        for member in ctx.guild.members:
            try:
                await member.edit(nick=nickname)
            except Exception as e:
                pass

    @commands.is_owner()
    @commands.command(hidden=True, name="re")
    async def regextest(self, ctx, expr: str, string: str):
        result = re.compile(expr).match(string)
        if result:
            try:
                result_str = ", ".join(result.groups())
                await ctx.send("Pattern matched. Result: " + result_str)
            except TypeError:
                await ctx.send("Pattern matched.")
        else:
            await ctx.send("String does not match pattern.")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def resetnicks(self, ctx):
        for member in ctx.guild.members:
            try:
                await member.edit(nick=None)
            except Exception as e:
                pass

    @commands.guild_only()
    @commands.command(name="8ball")
    async def eightball(self, ctx, question=None):
        """
        Ask the infinitely wise 8-ball a question
        """
        responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes - definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        await ctx.send(f"{ctx.author.mention} {choice(responses)}")

    # async def on_member_join(self, member):
    #     if not member.bot:
    #         await self.bot.send_message(discord.Object(id=config.greet_channel), f'Welcome to the server, {member.mention}!')


def setup(bot):
    bot.add_cog(Misc(bot))
