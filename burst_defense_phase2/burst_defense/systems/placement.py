"""Tower placement validation helpers.

Keeping placement checks in a dedicated module makes the `Game` class easier to
read and gives future contributors one obvious place to extend build rules.
"""

from __future__ import annotations

import pygame

from burst_defense.path import Path
from burst_defense.settings import RectBounds


def validate_tower_placement(
    center: pygame.Vector2,
    tower_radius: float,
    path: Path,
    existing_towers: list,
    playable_bounds: RectBounds,
) -> tuple[bool, str]:
    """Return whether a tower can be placed and, if not, explain why."""

    if center.x - tower_radius < playable_bounds.left or center.x + tower_radius > playable_bounds.right:
        return False, "Tower must stay inside the play area."

    if center.y - tower_radius < playable_bounds.top or center.y + tower_radius > playable_bounds.bottom:
        return False, "Tower must stay inside the play area."

    path_clearance = path.thickness / 2 + tower_radius + 4
    if path.distance_to_point(center) < path_clearance:
        return False, "Tower cannot be placed on top of the enemy path."

    for tower in existing_towers:
        minimum_distance = tower.body_radius + tower_radius + 8
        if center.distance_to(tower.position) < minimum_distance:
            return False, "Tower is too close to an existing tower."

    return True, "Placement is valid."
