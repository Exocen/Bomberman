import logging

from constants import EntitiesNames, InitValues, Messages
from entity import Entity


class User(Entity):
    BOMB_CD = int(1/InitValues.TICKS)
    STATE_INTERVAL = int(0.50/InitValues.TICKS)
    DESTRUCTABLE = True
    BLOCKABLE = True

    def __init__(self, ws, position, mailbox, mod, id):
        super().__init__(position, mailbox)
        self.ws = ws
        self.mod = mod
        self.id = id
        self.bomb_cd_state = False
        self.bomb_delay = None
        self.nb_kill = 0
        self.nb_suicide = 0
        self.nb_death = 0
        self.bomb_dropped = False

    def __str__(self):
        return f'{self.get_name()} {self.mod} {self.ws.remote_address[0]}'

    def get_name(self):
        return EntitiesNames.USER

    async def update(self):
        await Entity.update(self)
        message = {}

        if Messages.BOMB_DROPPED in self.message_queue:
            self.bomb_dropped = self.message_queue.pop(Messages.BOMB_DROPPED)
            if self.bomb_dropped:
                message.update({Messages.BOMB_CD: self.BOMB_CD})

        if Messages.BOMB_CD in self.message_queue:
            bomb_cd = self.message_queue.pop(Messages.BOMB_CD)
            if bomb_cd <= 0:
                self.bomb_dropped = False
            else:
                message.update({Messages.BOMB_CD: bomb_cd - 1})

        if Messages.RESET in self.message_queue:
            self._position = self.message_queue.pop(Messages.RESET)
            self.killed = None
            self.blocked = False
            message.update({Messages.BOMB_DROPPED: True})
            self._dead = False

        if message:
            self.mailbox.send(self, message)

        if self.message_queue:
            # Todo exceptions
            logging.error(f'message_queue should be empty : {self.message_queue}')

    def killed_message_handle(self):
            if Messages.KILLED in self.message_queue:
                self.killed = self.message_queue.pop(Messages.KILLED)
                self.mailbox.sendToList(EntitiesNames.LOG,
                                        self.mod,
                                        [f'killed by *{self.killed.mod}*'])
                self.kill()
                if self.killed is self:
                    self.nb_suicide += 1
                elif isinstance(self.killed, User):
                    self.killed.nb_kill += 1
                    self.nb_death += 1


    def is_user_can_drop_bomb(self):
        return self.bomb_dropped is False and not self.killed and not self.blocked

    def get_state(self):
        return {'mod': self.mod,
                'id': self.id,
                'can_drop': self.is_user_can_drop_bomb(),
                'drop_delay': self.bomb_delay,
                'deaths': self.nb_death,
                'killed': self.nb_kill,
                'suicides': self.nb_suicide,
                **Entity.get_state(self)}
