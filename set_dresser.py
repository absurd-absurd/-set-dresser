"""Set dresser engine: scatters rocks and trees on a ground plane.

No UI in here. The window (set_dresser_ui.py) reads its controls and calls
scatter() / clear().
"""

import math
import random

import maya.cmds as cmds

# --- the set -----------------------------------------------------------------
GROUND_SIZE = 40.0          # ground is GROUND_SIZE x GROUND_SIZE, centred on origin
PATH_WIDTH = 4.0            # path runs along Z through x = 0
POND_X, POND_Z = 10.0, 10.0
POND_RADIUS = 6.0

# How much room each kind needs (footprint radius, before random scale).
ROCK_RADIUS = 0.6
TREE_RADIUS = 1.4

LAYOUT_GROUP = "layout"     # ground, path, pond: built once, Clear never touches it
ROCK_GROUP = "rocks"
TREE_GROUP = "trees"

MAX_TRIES_PER_ITEM = 200


# --- things it makes ---------------------------------------------------------
def make_ground():
    """The 40x40 ground plane."""
    ground = cmds.polyPlane(name="ground", width=GROUND_SIZE, height=GROUND_SIZE,
                            subdivisionsX=1, subdivisionsY=1)[0]
    return ground


def make_path():
    """A 4-wide strip along Z through the middle, sitting just above the ground."""
    path = cmds.polyPlane(name="path", width=PATH_WIDTH, height=GROUND_SIZE,
                          subdivisionsX=1, subdivisionsY=1)[0]
    cmds.move(0, 0.01, 0, path)
    return path


def make_pond():
    """A flat disc of radius 6 at x=10, z=10."""
    pond = cmds.polyCylinder(name="pond", radius=POND_RADIUS, height=0.04,
                             subdivisionsAxis=32)[0]
    cmds.move(POND_X, 0.02, POND_Z, pond)
    return pond


def make_rock(x, z):
    """One rock: a squashed, randomly sized and turned sphere sitting on the ground."""
    size = random.uniform(0.6, 1.0)
    rock = cmds.polySphere(name="rock", radius=ROCK_RADIUS, subdivisionsX=8,
                           subdivisionsY=6)[0]
    cmds.scale(size * random.uniform(0.9, 1.2), size * random.uniform(0.4, 0.7),
               size * random.uniform(0.9, 1.2), rock)
    cmds.rotate(0, random.uniform(0, 360), 0, rock)
    cmds.move(x, 0, z, rock)
    return rock


def make_tree(x, z):
    """One tree: a group named tree holding a trunk and a canopy."""
    height = random.uniform(2.0, 3.0)
    trunk = cmds.polyCylinder(name="trunk", radius=0.2, height=height)[0]
    cmds.move(0, height / 2.0, 0, trunk)
    canopy_height = random.uniform(2.5, 3.5)
    canopy = cmds.polyCone(name="canopy", radius=TREE_RADIUS, height=canopy_height)[0]
    cmds.move(0, height + canopy_height / 2.0, 0, canopy)
    tree = cmds.group(trunk, canopy, name="tree")
    cmds.xform(tree, pivots=(0, 0, 0), worldSpace=True)
    cmds.rotate(0, random.uniform(0, 360), 0, tree)
    cmds.move(x, 0, z, tree)
    return tree


# --- the rule ----------------------------------------------------------------
def is_clear(x, z, radius, keep_clear, placed):
    """True if something of this radius can stand at (x, z).

    It must sit fully on the ground, not overlap anything already placed,
    and, when keep_clear is on, stay off the path and out of the pond.
    placed is a list of (x, z, radius) for things already put down.
    """
    half = GROUND_SIZE / 2.0
    if abs(x) + radius > half or abs(z) + radius > half:
        return False
    if keep_clear:
        if abs(x) < PATH_WIDTH / 2.0 + radius:
            return False
        if math.hypot(x - POND_X, z - POND_Z) < POND_RADIUS + radius:
            return False
    for px, pz, pr in placed:
        if math.hypot(x - px, z - pz) < radius + pr:
            return False
    return True


# --- the engine --------------------------------------------------------------
def _ensure_layout():
    """Build ground, path and pond under 'layout' if they aren't there yet."""
    if cmds.objExists(LAYOUT_GROUP):
        return
    parts = [make_ground(), make_path(), make_pond()]
    cmds.group(parts, name=LAYOUT_GROUP)


def _place(count, radius, area, keep_clear, placed, maker, group):
    """Put down up to count things with maker; return how many fit."""
    half = min(area, GROUND_SIZE) / 2.0
    made = 0
    for _ in range(count):
        for _try in range(MAX_TRIES_PER_ITEM):
            x = random.uniform(-half, half)
            z = random.uniform(-half, half)
            if is_clear(x, z, radius, keep_clear, placed):
                cmds.parent(maker(x, z), group)
                placed.append((x, z, radius))
                made += 1
                break
    return made


def scatter(rocks=20, trees=10, area=GROUND_SIZE, keep_clear=True, seed=None):
    """Replace the current scatter with a new one. One call = one undo step.

    Returns (rocks_made, trees_made).
    """
    try:
        rocks, trees, area = int(rocks), int(trees), float(area)
    except (TypeError, ValueError):
        cmds.warning("Rock count, tree count and area must be numbers.")
        return 0, 0
    if rocks < 0 or trees < 0 or area <= 0:
        cmds.warning("Counts can't be negative and the area must be bigger than zero.")
        return 0, 0

    if seed is not None:
        random.seed(seed)

    cmds.undoInfo(openChunk=True, chunkName="Set dresser scatter")
    try:
        _ensure_layout()
        clear()
        rock_group = cmds.group(empty=True, name=ROCK_GROUP)
        tree_group = cmds.group(empty=True, name=TREE_GROUP)
        placed = []
        # Trees first: they're bigger, so they get first pick of the space.
        trees_made = _place(trees, TREE_RADIUS, area, keep_clear, placed,
                            make_tree, tree_group)
        rocks_made = _place(rocks, ROCK_RADIUS, area, keep_clear, placed,
                            make_rock, rock_group)
        cmds.select(clear=True)
    finally:
        cmds.undoInfo(closeChunk=True)

    short = ["%d of %d %s" % (made, asked, kind)
             for made, asked, kind in ((trees_made, trees, "trees"), (rocks_made, rocks, "rocks"))
             if made < asked]
    if short:
        cmds.warning("Only %s fit, so try a bigger area or fewer of them."
                     % " and ".join(short))
    return rocks_made, trees_made


def clear():
    """Delete the rocks and trees groups, and nothing else."""
    for group in ("|" + ROCK_GROUP, "|" + TREE_GROUP):
        if cmds.objExists(group):
            cmds.delete(group)
