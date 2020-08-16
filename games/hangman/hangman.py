"""
    Hang Chowder from a rope
"""


class Hangman():
    def __init__(self, ctx, players):
        self.ctx = ctx
        self.players = players

    async def start(self):
        await self.ctx.send(f"Starting a game of **hangman* with [{', '.join([p.mention for p in self.players])}]")
