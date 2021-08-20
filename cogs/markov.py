import asyncio
import random

from operator import itemgetter
from typing import Tuple, Union

import discord
import markovify
from discord.ext import commands

from .utils import checks
import config


class Markov(commands.Cog):
    """Fun little plugin that generates random sentences using markov chains"""

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.model = None
        self.markov_channels = set()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        for channel, count in config.markov_channels:
            await self._create_model(self.bot.get_channel(channel), count)
            self.markov_channels.add(channel)

    def is_suitable(self, message: discord.Message) -> bool:
        disallowed_prefixes = ["!", "~", "p!", "$"]
        for prefix in disallowed_prefixes:
            if message.content.startswith(prefix):
                return False
        if not message.author.bot:
            return True

    def process_message(self, message: discord.Message) -> str:
        result = message.content.replace(
            self.bot.user.mention, message.author.mention
        ).replace(f"<@!{self.bot.user.id}>", message.author.mention)
        return result

    def delim_for(self, result) -> str:
        result = result.strip()
        if result.endswith(".") or result.endswith("?") or result.endswith("!"):
            return " "
        else:
            return ". "

    async def add_to_model(self, message) -> None:
        temp_model = markovify.NewlineText(self.process_message(message))
        new_model = await self.bot.loop.run_in_executor(
            None,
            markovify.combine,
            [temp_model, self.model],
            [1, 1],
        )
        self.model = new_model

    def generate_message(self, prompt=None, num_sentences=3) -> Union[str, None]:
        if self.model is None:
            return
        result = ""
        for i in range(1, num_sentences):
            if prompt is not None:
                sentence = self.model.make_sentence_with_start(prompt, strict=False)
            else:
                sentence = self.model.make_sentence()
            if result != "" and sentence is not None:
                result = result + self.delim_for(result)
            if sentence is not None:
                result = result + sentence
        return result

    @commands.group(aliases=["mk"])
    async def markov(self, ctx) -> None:
        if ctx.invoked_subcommand is None:
            await self.bot.get_command("include").invoke(ctx)

    @commands.is_owner()
    @commands.guild_only()
    @markov.command()
    async def gen(self, ctx, num_sentences=3) -> None:
        if not ctx.channel in self.markov_channels:
            await self.bot.get_command("mkmodel").invoke(ctx)
        result = self.generate_message()
        if not result:
            result = "I couldn't generate any sentences :("
        await ctx.send(result)

    @commands.guild_only()
    @markov.command()
    async def prompt(self, ctx, prompt: str) -> None:
        if ctx.channel in self.markov_channels:
            result = self.model.make_sentence_with_start(prompt)
            if not result:
                result = "Couldn't generate a sentence \N{SLIGHTLY FROWNING FACE}"
            await ctx.send(result)

    @commands.guild_only()
    @markov.command()
    async def include(self, ctx, include: str) -> None:
        if ctx.channel in self.markov_channels:
            result = self.model.make_sentence_with_start(include, strict=False)
            if not result:
                result = "Couldn't generate a sentence \N{SLIGHTLY FROWNING FACE}"
            await ctx.send(result)

    async def _create_model(self, channel, num_messages) -> Tuple[int, list]:
        corpus = ""
        count = 0
        authors = {}
        async for message in channel.history(limit=num_messages):
            if self.is_suitable(message):
                if not message.author in authors:
                    authors[message.author] = 1
                else:
                    authors[message.author] += 1
                corpus = corpus + "\n" + self.process_message(message)
                count += 1

        authors = sorted(authors.items(), key=itemgetter(1), reverse=True)
        markov_model = await self.bot.loop.run_in_executor(
            None, markovify.NewlineText, corpus
        )
        self.model = markov_model
        return count, authors

    @commands.is_owner()
    @commands.guild_only()
    @markov.command()
    async def mkmodel(self, ctx, num_messages: int = 1000) -> None:
        count, authors = await self._create_model(ctx.channel, num_messages)
        result = ""
        limit = 3
        n = 0
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
    async def on_message(self, message: discord.Message) -> None:
        if (
            message.content.strip().lower().startswith("good bot")
            or message.content.strip()
            .lower()
            .startswith(f"{self.bot.user.mention} good bot")
            and message.guild is not None
        ):
            async for last_msg in message.channel.history(limit=1, before=message):
                if (
                    last_msg.author == self.bot.user
                    and not "good human" in last_msg.content.lower()
                ):
                    await message.channel.send(f"{message.author.mention} good human")

        else:
            if message.channel.id in self.markov_channels and self.is_suitable(message):
                self.add_to_model(message)

                if random.uniform(0, 1.0) >= 0.85 or self.bot.user in message.mentions:
                    result = self.generate_message()
                    if result is not None:
                        await message.channel.send(result)


def setup(bot) -> None:
    bot.add_cog(Markov(bot))
