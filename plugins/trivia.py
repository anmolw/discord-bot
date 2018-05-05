import asyncio
import json
import sys
import traceback
from html import unescape
from random import randint, sample, shuffle
from timeit import default_timer as timer

from discord import Game
from discord.ext import commands

from .utils import checks


class Trivia:
    def __init__(self, bot):
        self.token = None
        self.request_count = 0
        self.bot = bot
        self.ongoing_games = set()
        self.last_response_time = None

    @checks.trivia_whitelist()
    @commands.guild_only()
    @commands.command(aliases=['t'])
    async def trivia(self, ctx, num_questions: int = 1, *, args: str = None):
        """
        Play a game of trivia. Questions are multiple choice, and can be responded to by either typing out the answer, or # followed by the answer number.
        Eg. #1, #2
        """
        if num_questions <= 0:
            num_questions = 1
        elif num_questions > 10:
            num_questions = 10
        if num_questions != 1:
            await ctx.send(f'Starting new game with {num_questions} questions.')

        if ctx.channel in self.ongoing_games:
            await ctx.send(f'There is already a trivia game in progress in #{ctx.channel}')
            return
        self.ongoing_games.add(ctx.channel)
        # await bot.say(f'#{ctx.channel} added to ongoing games')
        await self._update_trivia_presence()
        if args and 'test' in args:
            await self._start_game(ctx.channel, num_questions, True)
        else:
            await self._start_game(ctx.channel, num_questions, False)
        self.ongoing_games.remove(ctx.channel)
        await self._update_trivia_presence()

    @commands.is_owner()
    @commands.command(hidden=True)
    async def tq(self, ctx):
        questions = await self._get_questions(1)
        await ctx.send('__Category__: ' + questions[0]['category'])
        await ctx.send('__Question__: ' + questions[0]['question'])
        await ctx.send('__Choices__: ' + _format_answers(questions[0]))

    async def _start_game(self, channel, num_questions, hangman=False):
        try:
            questions = await self._get_questions(num_questions)
        except Exception as e:
            await channel.send(f"Error encountered while fetching questions: {type(e).__name__}")
            traceback.print_exc(file=sys.stderr)
            return

        for question in questions:

            question_fmt_string = f"__Category__: {questions[0]['category']}\n__Question__: {question['question']}"

            hint_task = None
            if hangman:
                hint_task = self.bot.loop.create_task(self._hint_task_v2(channel, question['correct_answer']))
            else:
                choices = _shuffle_choices(question)
                question_fmt_string = question_fmt_string + "\n" + _format_answers(choices)
                # await self.bot.send_message(channel, '__Choices__: '+_format_answers(choices))

            await channel.send(question_fmt_string)
            time_asked = timer()

            def guess_check(ctx):
                return ctx.author != self.bot.user and ctx.channel == channel

            while True:
                guess = None
                try:
                    guess = await self.bot.wait_for('message', timeout=60.0, check=guess_check)
                except asyncio.TimeoutError:
                    pass

                if timer() - time_asked > 60:
                    await channel.send(f"Time's up! The answer was: {question['correct_answer']}")
                    if hangman:
                        hint_task.cancel()
                    break
                if not guess:
                    continue
                if not hangman and guess.content.strip().startswith("#") and guess.content.strip()[1].isdigit():
                    guess_num = int(guess.content.strip()[1])
                    if 1 <= guess_num <= 4 and choices[guess_num - 1] == question['correct_answer']:
                        await self._congratulate(guess)
                        break

                if guess.content.lower().strip() == question['correct_answer'].lower().strip():
                    if hangman:
                        hint_task.cancel()
                    await self._congratulate(guess)
                    break

    async def _congratulate(self, guess):
        print('Correct answer!')
        await guess.add_reaction('\N{WHITE HEAVY CHECK MARK}')
        await guess.channel.send(f'Correct answer, {guess.author.mention}!')

    @commands.is_owner()
    @commands.command(pass_context=True, hidden=True)
    async def htest(self, ctx, *, answer):
        await ctx.send("Creating hint task")
        task = self.bot.loop.create_task(self._hint_task(ctx.channel, answer))

    @commands.is_owner()
    @commands.command(hidden=True)
    async def tdebug(self, ctx):
        await ctx.send(f'API token: {self.token} # of requests: {self.request_count}')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def htest2(self, ctx, *, answer):
        await ctx.send("Creating hint task")
        task = self.bot.loop.create_task(self._hint_task_v2(ctx.channel, answer))

    async def _hint_task(self, channel, answer):
        await channel.send("Hint task created")
        answer = answer.strip()
        hint_string_source = ['\_ '] * len(answer)
        revealed_chars = []
        reveal_per_hint = int(len(answer) * 0.25)
        start_time = timer()
        for i in range(3):
            await asyncio.sleep(5)
            reveal_now = reveal_per_hint
            while reveal_now > 0:
                temp_char = randint(0, len(answer) - 1)
                if temp_char not in revealed_chars:
                    revealed_chars.append(temp_char)
                    hint_string_source[temp_char] = answer[temp_char]
                    reveal_now = reveal_now - 1
            hint_string = "".join(hint_string_source)
            await channel.send(f"Hint: {hint_string} T+{str(int(timer() - start_time))}s")

    async def _hint_task_v2(self, channel, answer):
        await channel.send("Hint task created")
        answer = answer.strip()
        hint_reveal_pool = [i for i in range(len(answer)) if answer[i].isdigit() or answer[i].isalpha()]
        hint_string_source = ['\_ ' if elem.isdigit() or elem.isalpha() else elem.replace(' ', '  ') for elem in answer]
        reveal_per_hint = int(len(answer) * 0.25)
        start_time = timer()
        for i in range(3):
            await asyncio.sleep(15)
            if len(hint_reveal_pool) >= reveal_per_hint:
                reveal_now = sample(hint_reveal_pool, reveal_per_hint)
                # hint_reveal_pool = [elem for elem in hint_reveal_pool if elem not in reveal_now]
                for elem in reveal_now:
                    hint_reveal_pool.remove(elem)
                    hint_string_source[elem] = answer[elem]
            hint_string = "".join(hint_string_source)
            await channel.send(f"Hint: {hint_string} T+{str(int(timer() - start_time))}s")

    async def _update_trivia_presence(self):
        pass
        # if not self.ongoing_games:
        #     await self.bot.change_presence(game=None)
        # else:
        #     num_games = len(self.ongoing_games)
        #     await self.bot.change_presence(game=Game(name=f'{num_games} Trivia Game{"s" if num_games > 1 else ""}'))

    async def _get_questions(self, num_questions=10, category=None, multiple_choice=True):
        params = {'amount': num_questions, 'type': 'multiple', 'encoding': 'base64'}

        if not self.token or (self.last_response_time and (timer() - self.last_response_time >= 21600)):
            await self._request_token()

        params['token'] = self.token

        async with self.bot.http_session.get('https://opentdb.com/api.php', params=params) as response:
            json_response = await response.json()
            self.last_response_time = timer()
            self.request_count += 1
            for question in json_response['results']:
                question['question'] = unescape(question['question'])
                question['correct_answer'] = unescape(question['correct_answer'])
                for i in range(len(question['incorrect_answers'])):
                    question['incorrect_answers'][i] = unescape(question['incorrect_answers'][i])
            print(json_response)
            return json_response['results']

    async def _request_token(self):
        # params = {'command': 'request'}
        async with self.bot.http_session.get('https://opentdb.com/api_token.php?command=request') as response:
            json_response = await response.json()
            print(json_response)
            if json_response['response_code'] == 0:
                self.token = json_response['token']
                self.request_count += 1


def _score_answer(difficulty, answer_time, game_type, num_guesses):
    difficulty_mapping = {"easy": 0.75, "medium": 1, "hard": 1.25}
    base_score = 10
    if num_guesses > 1 and game_type == "":
        return 0
    else:
        return difficulty_mapping[difficulty] * base_score


def _shuffle_choices(question):
    choices = [i for i in question['incorrect_answers']]
    choices.append(question['correct_answer'])
    shuffle(choices)
    return choices


def _format_answers(choices):
    result_list = ['**' + str((i + 1)) + ')** ' + choices[i] for i in range(len(choices))]
    result = ' '.join(result_list)
    return result


def setup(bot):
    bot.add_cog(Trivia(bot))
