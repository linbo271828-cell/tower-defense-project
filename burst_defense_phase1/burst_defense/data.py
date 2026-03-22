"""Static game data.

Phase 1 uses plain Python data structures instead of JSON so the project stays
self-contained and easy to run in class. Once the core loop is stable, these
values can move into JSON files without changing the gameplay architecture much.
"""

from __future__ import annotations

# One handcrafted map is enough for the first vertical slice. The path is kept
# as a list of waypoints, which is a simple and readable starting point.
MAP_WAYPOINTS = [
    (40, 170),
    (250, 170),
    (250, 520),
    (540, 520),
    (540, 250),
    (840, 250),
    (840, 610),
    (980, 610),
]


ENEMY_DEFINITIONS = {
    "red": {
        "display_name": "Red Balloon",
        "max_health": 1,
        "speed": 105.0,
        "reward": 12,
        "leak_damage": 1,
        "color": (231, 76, 60),
    },
    "blue": {
        "display_name": "Blue Balloon",
        "max_health": 2,
        "speed": 120.0,
        "reward": 18,
        "leak_damage": 1,
        "color": (52, 152, 219),
    },
    "green": {
        "display_name": "Green Balloon",
        "max_health": 3,
        "speed": 140.0,
        "reward": 25,
        "leak_damage": 2,
        "color": (46, 204, 113),
    },
}


TOWER_DEFINITIONS = {
    "dart": {
        "display_name": "Dart Tower",
        "cost": 100,
        "range_radius": 165.0,
        "fire_rate": 1.2,
        "damage": 1,
        "projectile_speed": 420.0,
    }
}


# The wave format is intentionally human-readable. It is a list of spawn groups,
# and each group spawns one enemy type repeatedly at a fixed interval.
WAVE_DEFINITIONS = [
    [
        {"enemy_type": "red", "count": 8, "spawn_interval": 0.75},
    ],
    [
        {"enemy_type": "red", "count": 6, "spawn_interval": 0.6},
        {"enemy_type": "blue", "count": 4, "spawn_interval": 0.8},
    ],
    [
        {"enemy_type": "blue", "count": 8, "spawn_interval": 0.55},
        {"enemy_type": "green", "count": 5, "spawn_interval": 0.9},
    ],
]
