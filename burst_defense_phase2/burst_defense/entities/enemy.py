"""Enemy entity for Burst Defense.

This first version intentionally uses straightforward path-following and health
logic. More complex Bloons-inspired mechanics, like layered children on pop,
can be added later without rewriting the path architecture.

Phase 2 adds: layered children (splitting on pop), traits (camo, regen, armored,
fast, boss, shielded), status effects (slow, burn), shield HP, and regeneration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pygame

from burst_defense import settings
from burst_defense.entities.status_effect import StatusEffect
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

    # Phase 2 fields
    traits: set = field(default_factory=set)
    children_spec: list = field(default_factory=list)
    shield_hp: float = 0.0
    max_shield_hp: float = 0.0
    regen_rate: float = 0.0
    resistances: dict = field(default_factory=dict)
    status_effects: list = field(default_factory=list, init=False)
    start_progress: float = 0.0  # for spawning children mid-path
    _regen_pulse: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.health = self.max_health
        self.max_shield_hp = self.shield_hp
        if self.start_progress > 0 and len(self.path.waypoints) >= 2:
            self.position = self._get_position_at_progress(self.start_progress)
            self.distance_travelled = self.start_progress
            self._advance_segment_index()
        else:
            self.position = self.path.waypoints[0].copy()

    def _get_position_at_progress(self, progress: float) -> pygame.Vector2:
        """Return the world position at a given distance along the path."""
        remaining = progress
        for i in range(len(self.path.waypoints) - 1):
            seg_start = self.path.waypoints[i]
            seg_end = self.path.waypoints[i + 1]
            seg_len = self.path.segment_lengths[i]
            if remaining <= seg_len:
                t = remaining / seg_len if seg_len > 0 else 0
                return seg_start + (seg_end - seg_start) * t
            remaining -= seg_len
        return self.path.waypoints[-1].copy()

    def _advance_segment_index(self) -> None:
        """Set current_segment_index based on distance_travelled."""
        remaining = self.distance_travelled
        for i in range(len(self.path.segment_lengths)):
            if remaining <= self.path.segment_lengths[i]:
                self.current_segment_index = i
                return
            remaining -= self.path.segment_lengths[i]
        self.current_segment_index = len(self.path.waypoints) - 2

    def update(self, delta_time: float) -> bool:
        """Move the enemy along the path.

        Returns `True` if the enemy leaked during this update. Returning the
        event directly makes life-loss handling in `Game` easy to read.
        """

        if not self.is_alive or self.has_leaked:
            return False

        # Process status effects
        burn_damage = 0.0
        for effect in self.status_effects:
            burn_damage += effect.update(delta_time)
        self.status_effects = [e for e in self.status_effects if not e.expired]

        if burn_damage > 0:
            self.health -= burn_damage
            if self.health <= 0:
                self.health = 0
                self.is_alive = False
                return False

        # Regen
        if self.regen_rate > 0 and self.health < self.max_health:
            self.health = min(self.max_health, self.health + self.regen_rate * delta_time)
            self._regen_pulse += delta_time

        # Movement with status effect speed modifiers
        effective_speed = self._get_effective_speed()
        remaining_move_distance = effective_speed * delta_time

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

    def _get_effective_speed(self) -> float:
        """Current speed accounting for slow/stun effects."""
        factor = 1.0
        for effect in self.status_effects:
            f = effect.get_slow_factor()
            if f < factor:
                factor = f
        return self.speed * factor

    def apply_status_effect(self, effect: StatusEffect) -> None:
        """Apply a status effect, refreshing if the same type from the same source."""
        for existing in self.status_effects:
            if existing.effect_type == effect.effect_type and existing.source_id == effect.source_id:
                existing._remaining = max(existing._remaining, effect.duration)
                existing.magnitude = max(existing.magnitude, effect.magnitude)
                return
        self.status_effects.append(effect)

    def has_active_effect(self, effect_type: str) -> bool:
        return any(e.effect_type == effect_type and not e.expired for e in self.status_effects)

    def take_damage(self, damage_amount: float, damage_type: str = "sharp") -> bool:
        """Apply damage with optional shield and resistance handling.

        Returns True if the enemy was destroyed.
        """

        if not self.is_alive:
            return False

        # Apply resistance
        resistance = self.resistances.get(damage_type, 1.0)
        damage_amount = damage_amount * resistance

        # Shield absorbs first
        if self.shield_hp > 0:
            if damage_amount <= self.shield_hp:
                self.shield_hp -= damage_amount
                return False
            else:
                damage_amount -= self.shield_hp
                self.shield_hp = 0

        self.health -= damage_amount
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Render the enemy and a small health bar."""

        # Camo enemies are semi-transparent
        if "camo" in self.traits:
            self._draw_camo(surface)
        else:
            self._draw_body(surface)

        self._draw_status_indicators(surface)
        self._draw_health_bar(surface)

    def _draw_body(self, surface: pygame.Surface) -> None:
        """Draw the standard enemy body."""
        # Boss: extra ring
        if "boss" in self.traits:
            pygame.draw.circle(surface, (200, 180, 50), self.position, self.radius + 4, 2)

        pygame.draw.circle(surface, self.color, self.position, self.radius)
        pygame.draw.circle(surface, (20, 24, 29), self.position, self.radius, 2)

        # Highlight
        highlight = tuple(min(255, c + 50) for c in self.color)
        hx = int(self.position.x - self.radius * 0.25)
        hy = int(self.position.y - self.radius * 0.25)
        pygame.draw.circle(surface, highlight, (hx, hy), max(2, int(self.radius * 0.3)))

    def _draw_camo(self, surface: pygame.Surface) -> None:
        """Draw camo enemy with transparency and dashed outline."""
        s = pygame.Surface((int(self.radius * 2 + 4), int(self.radius * 2 + 4)), pygame.SRCALPHA)
        r = int(self.radius)
        pygame.draw.circle(s, (*self.color, 90), (r + 2, r + 2), r)
        for angle_deg in range(0, 360, 30):
            a = math.radians(angle_deg)
            x1 = r + 2 + math.cos(a) * r
            y1 = r + 2 + math.sin(a) * r
            x2 = r + 2 + math.cos(a) * (r - 3)
            y2 = r + 2 + math.sin(a) * (r - 3)
            pygame.draw.line(s, (*self.color, 140), (int(x1), int(y1)), (int(x2), int(y2)), 1)
        surface.blit(s, (int(self.position.x) - r - 2, int(self.position.y) - r - 2))

    def _draw_status_indicators(self, surface: pygame.Surface) -> None:
        """Draw small colored dots for active status effects."""
        indicators = []
        if self.has_active_effect("slow"):
            indicators.append((100, 180, 255))
        if self.has_active_effect("burn"):
            indicators.append((255, 140, 40))
        if self.has_active_effect("stun"):
            indicators.append((255, 255, 80))

        for i, c in enumerate(indicators):
            angle = math.pi * 0.5 + i * (2 * math.pi / max(len(indicators), 1))
            ix = int(self.position.x + math.cos(angle) * (self.radius + 6))
            iy = int(self.position.y + math.sin(angle) * (self.radius + 6))
            pygame.draw.circle(surface, c, (ix, iy), 3)

        # Shield arc
        if self.max_shield_hp > 0 and self.shield_hp > 0:
            frac = self.shield_hp / self.max_shield_hp
            arc_extent = frac * 2 * math.pi
            r = int(self.radius + 3)
            rect = pygame.Rect(
                int(self.position.x) - r, int(self.position.y) - r, r * 2, r * 2
            )
            pygame.draw.arc(surface, settings.SHIELD_BAR_COLOR, rect, 0, arc_extent, 2)

        # Regen pulse
        if self.regen_rate > 0 and self.health < self.max_health:
            pulse = abs(math.sin(self._regen_pulse * 3)) * 0.4
            glow_r = int(self.radius * (1.15 + pulse * 0.2))
            gs = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (80, 255, 80, int(20 + pulse * 25)), (glow_r, glow_r), glow_r)
            surface.blit(gs, (int(self.position.x) - glow_r, int(self.position.y) - glow_r))

        # Armored trait marker
        if "armored" in self.traits:
            px = int(self.position.x)
            py = int(self.position.y + self.radius + 5)
            pts = [(px - 4, py), (px, py + 6), (px + 4, py)]
            pygame.draw.polygon(surface, (160, 160, 180), pts)

    def _draw_health_bar(self, surface: pygame.Surface) -> None:
        if self.max_health <= 1 and self.max_shield_hp <= 0:
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
