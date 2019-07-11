import discord
import config
from asyncio import TimeoutError
from typing import NamedTuple
from discord.ext import commands
import datetime


class Game:
    def __init__(self, player1, player2=None):
        self._player1 = player1
        self._player2 = player2
        self._grid = [[0 for i in range(7)] for i in range(6)]
        self._turns_played = 0
        self._current_turn = player1
        self._over = False
        self._winner = None
        self._timed_out = False

    @property
    def player1(self):
        return self._player1

    @property
    def player2(self):
        return self._player2

    @player2.setter
    def player2(self, player):
        self._player2 = player

    @property
    def grid(self):
        return self._grid

    @property
    def turns_played(self):
        return self._turns_played

    @property
    def current_turn(self):
        return self._current_turn

    @current_turn.setter
    def current_turn(self, value):
        self._current_turn = value

    @property
    def over(self):
        return self._over

    @property
    def winner(self):
        return self._winner

    @property
    def timed_out(self):
        return self._timed_out

    @timed_out.setter
    def timed_out(self, value):
        self._timed_out = value

    def advance(self):
        self._turns_played += 1
        status = self.check_win()
        if status > 0:
            self._winner = self._player1 if status == 1 else self._player2
            self._over = True
        elif status == -1:
            self._over = True
        else:
            self._current_turn = (
                self._player1 if self._current_turn == self._player2 else self._player2
            )

    def place(self, column):
        for i in range(6):
            if self._grid[i][column] == 0 and (
                i == 5 or self._grid[i + 1][column] != 0
            ):  # Ensure space is empty and is the lowest available
                self._grid[i][column] = 1 if self._current_turn == self._player1 else 2
                self.advance()
                return True
        return False  # No available spaces in given column

    def check_win(self):
        # Check if a player has won. If yes, then return the player id
        # Horizontal check
        for row in range(6):
            for col in range(4):
                if self._grid[row][col] != 0:
                    if (
                        self._grid[row][col]
                        == self._grid[row][col + 1]
                        == self._grid[row][col + 2]
                        == self._grid[row][col + 3]
                    ):
                        return self._grid[row][col]

        # Vertical check
        for col in range(7):
            for row in range(3):
                if self._grid[row][col] != 0:
                    if (
                        self._grid[row][col]
                        == self._grid[row + 1][col]
                        == self._grid[row + 2][col]
                        == self._grid[row + 3][col]
                    ):
                        return self._grid[row][col]

        # Diagonal check
        # Top left to bottom right - column start
        for i in range(1, 4):
            col = i
            row = 0
            while col < 4 and row < 6:
                if (
                    self._grid[row][col] != 0
                    and self._grid[row][col]
                    == self._grid[row + 1][col + 1]
                    == self._grid[row + 2][col + 2]
                    == self._grid[row + 3][col + 3]
                ):
                    return self._grid[row][col]
                col += 1
                row += 1

        # Top left to bottom right - row start
        for i in range(3):
            col = 0
            row = i
            while col < 7 and row < 3:
                if (
                    self._grid[row][col] != 0
                    and self._grid[row][col]
                    == self._grid[row + 1][col + 1]
                    == self._grid[row + 2][col + 2]
                    == self._grid[row + 3][col + 3]
                ):
                    return self._grid[row][col]
                col += 1
                row += 1

        # Bottom left to top right - column start
        for i in reversed(range(1, 4)):
            col = i
            row = 5
            while col < 4 and row > 2:
                if (
                    self._grid[row][col] != 0
                    and self._grid[row][col]
                    == self._grid[row - 1][col + 1]
                    == self._grid[row - 2][col + 2]
                    == self._grid[row - 3][col + 3]
                ):
                    return self._grid[row][col]
                col += 1
                row -= 1

        # Bottom left to bottom right - row start
        for i in reversed(range(6)):
            col = 0
            row = i
            while col < 7 and row > 2:
                if (
                    self._grid[row][col] != 0
                    and self._grid[row][col]
                    == self._grid[row - 1][col + 1]
                    == self._grid[row - 2][col + 2]
                    == self._grid[row - 3][col + 3]
                ):
                    return self._grid[row][col]
                col += 1
                row -= 1

        return 0


