import asyncio
import random

from operator import itemgetter

import discord
import markovify
from discord.ext import commands

from .utils import checks


class Markov:
    """Fun little plugin that generates random sentences using markov chains"""

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.models = {}

    def is_suitable(self, message):
        disallowed_prefixes = ['!', '~']
        for prefix in disallowed_prefixes:
            if message.content.startswith(prefix):
                return False
        if not message.author.bot:
            return True

    def delim_for(self, result):
        result = result.strip()
        if result.endswith(".") or result.endswith("?"):
            return " "
        else:
            return ". "

    @commands.command()
    async def gen(self, ctx, num_sentences=3):
        if not ctx.channel in self.models:
            await self.bot.get_command("mkmodel").invoke(ctx)
        result = ""
        for i in range(3):
            sentence = self.models[ctx.channel].make_sentence()
            print(sentence)
            if result != "" and sentence is not None:
                result = result + self.delim_for(result)
            if sentence is not None:
                result = result + sentence
        if not result:
            result = "I couldn't generate any sentences :("
        await ctx.send(result)

    @commands.is_owner()
    @commands.command()
    async def mkmodel(self, ctx, num_messages: int = 1000):
        corpus = ""
        count = 0
        authors = {}
        async for message in ctx.channel.history(limit=num_messages):
            if self.is_suitable(message):
                if not message.author in authors:
                    authors[message.author] = 1
                else:
                    authors[message.author] += 1
                corpus = corpus + "\n" + message.content
                count += 1

        authors = sorted(authors.items(), key=itemgetter(1), reverse=True)
        limit = 3
        n = 0
        result = ""
        for author in authors:
            n += 1
            result = result + f"{n}. {author[0].mention}: {(author[1]/count) * 100:.2f}% "
            if n == limit:
                break

        output = f"Generated a markov model using the last {count} messages of {ctx.channel.mention}."
        if n >= 1:
            output = output + " Top contributors: " + result
        markov_model = await self.bot.loop.run_in_executor(None, markovify.NewlineText, corpus)
        self.models[ctx.channel] = markov_model
        await ctx.send(output)

    async def on_message(self, message):
        if message.channel in self.models and self.is_suitable(message):
            temp_model = markovify.NewlineText(message.content)
            new_model = await self.bot.loop.run_in_executor(None, markovify.combine,
                                                            [temp_model, self.models[message.channel]], [1, 1])
            self.models[message.channel] = new_model

            if random.uniform(0, 1.0) >= 0.85 or self.bot.user in message.mentions:
                result = ""
                for i in range(3):
                    sentence = self.models[message.channel].make_sentence()
                    if result != "" and sentence is not None:
                        result = result + self.delim_for(result)
                    if sentence is not None:
                        result = result + sentence
                await message.channel.send(result)


def setup(bot):
    bot.add_cog(Markov(bot))
