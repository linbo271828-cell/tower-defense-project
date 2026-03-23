"""Static game data.

Phase 1 uses plain Python data structures instead of JSON so the project stays
self-contained and easy to run in class. Once the core loop is stable, these
values can move into JSON files without changing the gameplay architecture much.

Phase 2 expands the data with multiple tower types, layered/splitting enemies,
status effects on towers, and more waves.
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
        "children": None,
        "traits": [],
        "shield_hp": 0,
        "regen_rate": 0.0,
    },
    "blue": {
        "display_name": "Blue Balloon",
        "max_health": 2,
        "speed": 120.0,
        "reward": 14,
        "leak_damage": 1,
        "color": (52, 152, 219),
        "children": [{"type": "red", "count": 1}],
        "traits": [],
        "shield_hp": 0,
        "regen_rate": 0.0,
    },
    "green": {
        "display_name": "Green Balloon",
        "max_health": 3,
        "speed": 140.0,
        "reward": 18,
        "leak_damage": 2,
        "color": (46, 204, 113),
        "children": [{"type": "blue", "count": 1}],
        "traits": ["fast"],
        "shield_hp": 0,
        "regen_rate": 0.0,
    },
    "yellow": {
        "display_name": "Yellow Balloon",
        "max_health": 4,
        "speed": 95.0,
        "reward": 22,
        "leak_damage": 2,
        "color": (241, 196, 15),
        "children": [{"type": "green", "count": 2}],
        "traits": [],
        "shield_hp": 0,
        "regen_rate": 0.0,
    },
    "pink": {
        "display_name": "Pink Balloon",
        "max_health": 2,
        "speed": 170.0,
        "reward": 16,
        "leak_damage": 1,
        "color": (240, 120, 180),
        "children": [{"type": "green", "count": 1}],
        "traits": ["fast"],
        "shield_hp": 0,
        "regen_rate": 0.0,
    },
    "camo": {
        "display_name": "Camo Balloon",
        "max_health": 3,
        "speed": 115.0,
        "reward": 20,
        "leak_damage": 2,
        "color": (70, 100, 70),
        "children": [{"type": "blue", "count": 1}],
        "traits": ["camo"],
        "shield_hp": 0,
        "regen_rate": 0.0,
    },
    "regen": {
        "display_name": "Regen Balloon",
        "max_health": 6,
        "speed": 90.0,
        "reward": 28,
        "leak_damage": 2,
        "color": (80, 220, 120),
        "children": [{"type": "yellow", "count": 1}],
        "traits": ["regen"],
        "shield_hp": 0,
        "regen_rate": 1.5,
    },
    "armored": {
        "display_name": "Armored Balloon",
        "max_health": 10,
        "speed": 60.0,
        "reward": 35,
        "leak_damage": 3,
        "color": (140, 140, 155),
        "children": [{"type": "yellow", "count": 2}],
        "traits": ["armored"],
        "shield_hp": 0,
        "regen_rate": 0.0,
        "resistances": {"sharp": 0.5},
    },
    "shield": {
        "display_name": "Shield Balloon",
        "max_health": 5,
        "speed": 85.0,
        "reward": 30,
        "leak_damage": 3,
        "color": (100, 160, 240),
        "children": [{"type": "yellow", "count": 2}],
        "traits": ["shielded"],
        "shield_hp": 6,
        "regen_rate": 0.0,
    },
    "boss": {
        "display_name": "B.A.D. Blimp",
        "max_health": 60,
        "speed": 35.0,
        "reward": 100,
        "leak_damage": 15,
        "color": (180, 40, 40),
        "children": [{"type": "armored", "count": 2}, {"type": "shield", "count": 2}],
        "traits": ["boss", "armored"],
        "shield_hp": 15,
        "regen_rate": 0.5,
        "resistances": {"sharp": 0.6},
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
        "color": (241, 196, 15),
        "attack_type": "single",
        "damage_type": "sharp",
        "pierce": 1,
        "splash_radius": 0,
        "status_on_hit": None,
        "can_see_camo": False,
        "description": "Fast basic shooter",
    },
    "bomb": {
        "display_name": "Bomb Tower",
        "cost": 250,
        "range_radius": 120.0,
        "fire_rate": 0.5,
        "damage": 4,
        "projectile_speed": 280.0,
        "color": (220, 130, 60),
        "attack_type": "splash",
        "damage_type": "explosive",
        "pierce": 0,
        "splash_radius": 55,
        "status_on_hit": None,
        "can_see_camo": False,
        "description": "Slow area damage",
    },
    "frost": {
        "display_name": "Frost Tower",
        "cost": 175,
        "range_radius": 130.0,
        "fire_rate": 0.8,
        "damage": 1,
        "projectile_speed": 360.0,
        "color": (100, 200, 240),
        "attack_type": "single",
        "damage_type": "frost",
        "pierce": 1,
        "splash_radius": 0,
        "status_on_hit": {"type": "slow", "duration": 2.0, "magnitude": 0.4},
        "can_see_camo": False,
        "description": "Slows enemies on hit",
    },
    "sniper": {
        "display_name": "Sniper Tower",
        "cost": 350,
        "range_radius": float("inf"),
        "fire_rate": 0.3,
        "damage": 8,
        "projectile_speed": 900.0,
        "color": (80, 100, 140),
        "attack_type": "single",
        "damage_type": "sharp",
        "pierce": 1,
        "splash_radius": 0,
        "status_on_hit": None,
        "can_see_camo": True,
        "description": "Infinite range, sees camo",
    },
    "pierce": {
        "display_name": "Pierce Tower",
        "cost": 200,
        "range_radius": 150.0,
        "fire_rate": 1.0,
        "damage": 1,
        "projectile_speed": 500.0,
        "color": (180, 160, 100),
        "attack_type": "single",
        "damage_type": "sharp",
        "pierce": 4,
        "splash_radius": 0,
        "status_on_hit": None,
        "can_see_camo": False,
        "description": "Hits 4 enemies per shot",
    },
    "support": {
        "display_name": "Support Tower",
        "cost": 300,
        "range_radius": 130.0,
        "fire_rate": 0,
        "damage": 0,
        "projectile_speed": 0,
        "color": (200, 180, 240),
        "attack_type": "support",
        "damage_type": "none",
        "pierce": 0,
        "splash_radius": 0,
        "status_on_hit": None,
        "can_see_camo": False,
        "description": "Buffs nearby towers +25% speed",
        "aura": {"attack_speed_bonus": 0.25, "range_bonus": 10},
    },
}

# Ordered list of tower keys for the shop UI and hotkeys
TOWER_ORDER = ["dart", "bomb", "frost", "sniper", "pierce", "support"]


# The wave format is intentionally human-readable. It is a list of spawn groups,
# and each group spawns one enemy type repeatedly at a fixed interval.
WAVE_DEFINITIONS = [
    # Wave 1: gentle intro
    [
        {"enemy_type": "red", "count": 8, "spawn_interval": 0.75},
    ],
    # Wave 2: introduce blue (layered)
    [
        {"enemy_type": "red", "count": 6, "spawn_interval": 0.6},
        {"enemy_type": "blue", "count": 4, "spawn_interval": 0.8},
    ],
    # Wave 3: more blues, introduce green
    [
        {"enemy_type": "blue", "count": 8, "spawn_interval": 0.55},
        {"enemy_type": "green", "count": 5, "spawn_interval": 0.9},
    ],
    # Wave 4: fast pink rush
    [
        {"enemy_type": "green", "count": 6, "spawn_interval": 0.45},
        {"enemy_type": "pink", "count": 8, "spawn_interval": 0.35},
    ],
    # Wave 5: yellows (deeper layer chain)
    [
        {"enemy_type": "yellow", "count": 5, "spawn_interval": 1.2},
        {"enemy_type": "green", "count": 10, "spawn_interval": 0.3},
    ],
    # Wave 6: camo introduction
    [
        {"enemy_type": "camo", "count": 6, "spawn_interval": 0.7},
        {"enemy_type": "blue", "count": 12, "spawn_interval": 0.3},
    ],
    # Wave 7: regen enemies
    [
        {"enemy_type": "regen", "count": 4, "spawn_interval": 1.5},
        {"enemy_type": "yellow", "count": 6, "spawn_interval": 0.8},
    ],
    # Wave 8: mixed camo + fast
    [
        {"enemy_type": "camo", "count": 8, "spawn_interval": 0.5},
        {"enemy_type": "pink", "count": 12, "spawn_interval": 0.3},
    ],
    # Wave 9: armored enemies
    [
        {"enemy_type": "armored", "count": 3, "spawn_interval": 2.0},
        {"enemy_type": "yellow", "count": 8, "spawn_interval": 0.6},
    ],
    # Wave 10: shield enemies
    [
        {"enemy_type": "shield", "count": 4, "spawn_interval": 1.5},
        {"enemy_type": "green", "count": 15, "spawn_interval": 0.25},
    ],
    # Wave 11: heavy mix
    [
        {"enemy_type": "armored", "count": 5, "spawn_interval": 1.5},
        {"enemy_type": "regen", "count": 5, "spawn_interval": 1.0},
        {"enemy_type": "camo", "count": 8, "spawn_interval": 0.5},
    ],
    # Wave 12: speed rush
    [
        {"enemy_type": "pink", "count": 20, "spawn_interval": 0.2},
        {"enemy_type": "yellow", "count": 8, "spawn_interval": 0.5},
    ],
    # Wave 13: camo + regen + shield
    [
        {"enemy_type": "camo", "count": 10, "spawn_interval": 0.5},
        {"enemy_type": "regen", "count": 6, "spawn_interval": 1.0},
        {"enemy_type": "shield", "count": 5, "spawn_interval": 1.2},
    ],
    # Wave 14: heavy armor wave
    [
        {"enemy_type": "armored", "count": 8, "spawn_interval": 1.2},
        {"enemy_type": "shield", "count": 6, "spawn_interval": 1.0},
        {"enemy_type": "yellow", "count": 12, "spawn_interval": 0.4},
    ],
    # Wave 15: boss fight
    [
        {"enemy_type": "boss", "count": 1, "spawn_interval": 1.0},
        {"enemy_type": "armored", "count": 4, "spawn_interval": 2.0},
        {"enemy_type": "shield", "count": 4, "spawn_interval": 1.5},
        {"enemy_type": "camo", "count": 6, "spawn_interval": 0.8},
    ],
]


# ---------------------------------------------------------------------------
# Targeting mode definitions
# ---------------------------------------------------------------------------
TARGETING_MODES = ["first", "last", "strong", "close"]
