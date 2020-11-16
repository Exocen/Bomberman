from entity import Entity
from constants import EntitiesNames, Messages


class Bomb(Entity):
    STATE = [1, 2]
    STATE_INTERVAL = 1
    BLOCKABLE = True

    def __init__(self, position, mailbox, user):
        self.user = user
        Entity.__init__(self, position, mailbox)
        self.exploded = False
        # Start detonation
        self.mailbox.send(self, {Messages.ITER_STATE: self.STATE_INTERVAL})

    def get_name(self):
        return f"{EntitiesNames.BOMB}"

    def message_handle(self):
        Entity.message_handle(self)
        self.state_update()

    def get_state(self):
        return {"bomb_state": self.state, **Entity.get_state(self)}

    def kill(self):
        Entity.kill(self)
        self.mailbox.send_to_list(EntitiesNames.BOARD, Messages.BOOM, self)
