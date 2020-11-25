from constants import Messages, InitValues
from user import User


class Bot(User):
    # Todo check memory clean

    BOT_DELAY = 0.5

    def __init__(self, game_board, position, mailbox, mod, user_id):
        self.game_board = game_board
        User.__init__(self, None, position, mailbox, mod, user_id)
        self.target = next(iter(game_board.users)) if game_board.users else None
        # Todo
        self.path = []
        self._bot_delay = 0

    async def update(self):
        self.bot_update()
        await User.update(self)

    def bot_update(self):
        if self._bot_delay > 0:
            self._bot_delay -= InitValues.TICKS
            return
        else:
            self._bot_delay = self.BOT_DELAY

        # target update
        if self.target is None or self.target not in self.game_board.users:
            self.target = next(iter(self.game_board.users)) if self.game_board.users else None

        # target pursuit
        if self.target is None or self.blocked:
            return

        path = self.game_board.find_path(self.get_position(), self.target.get_position())

        if not path:
            return
        new_position = path[0]

        self.game_board.check_explosions(self, new_position)

        self.mailbox.send(self, {Messages.POSITION: new_position})
