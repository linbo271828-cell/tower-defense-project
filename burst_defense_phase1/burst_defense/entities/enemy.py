"""Enemy entity for Burst Defense.

This first version intentionally uses straightforward path-following and health
logic. More complex Bloons-inspired mechanics, like layered children on pop,
can be added later without rewriting the path architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from burst_defense import settings
from burst_defense.path import Path


@dataclass
class Enemy:
    """An enemy traveling along the map path."""

    enemy_type: str
    display_name: str
    path: Path
    max_health: int
    speed: float
    reward: int
    leak_damage: int
    color: tuple[int, int, int]
    radius: float = settings.ENEMY_RADIUS
    health: int = field(init=False)
    current_segment_index: int = field(default=0, init=False)
    position: pygame.Vector2 = field(init=False)
    distance_travelled: float = field(default=0.0, init=False)
    is_alive: bool = field(default=True, init=False)
    has_leaked: bool = field(default=False, init=False)
    reward_granted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.health = self.max_health
        self.position = self.path.waypoints[0].copy()

    def update(self, delta_time: float) -> bool:
        """Move the enemy along the path.

        Returns `True` if the enemy leaked during this update. Returning the
        event directly makes life-loss handling in `Game` easy to read.
        """

        if not self.is_alive or self.has_leaked:
            return False

        remaining_move_distance = self.speed * delta_time

        while remaining_move_distance > 0 and self.current_segment_index < len(self.path.waypoints) - 1:
            segment_start = self.path.waypoints[self.current_segment_index]
            segment_end = self.path.waypoints[self.current_segment_index + 1]
            segment_vector = segment_end - self.position
            distance_to_segment_end = segment_vector.length()

            if distance_to_segment_end == 0:
                self.current_segment_index += 1
                continue

            if remaining_move_distance < distance_to_segment_end:
                direction = segment_vector.normalize()
                movement = direction * remaining_move_distance
                self.position += movement
                self.distance_travelled += movement.length()
                remaining_move_distance = 0
            else:
                self.position = segment_end.copy()
                self.distance_travelled += distance_to_segment_end
                remaining_move_distance -= distance_to_segment_end
                self.current_segment_index += 1

        if self.current_segment_index >= len(self.path.waypoints) - 1:
            self.has_leaked = True
            self.is_alive = False
            return True

        return False

    def take_damage(self, damage_amount: int) -> bool:
        """Apply damage and report whether the enemy was destroyed."""

        if not self.is_alive:
            return False

        self.health -= damage_amount
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Render the enemy and a small health bar."""

        pygame.draw.circle(surface, self.color, self.position, self.radius)
        pygame.draw.circle(surface, (20, 24, 29), self.position, self.radius, 2)
        self._draw_health_bar(surface)

    def _draw_health_bar(self, surface: pygame.Surface) -> None:
        if self.max_health <= 1:
            return

        bar_width = self.radius * 2.0
        bar_height = 6
        bar_left = self.position.x - self.radius
        bar_top = self.position.y - self.radius - 12

        background_rect = pygame.Rect(bar_left, bar_top, bar_width, bar_height)
        pygame.draw.rect(surface, settings.HEALTH_BAR_BG_COLOR, background_rect, border_radius=3)

        fill_ratio = self.health / self.max_health
        fill_rect = pygame.Rect(bar_left, bar_top, bar_width * fill_ratio, bar_height)
        pygame.draw.rect(surface, settings.HEALTH_BAR_FILL_COLOR, fill_rect, border_radius=3)
