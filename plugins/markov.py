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

    @commands.command(pass_context=True)
    async def gen(self, ctx, num_sentences=3):
        if not ctx.message.channel in self.models:
            await self.bot.get_command("mkmodel").invoke(ctx)
        result = ""
        for i in range(3):
            sentence = self.models[ctx.message.channel].make_sentence()
            print(sentence)
            if result != "" and sentence is not None:
                delim = " " if result.endswith(".") else ". "
                result = result + delim
            if sentence is not None:
                result = result + sentence
        if not result:
            result = "I couldn't generate any sentences :("
        await self.bot.say(result)

    @checks.is_owner()
    @commands.command(pass_context=True)
    async def mkmodel(self, ctx, num_messages: int = 1000):
        corpus = ""
        count = 0
        authors = {}
        async for message in self.bot.logs_from(ctx.message.channel, limit=num_messages):
            if not message.content.startswith("!") and not message.author.bot:
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

        output = f"Generated a markov model using the last {count} messages of {ctx.message.channel.mention}."
        if n >= 1:
            output = output + " Top contributors: " + result
        markov_model = await self.bot.loop.run_in_executor(None, markovify.NewlineText, corpus)
        self.models[ctx.message.channel] = markov_model
        await self.bot.say(output)

    async def on_message(self, message):
        if message.channel in self.models and not message.content.startswith("!") and not message.author.bot:
            temp_model = markovify.NewlineText(message.content)
            new_model = await self.bot.loop.run_in_executor(None, markovify.combine,
                                                            [temp_model, self.models[message.channel]], [1, 1])
            self.models[message.channel] = new_model

            if random.uniform(0, 1.0) >= 0.85:
                result = ""
                for i in range(3):
                    sentence = self.models[message.channel].make_sentence()
                    if result != "" and sentence is not None:
                        delim = " " if result.endswith(".") else ". "
                        result = result + delim
                    if sentence is not None:
                        result = result + sentence
                await self.bot.send_message(message.channel, result)


def setup(bot):
    bot.add_cog(Markov(bot))
