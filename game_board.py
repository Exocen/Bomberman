import asyncio
import json
import logging
import random
from uuid import uuid1

import websockets

from bomb import Bomb
from constants import Moves, InitValues, Messages, EntitiesNames, Directions
from entity import Entity
from explosion import Explosion
from mailbox import MailBox
from position import Position
from user import User
from wall import Wall


def _make_moves():
    return {
        Moves.RIGHT: lambda pos: (Position(pos.x + 1, pos.y) if pos.x + 1 < InitValues.LENGTH else Position(0, pos.y)),
        Moves.LEFT: lambda pos: (
            Position(pos.x - 1, pos.y) if pos.x - 1 >= 0 else Position(InitValues.LENGTH - 1, pos.y)),
        Moves.DOWN: lambda pos: (Position(pos.x, pos.y + 1) if pos.y + 1 < InitValues.WIDTH else Position(pos.x, 0)),
        Moves.UP: lambda pos: (Position(pos.x, pos.y - 1) if pos.y - 1 >= 0 else Position(pos.x, InitValues.WIDTH - 1))}


class GameBoard:
    def __init__(self):
        self.mailbox = MailBox()
        self.explosions_lock = asyncio.Lock()
        self.users_lock = asyncio.Lock()
        self.walls_lock = asyncio.Lock()
        self.bombs_lock = asyncio.Lock()
        self.explosions = set()
        self.users = set()
        self.walls = set()
        self.bombs = set()
        self.mods = {mod: 0 for mod in range(1, 5)}
        self.game_map = self.create_map()
        self.make_walls()
        self.dict_moves = _make_moves()

    def get_entities(self):
        return [self.users, self.walls, self.bombs, self.explosions]

    def get_destructible_entities(self):
        killable_entities_by_pos = {}
        for entities in self.get_entities():
            if entities and next(iter(entities)).DESTRUCTIBLE:
                killable_entities_by_pos.update({e.get_position(): e for e in entities})
        return killable_entities_by_pos

    def create_map(self):
        game_map = dict()
        for line in range(InitValues.LENGTH):
            for col in range(InitValues.WIDTH):
                game_map[Position(line, col)] = dict()

        for entities in self.get_entities():
            for entity in entities:
                game_map[entity.get_position()][entity] = entity.get_state()

        return game_map

    def create_server(self, ip, port):
        return websockets.serve(self.game, ip, port)

    def get_next_mod(self):
        mod = min(self.mods, key=self.mods.get)
        self.mods[mod] += 1
        return mod

    def get_init_state(self, user_id):
        """Get init state"""
        state = {"length": InitValues.LENGTH, "width": InitValues.WIDTH, "id": user_id}

        # Get all map for init
        message = dict()
        for entities in self.get_entities():
            for entity in entities:
                if entity.get_name() in message:
                    message[entity.get_name()].append(entity.get_state())
                else:
                    message[entity.get_name()] = [entity.get_state()]

        if message:
            state.update(message)

        return json.dumps({"type": "init", **state})

    def create_message(self):
        """Create message to notify users about map update

        Returns:
            dict : {{"type": "map"}{ updated : entities }} OR None
        """
        message = dict()
        new_game_map = self.create_map()
        updated_entities = []

        for position in new_game_map:
            if self.game_map[position] != new_game_map[position]:
                if new_game_map[position]:
                    updated_entities.extend([e for e in new_game_map[position]])
                else:
                    updated_entities.append(Entity(position, self.mailbox))

        for entity in updated_entities:
            if entity.get_name() in message:
                message[entity.get_name()].append(entity.get_state())
            else:
                message[entity.get_name()] = [entity.get_state()]

        if message:
            message.update({"type": "map"})

        self.game_map = new_game_map
        return json.dumps(message)

    async def notify(self, message):
        """
        Notify all users about game updates
        """
        try:
            # await user.ws.send(map_message)
            # Todo player FOV
            await asyncio.gather(*[user.ws.send(message) for user in self.users])
        except websockets.exceptions.ConnectionClosed:
            logging.debug("Connection lost")
        except Exception:
            logging.exception("Connection lost for unexpected reasons :")
            raise

    async def register(self, user):
        async with self.users_lock:
            self.users.add(user)
            logging.info(f"{user} user connected")
        self.mailbox.send_to_list(EntitiesNames.LOG, user.mod, "connected")

    async def unregister(self, user):
        async with self.users_lock:
            self.mods[user.mod] -= 1
            logging.info(f"{user} user disconnected")
            self.users.remove(user)
            if not self.users:
                logging.info("No more users, starting sleep mode")
                self.make_walls()
        self.mailbox.send_to_list(EntitiesNames.LOG, user.mod, "disconnected")

    async def put_bomb(self, user):
        if not user.is_user_can_drop_bomb():
            return
        self.mailbox.send(user, {Messages.BOMB_DROPPED: True})
        async with self.bombs_lock:
            self.bombs.add(Bomb(user.get_position(), self.mailbox, user))

    async def boom(self, bomb):
        bomb.exploded = True
        x, y = bomb.get_pos_tuple()
        killable_entities_by_pos = self.get_destructible_entities()
        explosion_list = [Explosion(bomb.get_position(), self.mailbox, bomb.user, Directions.ALL)]

        def explosion_propagation(exp_range, direction):
            for new in exp_range:
                if direction == Directions.VERTICAL:
                    new_pos = Position(new, y)
                elif direction == Directions.HORIZONTAL:
                    new_pos = Position(x, new)
                else:
                    new_pos = Position(x, y)
                if new_pos not in killable_entities_by_pos:
                    explosion_list.append(Explosion(new_pos, self.mailbox, bomb.user, direction))
                else:
                    self.mailbox.send_to_list(explosion_list[-1], Messages.TO_KILL, killable_entities_by_pos[new_pos])
                    self.mailbox.send(killable_entities_by_pos[new_pos], {Messages.BLOCKED: True})
                    break

        explosion_propagation(range(1), Directions.ALL)
        explosion_propagation(range((x - 1), -1, -1), Directions.VERTICAL)
        explosion_propagation(range((x + 1), InitValues.LENGTH), Directions.VERTICAL)
        explosion_propagation(range((y - 1), -1, -1), Directions.HORIZONTAL)
        explosion_propagation(range((y + 1), InitValues.WIDTH), Directions.HORIZONTAL)

        async with self.explosions_lock:
            self.explosions.update(set(explosion_list))

    def find_and_bomb_users(self):
        explosions_positions = {e.get_position(): e for e in self.explosions}
        for user in self.users:
            if user.get_position() in explosions_positions:
                self.mailbox.send_to_list(explosions_positions[user.get_position()], Messages.TO_KILL, user)
                self.mailbox.send(user, {Messages.BLOCKED: True})

    def kill_and_respawn(self, user):
        self.mailbox.send(user, {Messages.RESET: (self.random_spawn()[0])})

    def make_walls(self):
        self.walls = set()
        wall_positions = set(self.random_spawn(InitValues.WALLS))
        for wall_position in wall_positions:
            self.walls.add(Wall(wall_position, self.mailbox))

    def is_position_free(self, position):
        """Check if position doesn't contain a blockable entity"""
        for entities in self.get_entities():
            if entities and next(iter(entities)).BLOCKABLE:
                for entity in entities:
                    if entity.get_position() == position:
                        return False
        return True

    async def move_user(self, user, move):
        if user.blocked:
            return

        new_position = self.dict_moves[move](user.get_position())

        if self.is_position_free(new_position):
            self.mailbox.send(user, {Messages.POSITION: new_position})

        explosions_positions = {e.get_position(): e for e in self.explosions}
        if new_position in explosions_positions:
            self.mailbox.send_to_list(explosions_positions[new_position], Messages.TO_KILL, user)
            self.mailbox.send(user, {Messages.BLOCKED: True})

    @staticmethod
    def is_position_valid(position):
        if position.x < 0 or position.x >= InitValues.LENGTH:
            return False
        elif position.y < 0 or position.y >= InitValues.WIDTH:
            return False
        return True

    def find_path(self, origin, destination, max_iter=None):
        class Node:
            def __init__(self, dest, parent=None, position=None):
                self.parent = parent
                self.position = position
                self.g = parent.g + 1 if parent else 0
                self.h = pow(self.position.x - dest.x, 2) + pow(self.position.y - dest.y, 2)

            @property
            def f(self):
                return self.g + self.h

            def __eq__(self, other):
                return self.position == other.position

            def get_ancestors(self, ancestors=None):
                if ancestors is None:
                    ancestors = []
                if self.parent is not None:
                    ancestors.append(self)
                    return self.parent.get_ancestors(ancestors)
                ancestors = ancestors[::-1]
                return [an.position for an in ancestors]

        node_list = []
        first_node = Node(destination, position=origin)
        tmp_node_list = [first_node]
        max_iter = max_iter if max_iter else InitValues.MAX_PATH_ITER

        while len(tmp_node_list) > 0 and max_iter > 0:
            max_iter -= 1
            node = min(tmp_node_list, key=(lambda k: k.f))
            tmp_node_list.remove(node)
            node_list.append(node)
            if node.position == destination:
                return node.get_ancestors()

            adjacent_nodes = []
            n_pos = node.position
            # available movements:
            for new_p in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                new_node_pos = Position(n_pos.x + new_p[0], n_pos.y + new_p[1])
                if self.is_position_valid(new_node_pos) and self.is_position_free(new_node_pos):
                    adjacent_nodes.append(Node(destination, node, new_node_pos))

            for n in adjacent_nodes:
                if n not in node_list and (n not in tmp_node_list or node.g > n.g):
                    tmp_node_list.append(n)

        return (min(node_list, key=(lambda k: k.h))).get_ancestors()

    def random_spawn(self, nb=1):
        """Return nb available positions

        Args:
            nb (int, optional): nb positions. Defaults to 1.

        Returns:
            [Position]: positions list
        """
        # todo need better complexity (only if procedural maps)
        x_choices = range(InitValues.LENGTH)
        y_choices = range(InitValues.WIDTH)

        pos_choices = set()
        for x in x_choices:
            for y in y_choices:
                pos_choices.add(Position(x, y))

        blocked_positions = set()

        for entities in self.get_entities():
            for entity in entities:
                blocked_positions.add(entity.get_position())

        new_pos = pos_choices - blocked_positions

        return random.choices(list(new_pos), k=nb)

    async def game_loop(self):
        """
        Update and clean all entities and notify users
        """
        while True:
            await asyncio.sleep(InitValues.TICKS)
            if self.users:

                # Board update DO NOT send messages to board before mailbox.drop()
                self.mailbox.drop_key(EntitiesNames.BOARD)
                message_queue = self.mailbox.get(EntitiesNames.BOARD)
                if message_queue:
                    tasks = []
                    if Messages.BOOM in message_queue:
                        boom_pos_list = message_queue.pop(Messages.BOOM)
                        tasks += [self.boom(pos) for pos in boom_pos_list]
                    if Messages.MOVE in message_queue:
                        move_mess = message_queue.pop(Messages.MOVE)
                        tasks += [self.move_user(m[0], m[1]) for m in move_mess]
                    if Messages.BOMB in message_queue:
                        bomb_mess = message_queue.pop(Messages.BOMB)
                        tasks += [self.put_bomb(u) for u in bomb_mess]
                    if tasks:
                        await asyncio.gather(*tasks)

                self.mailbox.drop()

                # All entities async update
                entities_task_update = []
                for entities in self.get_entities():
                    for entity in entities:
                        entities_task_update.append(entity.update())
                await asyncio.gather(*entities_task_update)

                message = self.create_message()
                if message:
                    await self.notify(message)
                await self.clean_entities()
                await self.send_logs()
                # Mailbox -> outbox should be empty
            else:
                # Waiting users while resting
                await asyncio.sleep(1)

    async def send_logs(self):
        logs = self.mailbox.get(EntitiesNames.LOG)

        if not logs:
            return

        message = {"type": "log"}
        log_list = []
        for (k, v) in logs.items():
            for log in v:
                log_list.append({k: log})

        message.update({"logs": log_list})
        map_message = json.dumps(message)
        logging.debug(message)
        await self.notify(map_message)

    @staticmethod
    async def clean_entity_list(entity_set, lock):
        """Remove dead entities

        Args:
            entity_set (set): entity list to clean
            lock (async lock): entity lock
        """
        async with lock:
            entity_set -= {e for e in entity_set if e.is_dead()}

    async def clean_entities(self):
        async with self.users_lock:
            users_to_kill = {u for u in self.users if u.is_dead()}
            if users_to_kill:
                for user in users_to_kill:
                    self.kill_and_respawn(user)

        await asyncio.gather(
            self.clean_entity_list(self.bombs, self.bombs_lock),
            self.clean_entity_list(self.walls, self.walls_lock),
            self.clean_entity_list(self.explosions, self.explosions_lock),
        )

    async def game(self, websocket, _):
        if len(self.users) >= InitValues.MAX_USERS:
            return

        user = User(
            websocket,
            self.random_spawn()[0],
            self.mailbox,
            self.get_next_mod(),
            str(uuid1()),
        )

        await self.register(user)

        try:
            await websocket.send(self.get_init_state(user.id))
            async for message in websocket:
                data = json.loads(message)
                logging.debug(f"received: {data}")
                if "action" in data:
                    if data["action"] in Moves.ALL:
                        self.mailbox.send_to_list(
                            EntitiesNames.BOARD, Messages.MOVE, [user, data["action"]]
                        )
                    elif data["action"] == "bomb":
                        # await self.put_bomb(user)
                        self.mailbox.send_to_list(
                            EntitiesNames.BOARD, Messages.BOMB, user
                        )
                    else:
                        logging.error(f"Unsupported data {data}")
                elif "chat" in data:
                    self.mailbox.send_to_list(EntitiesNames.LOG, user.mod, data["chat"])
                else:
                    logging.error(f"Unsupported event {message}")
        except websockets.exceptions.ConnectionClosed:
            logging.debug("Connection lost")
        except Exception:
            logging.exception("Unexpected error")
            raise
        finally:
            await self.unregister(user)
