"""Tower entity.

Phase 1 includes one simple tower type. The targeting logic is kept inside this
class for readability. Once the project adds more targeting modes and special
filters, moving that logic into a dedicated targeting module will be worthwhile.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from burst_defense import settings
from burst_defense.entities.enemy import Enemy
from burst_defense.entities.projectile import Projectile


@dataclass
class Tower:
    """A basic auto-attacking tower."""

    tower_type: str
    display_name: str
    position: pygame.Vector2
    range_radius: float
    fire_rate: float
    damage: int
    projectile_speed: float
    cost: int
    body_radius: float = settings.TOWER_RADIUS
    cooldown_remaining: float = field(default=0.0, init=False)

    def update(self, delta_time: float, enemies: list[Enemy], projectiles: list[Projectile]) -> None:
        """Fire at the most advanced enemy in range when off cooldown."""

        self.cooldown_remaining = max(0.0, self.cooldown_remaining - delta_time)

        target = self._choose_target(enemies)
        if target is None or self.cooldown_remaining > 0:
            return

        projectiles.append(
            Projectile(
                position=self.position.copy(),
                target=target,
                speed=self.projectile_speed,
                damage=self.damage,
            )
        )
        self.cooldown_remaining = 1.0 / self.fire_rate

    def _choose_target(self, enemies: list[Enemy]) -> Enemy | None:
        """Choose the enemy furthest along the path within range.

        "First" targeting is the most natural starting policy for a tower
        defense prototype because it clearly rewards good placement.
        """

        enemies_in_range = [
            enemy
            for enemy in enemies
            if enemy.is_alive and not enemy.has_leaked
            and self.position.distance_to(enemy.position) <= self.range_radius
        ]

        if not enemies_in_range:
            return None

        return max(enemies_in_range, key=lambda enemy: enemy.distance_travelled)

    def draw(self, surface: pygame.Surface, show_range: bool = False) -> None:
        """Draw the tower and optionally its attack radius."""

        if show_range:
            pygame.draw.circle(surface, (255, 255, 255), self.position, self.range_radius, 1)

        pygame.draw.circle(surface, settings.TOWER_BODY_COLOR, self.position, self.body_radius)
        pygame.draw.circle(surface, (30, 33, 38), self.position, self.body_radius, 2)

        # The barrel points upward in Phase 1. Rotating it toward the current
        # target is a nice polish task for a later phase.
        barrel_rect = pygame.Rect(0, 0, 12, 26)
        barrel_rect.centerx = self.position.x
        barrel_rect.bottom = self.position.y - 4
        pygame.draw.rect(surface, settings.TOWER_BARREL_COLOR, barrel_rect, border_radius=4)
