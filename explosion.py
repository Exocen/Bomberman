from entity import Entity
from constants import EntitiesNames, InitValues, Messages


class Explosion(Entity):
    STATE = [1, 2]
    STATE_INTERVAL = int(0.5/InitValues.TICKS)

    def __init__(self, position, mailbox, user, direction):
        self.user = user
        Entity.__init__(self, position, mailbox)
        self.direction = direction
        self.entities_to_kill = set()
        # Start detonation
        self.mailbox.send(self, {Messages.ITER_STATE: self.STATE_INTERVAL})

    def get_name(self):
        return f'{EntitiesNames.EXPLOSION}'

    async def update(self):
        await Entity.update(self)
        self.state_update()

        if Messages.TO_KILL in self.message_queue:
            self.entities_to_kill.update(set(self.message_queue.pop(Messages.TO_KILL)))

        if self.message_queue:
            raise f'message_queue should be empty {self.message_queue}'

    def get_state(self):
        return {'explosion_state': self.state, 'direction': self.direction,
                **Entity.get_state(self)}

    def kill(self):
        Entity.kill(self)
        for entity in self.entities_to_kill:
            self.mailbox.send(entity, {Messages.KILLED: self.user})
