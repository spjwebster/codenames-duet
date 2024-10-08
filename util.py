from dataclasses import dataclass
from random import randrange

def mm_to_px(mm, dpi=92):
    return round((dpi * mm) / 25.4)

def centred_pos(mid:int, col:int, cols:int, width:int, spacing:int) -> int:
    """ 
    Returns X position for COL in page of COLS columns of given WIDTH plus SPACING, centred 
    around the given MID point
    """
    offset = mid - round(((cols * width) + ((cols - 1) * spacing)) / 2)
    return offset + col * (width + spacing)


def choose(arr:list, count:int) -> tuple[list, list]:
    remaining = list(arr)
    extracted = list()
    for _ in range(0, count):
        index = randrange(0, len(remaining))
        extracted.append(remaining.pop(index))
    
    return extracted, remaining

def chunk(arr:list, count:int):
    for i in range(0, len(arr), count):
        yield arr[i:i+count]

@dataclass
class Coord:
    x:int
    y:int

    @classmethod
    def from_dict(cls, d:dict) -> 'Coord':
        return cls(d['x'], d['y'])

    def translate(self, dx:int, dy:int):
        self.x += dx
        self.y += dy

    def translated(self, dx:int, dy:int) -> 'Coord':
        return Coord(self.x + dx, self.y + dy)


@dataclass
class Dimensions:
    w:int
    h:int

    @classmethod
    def from_dict(cls, d:dict, default=None) -> 'Dimensions':
        return cls(d['w'],d['h'])