class ConnectFour(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.game_reactions = [
        #     "{i}\N{COMBINING ENCLOSING KEYCAP}".encode("utf-8") for i in range(1, 8)
        # ]
        self.game_reactions = [
            b"1\xe2\x83\xa3".decode("utf-8"),
            b"2\xe2\x83\xa3".decode("utf-8"),
            b"3\xe2\x83\xa3".decode("utf-8"),
            b"4\xe2\x83\xa3".decode("utf-8"),
            b"5\xe2\x83\xa3".decode("utf-8"),
            b"6\xe2\x83\xa3".decode("utf-8"),
            b"7\xe2\x83\xa3".decode("utf-8"),
        ]
        self.current_players = set()

    @commands.guild_only()
    @commands.command(aliases=["c4"])
    async def connectfour(self, ctx):
        if ctx.message.author in self.current_players:
            await ctx.send(
                "You are already playing a game. Please finish it before starting another one."
            )
            return
        game = Game(ctx.message.author)
        self.current_players.add(ctx.message.author)
        game_msg = await ctx.send("Connect Four: Setting up game...")
        await self._add_reactions(game_msg)
        while not game.over and not game.timed_out:

            await game_msg.edit(content=self._draw_board(game))

            def reaction_check(reaction, user):
                return reaction.message.id == game_msg.id
                # if (
                #     user == game.current_turn
                #     or (game.player2 is None and user != game.player1)
                #     and self.bot.user in reaction.users().flatten()
                # ):
                #     return True
                # return False

            try:
                proceed = False
                start_turn_count = game.turns_played
                turn_start_time = datetime.datetime.now()
                while proceed != True:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=90.0, check=reaction_check
                    )
                    if reaction is not None:
                        chosen_column = self._reaction_to_number(reaction)
                        if chosen_column != -1:
                            if (
                                game.player2 is None
                                and game.player1 != game.current_turn
                                and user not in self.current_players
                            ):
                                game.player2 = user
                                game.current_turn = user
                                self.current_players.add(user)

                            if user == game.current_turn:
                                game.place(chosen_column)
                                proceed = True

                        await reaction.remove(user)

                        elapsed_time = datetime.datetime.now() - turn_start_time
                        if (
                            game.turns_played - start_turn_count == 0
                            and elapsed_time.seconds > 90
                        ):
                            raise TimeoutError()

            except TimeoutError as e:
                game.timed_out = True

        await game_msg.edit(content=self._draw_board(game))
        await game_msg.clear_reactions()
        self.current_players.remove(game.player1)
        if game.player2 is not None:
            self.current_players.remove(game.player2)

    def _reaction_to_number(self, reaction):
        for i in range(0, 7):
            if self.game_reactions[i] == str(reaction.emoji):
                return i
        return -1

    async def _add_reactions(self, msg):
        for i in range(1, 8):
            await msg.add_reaction(f"{i}\N{COMBINING ENCLOSING KEYCAP}")

    def _draw_board(self, game, timeout=False):
        result = ""

        player1 = f"\N{LARGE RED CIRCLE}{game.player1.display_name}"

        player2 = (
            "\N{LARGE BLUE CIRCLE}???"
            if game.player2 is None
            else f"\N{LARGE BLUE CIRCLE}{game.player2.display_name}"
        )
        # if game.current_turn == game.player1:
        #     player1 = f"**{player1}**"
        # else:
        #     player2 = f"**{player2}**"

        print(player1)
        print(player2)
        title_line = f"Connect Four: {player1} vs {player2}"
        result += title_line + "\n"
        if game.turns_played == 0:
            result += (
                "\N{BLACK LARGE SQUARE} \N{BLACK LARGE SQUARE} \N{BLACK LARGE SQUARE} \N{BLACK LARGE SQUARE} \N{BLACK LARGE SQUARE} \N{BLACK LARGE SQUARE} \N{BLACK LARGE SQUARE}\n"
                * 6
            )
        else:
            for i in range(6):
                for j in range(7):
                    if game.grid[i][j] == 1:
                        result += "\N{LARGE RED CIRCLE} "
                    elif game.grid[i][j] == 2:
                        result += "\N{LARGE BLUE CIRCLE} "
                    else:
                        result += "\N{BLACK LARGE SQUARE} "
                result += "\n"

        for i in range(1, 8):
            result += f"{i}\N{COMBINING ENCLOSING KEYCAP} "

        if game.timed_out:
            result += "\nGame timed out."
        if game.over:
            result += f"\nGame over! **{game.winner.display_name}** wins."

        print(result)
        return result


def setup(bot):
    bot.add_cog(ConnectFour(bot))
