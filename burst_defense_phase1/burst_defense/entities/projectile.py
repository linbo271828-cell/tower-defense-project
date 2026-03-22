"""Projectile entity.

Projectiles are kept intentionally simple in Phase 1: they home toward the
selected target and disappear on impact. This is enough to validate the combat
loop before adding pierce, splash, or damage type rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from burst_defense import settings
from burst_defense.entities.enemy import Enemy


@dataclass
class Projectile:
    """A basic homing projectile fired by a tower."""

    position: pygame.Vector2
    target: Enemy
    speed: float
    damage: int
    radius: float = settings.PROJECTILE_RADIUS
    is_active: bool = field(default=True, init=False)

    def update(self, delta_time: float) -> None:
        """Move toward the target and apply damage on contact."""

        if not self.is_active:
            return

        if not self.target.is_alive or self.target.has_leaked:
            self.is_active = False
            return

        target_vector = self.target.position - self.position
        distance_to_target = target_vector.length()
        hit_distance = self.radius + self.target.radius

        if distance_to_target <= hit_distance:
            self.target.take_damage(self.damage)
            self.is_active = False
            return

        if distance_to_target == 0:
            self.is_active = False
            return

        direction = target_vector.normalize()
        movement_distance = self.speed * delta_time
        self.position += direction * movement_distance

        # A fast projectile can step past a target in one update. We check again
        # after movement so impacts still feel reliable at higher speeds.
        if self.position.distance_to(self.target.position) <= hit_distance:
            self.target.take_damage(self.damage)
            self.is_active = False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the projectile as a small bright circle."""

        pygame.draw.circle(surface, settings.PROJECTILE_COLOR, self.position, self.radius)
