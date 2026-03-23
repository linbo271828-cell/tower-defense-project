"""Wave scheduling.

The wave manager owns spawn timing and high-level round progression. It does not
update enemies directly; that responsibility stays in the game loop.
"""

from __future__ import annotations

from dataclasses import dataclass

from burst_defense.data import WAVE_DEFINITIONS


@dataclass
class SpawnGroupState:
    """Mutable state for one spawn group inside a wave."""

    enemy_type: str
    enemies_remaining: int
    spawn_interval: float


class WaveManager:
    """Spawn enemies from the static wave definitions."""

    def __init__(self) -> None:
        self.wave_index = -1
        self.current_groups: list[SpawnGroupState] = []
        self.current_group_index = 0
        self.spawn_timer = 0.0
        self.wave_in_progress = False
        self.wave_finished_spawning = False

    @property
    def current_wave_number(self) -> int:
        """Return a 1-based wave number for UI display."""

        return self.wave_index + 1

    @property
    def total_waves(self) -> int:
        """Total number of waves defined."""
        return len(WAVE_DEFINITIONS)

    def has_more_waves(self) -> bool:
        """Return whether another wave can be started."""

        return self.wave_index + 1 < len(WAVE_DEFINITIONS)

    def start_next_wave(self) -> bool:
        """Advance to the next wave if possible.

        Returns `True` if a new wave started.
        """

        if self.wave_in_progress or not self.has_more_waves():
            return False

        self.wave_index += 1
        self.current_groups = [
            SpawnGroupState(
                enemy_type=group_definition["enemy_type"],
                enemies_remaining=group_definition["count"],
                spawn_interval=group_definition["spawn_interval"],
            )
            for group_definition in WAVE_DEFINITIONS[self.wave_index]
        ]
        self.current_group_index = 0
        self.spawn_timer = 0.0
        self.wave_in_progress = True
        self.wave_finished_spawning = False
        return True

    def update(self, delta_time: float) -> list[str]:
        """Advance spawn timers and return enemy types that should spawn now."""

        if not self.wave_in_progress or self.wave_finished_spawning:
            return []

        spawned_enemy_types: list[str] = []
        self.spawn_timer -= delta_time

        while self.spawn_timer <= 0 and self.current_group_index < len(self.current_groups):
            current_group = self.current_groups[self.current_group_index]

            if current_group.enemies_remaining > 0:
                spawned_enemy_types.append(current_group.enemy_type)
                current_group.enemies_remaining -= 1
                self.spawn_timer += current_group.spawn_interval
            else:
                self.current_group_index += 1

        if self.current_group_index >= len(self.current_groups):
            self.wave_finished_spawning = True

        return spawned_enemy_types

    def maybe_finish_wave(self, active_enemy_count: int) -> bool:
        """Mark the wave complete when nothing remains alive or queued."""

        if not self.wave_in_progress:
            return False

        if self.wave_finished_spawning and active_enemy_count == 0:
            self.wave_in_progress = False
            return True

        return False
