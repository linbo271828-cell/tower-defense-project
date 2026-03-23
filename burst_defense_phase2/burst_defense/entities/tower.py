"""Tower entity.

Phase 1 includes one simple tower type. The targeting logic is kept inside this
class for readability. Once the project adds more targeting modes and special
filters, moving that logic into a dedicated targeting module will be worthwhile.

Phase 2 adds: multiple tower types, 4 targeting modes (first, last, strong,
close), status effects on hit, support tower aura, camo detection, splash and
pierce attack types.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pygame

from burst_defense import settings
from burst_defense.data import TARGETING_MODES
from burst_defense.entities.enemy import Enemy
from burst_defense.entities.projectile import Projectile
from burst_defense.entities.status_effect import StatusEffect


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

    # Phase 2 fields
    color: tuple = (241, 196, 15)
    attack_type: str = "single"
    damage_type: str = "sharp"
    pierce: int = 1
    splash_radius: float = 0
    status_on_hit: dict | None = None
    can_see_camo: bool = False
    targeting_mode: str = "first"
    is_support: bool = False
    aura_config: dict | None = None
    sell_value: int = field(init=False)
    upgrade_level: int = field(default=0, init=False)

    # Aura buff tracking
    buffed_by: set = field(default_factory=set, init=False)
    _buff_attack_speed: float = field(default=0.0, init=False)
    _buff_range: float = field(default=0.0, init=False)
    _base_fire_rate: float = field(default=0.0, init=False)
    _base_range: float = field(default=0.0, init=False)

    # Visual
    selected: bool = field(default=False, init=False)
    angle: float = field(default=0.0, init=False)
    fired_this_frame: bool = field(default=False, init=False)
    _aura_pulse: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.sell_value = int(self.cost * 0.7)
        self._base_fire_rate = self.fire_rate
        self._base_range = self.range_radius

    def update(self, delta_time: float, enemies: list[Enemy], projectiles: list[Projectile]) -> None:
        """Fire at the best target in range when off cooldown."""

        self.fired_this_frame = False

        if self.is_support:
            self._aura_pulse += delta_time
            return

        self.cooldown_remaining = max(0.0, self.cooldown_remaining - delta_time)

        target = self._choose_target(enemies)
        if target is None or self.cooldown_remaining > 0:
            return

        # Rotate barrel toward target
        self.angle = math.atan2(
            target.position.y - self.position.y,
            target.position.x - self.position.x,
        )

        projectiles.append(
            Projectile(
                position=self.position.copy(),
                target=target,
                speed=self.projectile_speed,
                damage=self.damage,
                damage_type=self.damage_type,
                pierce_remaining=self.pierce,
                splash_radius=self.splash_radius,
                status_on_hit=self.status_on_hit,
                source_tower_id=id(self),
                color=tuple(min(255, c + 80) for c in self.color),
            )
        )
        if self.fire_rate > 0:
            self.cooldown_remaining = 1.0 / self.fire_rate
        self.fired_this_frame = True

    def _choose_target(self, enemies: list[Enemy]) -> Enemy | None:
        """Choose the best target based on the current targeting mode.

        "First" targeting is the most natural starting policy for a tower
        defense prototype because it clearly rewards good placement.
        """

        enemies_in_range = [
            enemy
            for enemy in enemies
            if enemy.is_alive and not enemy.has_leaked
            and self.position.distance_to(enemy.position) <= self.range_radius
            and (self.can_see_camo or "camo" not in enemy.traits)
        ]

        if not enemies_in_range:
            return None

        if self.targeting_mode == "first":
            return max(enemies_in_range, key=lambda e: e.distance_travelled)
        elif self.targeting_mode == "last":
            return min(enemies_in_range, key=lambda e: e.distance_travelled)
        elif self.targeting_mode == "strong":
            return max(enemies_in_range, key=lambda e: e.health)
        elif self.targeting_mode == "close":
            return min(enemies_in_range, key=lambda e: self.position.distance_to(e.position))
        else:
            return max(enemies_in_range, key=lambda e: e.distance_travelled)

    def has_infinite_range(self) -> bool:
        """Return whether this tower can target across the entire map."""
        return math.isinf(self._base_range)

    def get_upgrade_cost(self) -> int | None:
        """Return the current upgrade cost, or None if range cannot improve."""
        if self.has_infinite_range():
            return None
        # Mildly scaling cost keeps upgrades relevant across the run.
        base_cost = max(45, int(self.cost * 0.55))
        return int(base_cost * (1.0 + self.upgrade_level * 0.45))

    def upgrade_range(self) -> bool:
        """Increase base range and update derived values."""
        if self.has_infinite_range():
            return False
        paid_cost = self.get_upgrade_cost() or 0
        self.upgrade_level += 1
        self._base_range += 20
        self.sell_value += int(paid_cost * 0.45)
        self._recalc_stats()
        return True

    def cycle_targeting_mode(self) -> None:
        """Advance to the next targeting mode."""
        idx = TARGETING_MODES.index(self.targeting_mode)
        self.targeting_mode = TARGETING_MODES[(idx + 1) % len(TARGETING_MODES)]

    # --- Aura buff system ---

    def apply_buff(self, support_id: int, as_bonus: float, r_bonus: float) -> None:
        if support_id in self.buffed_by:
            return
        self.buffed_by.add(support_id)
        self._buff_attack_speed += as_bonus
        self._buff_range += r_bonus
        self._recalc_stats()

    def remove_buff(self, support_id: int, as_bonus: float, r_bonus: float) -> None:
        if support_id not in self.buffed_by:
            return
        self.buffed_by.discard(support_id)
        self._buff_attack_speed -= as_bonus
        self._buff_range -= r_bonus
        self._recalc_stats()

    def _recalc_stats(self) -> None:
        self.fire_rate = self._base_fire_rate * (1.0 + self._buff_attack_speed)
        self.range_radius = self._base_range + self._buff_range

    def draw(self, surface: pygame.Surface, show_range: bool = False) -> None:
        """Draw the tower and optionally its attack radius."""

        if (show_range or self.selected) and not math.isinf(self.range_radius):
            range_surface = pygame.Surface(
                (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA
            )
            pygame.draw.circle(
                range_surface, (255, 255, 255, 25), self.position, int(self.range_radius)
            )
            pygame.draw.circle(
                range_surface, (255, 255, 255, 50), self.position, int(self.range_radius), 1
            )
            surface.blit(range_surface, (0, 0))

        if self.is_support:
            self._draw_support(surface)
        else:
            self._draw_attacker(surface)

        # Buff indicator
        if self.buffed_by:
            bx = int(self.position.x + self.body_radius - 3)
            by = int(self.position.y - self.body_radius + 3)
            pygame.draw.circle(surface, (200, 180, 255), (bx, by), 3)

        # Selection highlight
        if self.selected:
            pygame.draw.circle(surface, (255, 255, 100), self.position, int(self.body_radius + 2), 2)

    def _draw_attacker(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.color, self.position, self.body_radius)
        pygame.draw.circle(surface, (30, 33, 38), self.position, self.body_radius, 2)

        # The barrel points toward the target (or upward by default).
        barrel_len = self.body_radius + 6
        end_x = self.position.x + math.cos(self.angle) * barrel_len
        end_y = self.position.y + math.sin(self.angle) * barrel_len
        barrel_color = tuple(max(0, c - 60) for c in self.color)
        pygame.draw.line(surface, barrel_color, self.position, (int(end_x), int(end_y)), 4)

    def _draw_support(self, surface: pygame.Surface) -> None:
        # Pulsing aura ring
        pulse = 0.5 + 0.5 * math.sin(self._aura_pulse * 2.5)
        aura_r = int(self.range_radius * (0.15 + pulse * 0.08))
        aura_s = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura_s, (*self.color, int(15 + pulse * 15)), (aura_r, aura_r), aura_r)
        surface.blit(aura_s, (int(self.position.x) - aura_r, int(self.position.y) - aura_r))

        pygame.draw.circle(surface, self.color, self.position, self.body_radius)
        pygame.draw.circle(surface, (30, 33, 38), self.position, self.body_radius, 2)

        # Diamond inner marker
        r = self.body_radius - 4
        pts = [
            (self.position.x, self.position.y - r),
            (self.position.x + r, self.position.y),
            (self.position.x, self.position.y + r),
            (self.position.x - r, self.position.y),
        ]
        inner = tuple(min(255, c + 40) for c in self.color)
        pygame.draw.polygon(surface, inner, pts, 2)
