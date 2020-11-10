class Moves:
    RIGHT = "right"
    LEFT = "left"
    DOWN = "down"
    UP = "up"
    ALL = {RIGHT, LEFT, DOWN, UP}


class InitValues:
    LENGTH = 10
    WIDTH = 10
    WALLS = 20
    MAX_USERS = 4
    TICKS = 0.02


class Messages:
    # Position
    POSITION = "position"
    # Boolean
    BLOCKED = "blocked"
    # Position
    BOMB_DROPPED = "bomb_dropped"
    # User
    KILLED = "killed"
    # Color
    COLOR = "color"
    # Entity init args tuple
    RESET = "reset"
    # int
    ITER_STATE = "iter_state"
    # int
    BOMB_CD = "bomb_cd"
    # Bomb
    BOOM = "boom"
    # Move
    MOVE = "move"
    # Position
    BOMB = "bomb"
    # Entity
    TO_KILL = "to_kill"


class EntitiesNames:
    ENTITY = "entity"
    USER = "user"
    EXPLOSION = "explosion"
    WALL = "wall"
    BOMB = "bomb"
    BOARD = "board"
    LOG = "log"


class Directions:
    VERTICAL = "v"
    HORIZONTAL = "h"
    ALL = "f"
