
from enum import Enum
from random import randrange

from util import choose

class TileType(Enum):
    BYSTANDER = ' '
    ASSASSIN = 'x'
    AGENT = '*'

def generate_word_grids() -> tuple[list[int], list[int]]:
    """
    Generate a matching pair of 5x5 word index grids

    NOTE: Generated grids are BOTH from person A's perspective as this makes
    validating the grid pair easier. Use `reverse_grid` on B before printing / 
    displaying.
    """
    words = list(range(0, 25))

    # Pick 5 common agent words, and 1 common assassin word
    (agent_common, remaining) = choose(words, 3)
    (assassin_common, remaining) = choose(remaining, 1)

    # Pick 5 exclusively agent words per side
    (agent_excl_a, remaining) = choose(remaining, 5)
    (agent_excl_b, remaining) = choose(remaining, 5)

    # Pick 2 exclusively assassin words per side
    (assassin_excl_a, remaining) = choose(remaining, 2)
    (assassin_excl_b, remaining) = choose(remaining, 2)

    # pick an assassin word from the opposite side to be an agent
    (agent_opp_a, _) = choose(assassin_excl_b, 1)
    (agent_opp_b, _) = choose(assassin_excl_a, 1)

    # Combine pieces to get first grid
    agent_a = agent_opp_a + agent_excl_a + agent_common
    assassin_a = assassin_excl_a + assassin_common
    a = create_grid(agent_a, assassin_a)

    # Combine pieces to get second grid
    agent_b = agent_opp_b + agent_excl_b + agent_common
    assassin_b = assassin_excl_b + assassin_common
    b = create_grid(agent_b, assassin_b)

    return a, b

def create_grid(agents:list[int], assassins:list[int]) -> list[str]:
    """ Convert a list of agent and assassin tile indexes to enumerated 5x5 grid"""
    grid = [TileType.BYSTANDER for _ in range(0, 25)]

    for index in agents:
        grid[index] = TileType.AGENT

    for index in assassins:
        grid[index] = TileType.ASSASSIN

    return grid

def reverse_grid(grid:list[int]) -> list[int]:
    return list(reversed(grid))

def check_grid(grid:list[str], other:list[str]):
    # There should be 9 total agent tiles
    assert(len([v for v in grid if v == TileType.AGENT]) == 9)

    # ...and 3 total assassin tiles
    assert(len([v for v in grid if v == TileType.ASSASSIN]) == 3)

    # ...with 1 assassin tile having a matching assassin in other
    assert(len([v for i, v in enumerate(grid) if v == TileType.ASSASSIN == other[i]]) == 1)

    # ...and 1 assassin tile matching an agent in other
    assert(len([v for i, v in enumerate(grid) if v == TileType.ASSASSIN and other[i] == TileType.AGENT]) == 1)

    # ...and 5 agent tiles matching bystanders in other
    assert(len([v for i, v in enumerate(grid) if v == TileType.AGENT and other[i] == TileType.BYSTANDER]) == 5)

def check_grids(a:list[str], b:list[str]):
    # Check A with respect to B
    check_grid(a, b)
    # Check B with respect to A
    check_grid(b, a)