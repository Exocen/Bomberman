from entity import Entity
from constants import EntitiesNames, InitValues, Messages


class Wall(Entity):
    DESTRUCTABLE = True
    BLOCKABLE = True

    def __init__(self, position, mailbox):
        Entity.__init__(self, position, mailbox)

    def get_name(self):
        return EntitiesNames.WALL

    async def update(self):
        await Entity.update(self)

        if self.message_queue:
            raise f'message_queue should be empty {self.message_queue}'

    def next_state(self):
        self.state = next(self.state_iterator, None)

    def get_state(self):
        return {'wall_state': self.state, **Entity.get_state(self)}