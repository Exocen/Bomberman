from constants import Messages, EntitiesNames, InitValues
import logging


class Entity:
    DESTRUCTABLE = False
    BLOCKABLE = False
    STATE = [0]
    STATE_INTERVAL = 0

    def __init__(self, position, mailbox):
        self._position = position
        self.mailbox = mailbox
        self.blocked = False
        self.killed = None
        self._dead = False
        self.message_queue = {}
        self.state_iterator = iter(self.STATE)
        self.state = next(self.state_iterator)

    def __str__(self):
        return f"{self.get_name()} {self.get_pos_tuple()}"

    async def update(self):
        self.message_queue = self.mailbox.get(self)
        self.message_handle()
        if self.message_queue:
            # Todo Exceptions
            error_mess = f"message_queue should be empty {self.message_queue}"
            logging.exception(error_mess)
            raise Exception(error_mess)

    def message_handle(self):
        if not self.message_queue:
            return
        self.killed_message_handle()
        if Messages.POSITION in self.message_queue:
            self.set_position(self.message_queue.pop(Messages.POSITION))
        if Messages.BLOCKED in self.message_queue:
            self.blocked = self.message_queue.pop(Messages.BLOCKED)

    def killed_message_handle(self):
        if Messages.KILLED in self.message_queue:
            killed = self.message_queue.pop(Messages.KILLED)
            if self.killed is None or killed is None:
                self.killed = killed
                self.kill()

    def get_position(self):
        return self._position

    def is_dead(self):
        return self._dead

    def kill(self):
        self._dead = True

    def state_update(self):
        """Update dying states"""
        message = {}
        if Messages.ITER_STATE in self.message_queue:
            state_interval = self.message_queue.pop(Messages.ITER_STATE)
            if state_interval <= 0:
                if self.state == self.STATE[-1]:
                    self.kill()
                else:
                    self.state = next(self.state_iterator)
                    message.update({Messages.ITER_STATE: self.STATE_INTERVAL})
            else:
                message.update({Messages.ITER_STATE: state_interval - InitValues.TICKS})
        if message:
            self.mailbox.send(self, message)

    def get_pos_tuple(self):
        return (self._position.x, self._position.y)

    def get_state(self):
        return {"x": self._position.x, "y": self._position.y, "dead": self.is_dead()}

    def set_position(self, position):
        if not self.blocked:
            self._position = position

    def get_name(self):
        return f"{EntitiesNames.ENTITY}"
