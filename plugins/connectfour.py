import discord
import config
from asyncio import TimeoutError
from typing import NamedTuple
from discord.ext import commands


class Game:
    def __init__(self, player1, player2=None):
        self.player1 = player1
        self.player2 = player2
        self.grid = [[0 for i in range(7)] for i in range(6)]
        self.turns_played = 0
        self.current_turn = player1
        self.over = False
        self.winner = None
        self.timed_out = False

    def advance(self):
        self.turns_played += 1
        status = self.check_win()
        if status > 0:
            self.winner = self.player1 if status == 1 else self.player2
            self.over = True
        elif status == -1:
            self.over = True
        else:
            self.current_turn = (
                self.player1 if self.current_turn == self.player2 else self.player2
            )

    def place(self, column):
        for i in range(7):
            if self.grid[i][column] == 0 and (
                i == 6 or self.grid[i + 1][column] != 0
            ):  # Ensure space is empty and is the lowest available
                self.grid[i][column] = 1 if self.current_turn == self.player1 else 2
                self.advance()
                return True
        return False  # No available spaces in given column

    def check_win(self):
        # Check if a player has won. If yes, then return the player id
        # Horizontal check
        for row in range(6):
            for col in range(4):
                if self.grid[row][col] != 0:
                    if (
                        self.grid[row][col]
                        == self.grid[row][col + 1]
                        == self.grid[row][col + 2]
                        == self.grid[row][col + 3]
                    ):
                        return self.grid[row][col]

        # Vertical check
        for col in range(7):
            for row in range(3):
                if self.grid[row][col] != 0:
                    if (
                        self.grid[row][col]
                        == self.grid[row + 1][col]
                        == self.grid[row + 2][col]
                        == self.grid[row + 3][col]
                    ):
                        return self.grid[row][col]

        # Diagonal check
        # Top left to bottom right - column start
        for i in range(1, 4):
            col = i
            row = 0
            while col < 4 and row < 6:
                if (
                    self.grid[row][col] != 0
                    and self.grid[row][col]
                    == self.grid[row + 1][col + 1]
                    == self.grid[row + 2][col + 2]
                    == self.grid[row + 3][col + 3]
                ):
                    return self.grid[row][col]
                col += 1
                row += 1

        # Top left to bottom right - row start
        for i in range(3):
            col = 0
            row = i
            while col < 7 and row < 3:
                if (
                    self.grid[row][col] != 0
                    and self.grid[row][col]
                    == self.grid[row + 1][col + 1]
                    == self.grid[row + 2][col + 2]
                    == self.grid[row + 3][col + 3]
                ):
                    return self.grid[row][col]
                col += 1
                row += 1

        # Bottom left to top right - column start
        for i in reversed(range(1, 4)):
            col = i
            row = 5
            while col < 4 and row > 2:
                if (
                    self.grid[row][col] != 0
                    and self.grid[row][col]
                    == self.grid[row - 1][col + 1]
                    == self.grid[row - 2][col + 2]
                    == self.grid[row - 3][col + 3]
                ):
                    return self.grid[row][col]
                col += 1
                row -= 1

        # Bottom left to bottom right - row start
        for i in reversed(range(6)):
            col = 0
            row = i
            while col < 7 and row > 2:
                if (
                    self.grid[row][col] != 0
                    and self.grid[row][col]
                    == self.grid[row - 1][col + 1]
                    == self.grid[row - 2][col + 2]
                    == self.grid[row - 3][col + 3]
                ):
                    return self.grid[row][col]
                col += 1
                row -= 1

        return 0


class ConnectFour(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game_reactions = ["{i}\N{COMBINING ENCLOSING KEYCAP}" for i in range(1, 8)]
        self.current_players = set()

    @commands.guild_only()
    @commands.command(aliases=["c4"])
    @commands.is_owner()
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
                if (
                    user == game.current_turn
                    or (game.player2 is None and user != game.player1)
                    and self.bot.user in reaction.users().flatten()
                ):
                    return True
                return False

            try:
                proceed = False
                while proceed != True:
                    reaction = await self.bot.wait_for(
                        "reaction_add", timeout=90.0, check=reaction_check
                    )
                    if reaction is not None:
                        chosen_column = self._reaction_to_number(reaction)
                        if chosen_column != 0:
                            if (
                                game.player2 is None
                                and game.player1 != game.current_turn
                                and reaction.user not in self.current_players
                            ):
                                game.player2 = reaction.user
                                game.current_turn = reaction.user
                                self.current_players.add(reaction.user)
                            if reaction.user == game.current_turn:
                                game.place(chosen_column)
                                proceed = True

            except TimeoutError as e:
                game.timed_out = True
                self._end_game(game_msg, game, timeout=True)

                await self._reset_reactions(game_msg, game)

        await game_msg.edit(content=self._draw_board(game))
        self.current_players.remove(game.player1)
        if game.player2 is not None:
            self.current_players.remove(game.player2)

    def _reaction_to_number(self, reaction):
        for i in range(0, 7):
            if self.game_reactions[i] == str(reaction.emoji):
                return i
        return 0

    async def _add_reactions(self, msg):
        for i in range(1, 8):
            await msg.add_reaction(f"{i}\N{COMBINING ENCLOSING KEYCAP}")

    async def _reset_reactions(self, msg, game):
        for reaction in msg.reactions():
            for user in reaction.users().flatten():
                if user != self.bot.user:
                    reaction.remove(reaction.user)

    def _draw_board(self, game, timeout=False):
        result = ""

        player1 = f"\N{LARGE RED CIRCLE}{game.player1.display_name}"

        player2 = (
            "\N{LARGE BLUE CIRCLE}" + "???"
            if game.player2 is None
            else f"{game.player2.display_name}"
        )
        if game.current_turn == player1:
            player1 = "**" + player1 + "**"
        else:
            player2 = "**" + player2 + "**"

        title_line = f"Connect Four: "
        title_line += player1 + " vs " + player2
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
                result += "/n"

        for i in range(1, 8):
            result += f"{i}\N{COMBINING ENCLOSING KEYCAP} "

        if game.over:
            result += f"\nGame over! {game.winner.display_name} wins."
        return result


def setup(bot):
    bot.add_cog(ConnectFour(bot))
