"""Position utilities and geometric types for the pets module."""


def parse_position(position):
    x, y = position.split(",")
    return {"x": int(x), "y": int(y)}


def position_tuple(pos):
    return (pos["x"], pos["y"])


def offset_position(position, delta):
    return {"x": position["x"] + delta["x"], "y": position["y"] + delta["y"]}


def is_adjacent(p1, p2):
    return abs(p2["x"] - p1["x"]) <= 1 and abs(p2["y"] - p1["y"]) <= 1


class Region:
    def __init__(self, top_left, bottom_right):
        self.top_left = top_left
        self.bottom_right = bottom_right

    def __contains__(self, point):
        return (
            self.top_left["x"] <= point["x"] <= self.bottom_right["x"]
            and self.top_left["y"] <= point["y"] <= self.bottom_right["y"]
        )

    def random_point(self):
        import random

        return {
            "x": random.randint(self.top_left["x"], self.bottom_right["x"]),
            "y": random.randint(self.top_left["y"], self.bottom_right["y"]),
        }

    def __repr__(self):
        return f"<Region {self.top_left!r} {self.bottom_right!r}>"


DELTAS = [{"x": x, "y": y} for x in [-1, 0, 1] for y in [-1, 0, 1] if x != 0 or y != 0]
