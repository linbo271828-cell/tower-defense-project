"""Path geometry helpers.

This module owns map path math so that enemy movement and tower placement code
stay simpler. The path is represented by straight line segments between
waypoints, which is an excellent Phase 1 tradeoff between clarity and utility.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable

import pygame

from burst_defense import settings


@dataclass
class Path:
    """A polyline path used by enemies and placement validation."""

    waypoints: list[pygame.Vector2]
    thickness: float

    def __post_init__(self) -> None:
        self.segment_lengths: list[float] = []
        self.total_length = 0.0

        for start, end in zip(self.waypoints, self.waypoints[1:]):
            segment_length = start.distance_to(end)
            self.segment_lengths.append(segment_length)
            self.total_length += segment_length

    @classmethod
    def from_points(cls, points: Iterable[tuple[float, float]], thickness: float) -> "Path":
        """Create a path from raw `(x, y)` tuples."""

        return cls([pygame.Vector2(point) for point in points], thickness)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the visible map path.

        The double draw gives the path a darker border, which improves visual
        clarity without requiring art assets.
        """

        pygame.draw.lines(
            surface,
            settings.PATH_EDGE_COLOR,
            False,
            self.waypoints,
            int(self.thickness + 10),
        )
        pygame.draw.lines(
            surface,
            settings.PATH_COLOR,
            False,
            self.waypoints,
            int(self.thickness),
        )

    def distance_to_point(self, point: pygame.Vector2) -> float:
        """Return the shortest distance from a point to the path."""

        if len(self.waypoints) < 2:
            return float("inf")

        smallest_distance = float("inf")
        for start, end in zip(self.waypoints, self.waypoints[1:]):
            candidate_distance = _distance_point_to_segment(point, start, end)
            smallest_distance = min(smallest_distance, candidate_distance)
        return smallest_distance


def _distance_point_to_segment(
    point: pygame.Vector2,
    segment_start: pygame.Vector2,
    segment_end: pygame.Vector2,
) -> float:
    """Compute the shortest distance from a point to a line segment.

    This helper is used for placement validation. We keep it here instead of in
    a generic math module because its only current responsibility is path logic.
    """

    segment = segment_end - segment_start
    segment_length_squared = segment.length_squared()

    if segment_length_squared == 0:
        return point.distance_to(segment_start)

    projection = (point - segment_start).dot(segment) / segment_length_squared
    projection = max(0.0, min(1.0, projection))
    nearest_point = segment_start + segment * projection
    dx = point.x - nearest_point.x
    dy = point.y - nearest_point.y
    return sqrt(dx * dx + dy * dy)
