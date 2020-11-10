class Position:
    
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    @property
    def position(self):
        """Get position tuple
        Returns:
            tuple: (x, y)
        """
        return (self.x, self.y)

    def __str__(self) -> str:
        return f"<{self.x}, {self.y}>"

    def __eq__(self, other):
        return self.y == other.y and self.x == other.x

    def __hash__(self):
        return hash((self.x, self.y))
