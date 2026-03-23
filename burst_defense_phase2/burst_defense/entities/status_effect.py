"""Status effects that can be applied to enemies by tower projectiles.

Phase 2 adds slow as the primary status effect. The system is designed to
support burn, stun, and armor break in the future.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StatusEffect:
    """A timed debuff applied to an enemy.

    Types:
        slow:  reduces speed by `magnitude` fraction (0.4 = 40% slower)
        burn:  deals `magnitude` damage every `tick_interval` seconds
        stun:  reduces speed to zero for the duration
    """

    effect_type: str
    duration: float
    magnitude: float = 0.5
    tick_interval: float = 0.5
    source_id: int = -1
    _remaining: float = 0.0
    _tick_timer: float = 0.0

    def __post_init__(self) -> None:
        self._remaining = self.duration
        self._tick_timer = 0.0

    @property
    def expired(self) -> bool:
        return self._remaining <= 0

    def update(self, delta_time: float) -> float:
        """Advance the effect. Returns tick damage for burn, else 0."""
        self._remaining -= delta_time
        damage = 0.0

        if self.effect_type == "burn":
            self._tick_timer += delta_time
            if self._tick_timer >= self.tick_interval:
                self._tick_timer -= self.tick_interval
                damage = self.magnitude

        return damage

    def get_slow_factor(self) -> float:
        """Speed multiplier. 1.0 = no change, 0.0 = frozen."""
        if self.expired:
            return 1.0
        if self.effect_type == "stun":
            return 0.0
        if self.effect_type == "slow":
            return max(0.1, 1.0 - self.magnitude)
        return 1.0
