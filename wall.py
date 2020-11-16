from entity import Entity
from constants import EntitiesNames


class Wall(Entity):
    DESTRUCTIBLE = True
    BLOCKABLE = True

    def __init__(self, position, mailbox):
        Entity.__init__(self, position, mailbox)

    def get_name(self):
        return EntitiesNames.WALL

    def next_state(self):
        self.state = next(self.state_iterator, None)

    def get_state(self):
        return {"wall_state": self.state, **Entity.get_state(self)}
