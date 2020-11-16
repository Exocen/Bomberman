import logging


class MailBox:
    def __init__(self):
        # {entity: {message_key: value}}
        # {entity: {message_key: []}
        self.inbox = {}
        self.outbox = {}

    def drop(self):
        if self.outbox:
            logging.error(f"Outbox should be empty: {self.outbox}")
            self.outbox = {}
        self.inbox, self.outbox = self.outbox, self.inbox

    def send(self, entity, message):
        if entity not in self.inbox:
            self.inbox[entity] = {}
        self.inbox[entity].update(message)

    def send_to_list(self, entity, key, value):
        if entity not in self.inbox:
            self.inbox[entity] = {key: []}
        elif key not in self.inbox[entity]:
            self.inbox[entity][key] = []
        self.inbox[entity][key] += [value]

    def drop_key(self, key):
        if not self.inbox or key not in self.inbox:
            return
        if self.outbox:
            logging.error(f"Outbox should be empty: {self.outbox}")
        self.outbox[key] = self.inbox.pop(key)

    def get(self, entity):
        return self.outbox.pop(entity, {})
