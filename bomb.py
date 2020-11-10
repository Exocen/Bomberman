from entity import Entity
from constants import EntitiesNames, InitValues, Messages


class Bomb(Entity):
    STATE = [1, 2]
    STATE_INTERVAL = int(0.5 / InitValues.TICKS)
    BLOCKABLE = True

    def __init__(self, position, mailbox, user):
        self.user = user
        Entity.__init__(self, position, mailbox)
        self.explosed = False
        # Start detonation
        self.mailbox.send(self, {Messages.ITER_STATE: self.STATE_INTERVAL})

    def get_name(self):
        return f"{EntitiesNames.BOMB}"

    async def update(self):
        await Entity.update(self)
        self.state_update()

        if self.message_queue:
            raise f"message_queue should be empty {self.message_queue}"

    def get_state(self):
        return {"bomb_state": self.state, **Entity.get_state(self)}

    def kill(self):
        Entity.kill(self)
        self.mailbox.sendToList(EntitiesNames.BOARD, Messages.BOOM, [self])
