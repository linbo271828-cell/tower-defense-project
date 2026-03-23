"""Projectile entity.

Projectiles are kept intentionally simple in Phase 1: they home toward the
selected target and disappear on impact. This is enough to validate the combat
loop before adding pierce, splash, or damage type rules.

Phase 2 adds: pierce (hit multiple enemies), splash (damage area on impact),
status effect payloads (slow, burn), and damage types for resistance checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from burst_defense import settings
from burst_defense.entities.enemy import Enemy


@dataclass
class Projectile:
    """A homing projectile fired by a tower, with optional pierce and splash."""

    position: pygame.Vector2
    target: Enemy
    speed: float
    damage: int
    radius: float = settings.PROJECTILE_RADIUS
    is_active: bool = field(default=True, init=False)

    # Phase 2 fields
    damage_type: str = "sharp"
    pierce_remaining: int = 1
    splash_radius: float = 0
    status_on_hit: dict | None = None
    source_tower_id: int = -1
    color: tuple = settings.PROJECTILE_COLOR
    hit_enemies: set = field(default_factory=set, init=False)
    max_lifetime: float = 3.0
    _age: float = field(default=0.0, init=False)

    def update(self, delta_time: float) -> None:
        """Move toward the target and apply damage on contact."""

        if not self.is_active:
            return

        self._age += delta_time
        if self._age >= self.max_lifetime:
            self.is_active = False
            return

        if not self.target.is_alive or self.target.has_leaked:
            self.is_active = False
            return

        target_vector = self.target.position - self.position
        distance_to_target = target_vector.length()
        hit_distance = self.radius + self.target.radius

        if distance_to_target <= hit_distance:
            self._on_hit(self.target)
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
            self._on_hit(self.target)

    def _on_hit(self, enemy: Enemy) -> None:
        """Handle impact — apply damage, status effect, track pierce."""
        enemy.take_damage(self.damage, self.damage_type)

        if self.status_on_hit and enemy.is_alive:
            from burst_defense.entities.status_effect import StatusEffect
            effect = StatusEffect(
                effect_type=self.status_on_hit["type"],
                duration=self.status_on_hit["duration"],
                magnitude=self.status_on_hit.get("magnitude", 0.5),
                tick_interval=self.status_on_hit.get("tick_interval", 0.5),
                source_id=self.source_tower_id,
            )
            enemy.apply_status_effect(effect)

        self.hit_enemies.add(id(enemy))
        self.pierce_remaining -= 1
        if self.pierce_remaining <= 0:
            self.is_active = False

    def check_pierce_hit(self, enemies: list[Enemy]) -> list[Enemy]:
        """For pierce projectiles, check collisions with additional enemies."""
        if not self.is_active or self.pierce_remaining <= 0:
            return []

        newly_hit = []
        for enemy in enemies:
            if not enemy.is_alive or enemy.has_leaked:
                continue
            if id(enemy) in self.hit_enemies:
                continue
            if self.position.distance_to(enemy.position) <= self.radius + enemy.radius:
                self._on_hit(enemy)
                newly_hit.append(enemy)
                if not self.is_active:
                    break
        return newly_hit

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the projectile as a small bright circle."""

        pygame.draw.circle(surface, self.color, self.position, self.radius)
        core = tuple(min(255, c + 60) for c in self.color)
        pygame.draw.circle(surface, core, self.position, max(1, self.radius // 2))
