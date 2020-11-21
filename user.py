from constants import EntitiesNames, InitValues, Messages
from entity import Entity


class User(Entity):
    BOMB_CD = 1
    STATE_INTERVAL = 0.5
    DESTRUCTIBLE = True
    BLOCKABLE = True

    def __init__(self, ws, position, mailbox, mod, user_id):
        super().__init__(position, mailbox)
        self.ws = ws
        self.mod = mod
        self.id = user_id
        self.bomb_cd = 0
        self.nb_kill = 0
        self.nb_suicide = 0
        self.nb_death = 0
        self.bomb_dropped = False

    def __str__(self):
        return f"{self.get_name()} {self.mod} {self.ws.remote_address[0]}"

    def get_name(self):
        return EntitiesNames.USER

    def message_handle(self):
        Entity.message_handle(self)
        message = {}

        if Messages.BOMB_DROPPED in self.message_queue:
            self.bomb_dropped = self.message_queue.pop(Messages.BOMB_DROPPED)
            if self.bomb_dropped:
                self.bomb_cd = self.BOMB_CD

        # TODO cd handle -> entity
        if self.bomb_cd < 0:
            self.bomb_dropped = False
        else:
            self.bomb_cd -= InitValues.TICKS

        if Messages.RESET in self.message_queue:
            self._position = self.message_queue.pop(Messages.RESET)
            self.killed = None
            self.blocked = False
            message.update({Messages.BOMB_DROPPED: True})
            self._dead = False

        if message:
            self.mailbox.send(self, message)

    def killed_message_handle(self):
        if Messages.KILLED in self.message_queue:
            self.killed = self.message_queue.pop(Messages.KILLED)
            self.mailbox.send_to_list(EntitiesNames.LOG, self.mod, f"killed by *{self.killed.mod}*")
            self.kill()
            if self.killed is self:
                self.nb_suicide += 1
            elif isinstance(self.killed, User):
                self.killed.nb_kill += 1
                self.nb_death += 1

    def is_user_can_drop_bomb(self):
        return self.bomb_dropped is False and not self.killed and not self.blocked

    def get_state(self):
        return {
            "mod": self.mod,
            "id": self.id,
            "can_drop": self.is_user_can_drop_bomb(),
            "deaths": self.nb_death,
            "killed": self.nb_kill,
            "suicides": self.nb_suicide,
            **Entity.get_state(self),
        }
