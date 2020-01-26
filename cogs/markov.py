import asyncio
import random

from operator import itemgetter

import discord
import markovify
from discord.ext import commands

from .utils import checks
import config


class Markov(commands.Cog):
    """Fun little plugin that generates random sentences using markov chains"""

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.models = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for channel, count in config.markov_channels:
            await self._create_model(self.bot.get_channel(channel), count)

    def is_suitable(self, message):
        disallowed_prefixes = ["!", "~", "p!"]
        for prefix in disallowed_prefixes:
            if message.content.startswith(prefix):
                return False
        if not message.author.bot:
            return True

    def delim_for(self, result):
        result = result.strip()
        if result.endswith(".") or result.endswith("?") or result.endswith("!"):
            return " "
        else:
            return ". "

    @commands.group(aliases=["mk"])
    async def markov(self, ctx):
        pass

    @commands.is_owner()
    @commands.guild_only()
    @markov.command()
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

    @commands.guild_only()
    @markov.command()
    async def prompt(self, ctx, prompt: str):
        if ctx.channel in self.models:
            result = self.models[ctx.channel].make_sentence_with_start(prompt)
            if not result:
                result = "Couldn't generate a sentence \N{SLIGHTLY FROWNING FACE}"
            await ctx.send(result)

    @commands.guild_only()
    @markov.command()
    async def include(self, ctx, include: str):
        if ctx.channel in self.models:
            result = self.models[ctx.channel].make_sentence_with_start(
                include, strict=False
            )
            if not result:
                result = "Couldn't generate a sentence \N{SLIGHTLY FROWNING FACE}"
            await ctx.send(result)

    async def _create_model(self, channel, num_messages):
        corpus = ""
        count = 0
        authors = {}
        async for message in channel.history(limit=num_messages):
            if self.is_suitable(message):
                if not message.author in authors:
                    authors[message.author] = 1
                else:
                    authors[message.author] += 1
                corpus = corpus + "\n" + message.content
                count += 1

        authors = sorted(authors.items(), key=itemgetter(1), reverse=True)
        markov_model = await self.bot.loop.run_in_executor(
            None, markovify.NewlineText, corpus
        )
        self.models[channel] = markov_model
        return count, authors

    @commands.is_owner()
    @commands.guild_only()
    @markov.command()
    async def mkmodel(self, ctx, num_messages: int = 1000):
        count, authors = await self._create_model(ctx.channel, num_messages)
        result = ""
        limit = 3
        for author in authors:
            n += 1
            result = (
                result + f"{n}. {author[0].mention}: {(author[1]/count) * 100:.2f}% "
            )
            if n == limit:
                break

        output = f"Generated a markov model using the last {count} messages of {ctx.channel.mention}."
        if n >= 1:
            output = output + " Top contributors: " + result

        await ctx.send(output)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.strip().lower().startswith(
            "good bot"
        ) or message.content.strip().lower().startswith(
            f"{self.bot.user.mention} good bot"
        ):
            async for last_msg in message.channel.history(limit=1, before=message):
                if (
                    last_msg.author == self.bot.user
                    and not "good human" in last_msg.content.lower()
                ):
                    await message.channel.send(f"{message.author.mention} good human")

        else:
            if message.channel in self.models and self.is_suitable(message):
                temp_model = markovify.NewlineText(message.content)
                new_model = await self.bot.loop.run_in_executor(
                    None,
                    markovify.combine,
                    [temp_model, self.models[message.channel]],
                    [1, 1],
                )
                self.models[message.channel] = new_model

                if random.uniform(0, 1.0) >= 0.85 or self.bot.user in message.mentions:
                    result = ""
                    for i in range(random.randint(1, 3)):
                        sentence = self.models[message.channel].make_sentence()
                        if result != "" and sentence is not None:
                            result = result + self.delim_for(result)
                        if sentence is not None:
                            result = result + sentence
                    if result != "":
                        await message.channel.send(result)


def setup(bot):
    bot.add_cog(Markov(bot))
