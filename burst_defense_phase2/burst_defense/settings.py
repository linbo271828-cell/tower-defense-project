"""Centralized project settings.

Keeping constants in one place makes tuning easier and avoids magic numbers
being scattered across gameplay code.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Window and timing
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Burst Defense - Phase 2"
TARGET_FPS = 60


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
TOP_BAR_HEIGHT = 96
RIGHT_PANEL_WIDTH = 280
PLAY_AREA_PADDING = 24


# ---------------------------------------------------------------------------
# Core gameplay values
# ---------------------------------------------------------------------------
STARTING_MONEY = 400
STARTING_LIVES = 25
TOWER_COST = 100
TOWER_RADIUS = 22
TOWER_RANGE = 165
TOWER_FIRE_RATE = 1.2  # shots per second
TOWER_DAMAGE = 1
PROJECTILE_SPEED = 420
PROJECTILE_RADIUS = 6

ENEMY_RADIUS = 16
PATH_THICKNESS = 52

PREVIEW_GOOD_ALPHA = 120
PREVIEW_BAD_ALPHA = 120
STATUS_MESSAGE_DURATION_SECONDS = 2.25


# ---------------------------------------------------------------------------
# Phase 2+ gameplay values
# ---------------------------------------------------------------------------
SPEED_OPTIONS = [1.0, 2.0, 3.0]
MAX_PARTICLES = 600


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
BACKGROUND_COLOR = (32, 36, 43)
GRID_COLOR = (42, 48, 58)
TEXT_COLOR = (236, 240, 241)
SUBTLE_TEXT_COLOR = (190, 196, 204)
PANEL_COLOR = (24, 27, 33)
PANEL_BORDER_COLOR = (74, 84, 99)
PATH_COLOR = (178, 139, 96)
PATH_EDGE_COLOR = (120, 91, 61)
ENEMY_COLOR = (231, 76, 60)
ENEMY_STRONG_COLOR = (52, 152, 219)
TOWER_BODY_COLOR = (241, 196, 15)
TOWER_BARREL_COLOR = (120, 86, 10)
PROJECTILE_COLOR = (248, 249, 250)
PLACEMENT_OK_COLOR = (46, 204, 113)
PLACEMENT_BAD_COLOR = (231, 76, 60)
HEALTH_BAR_BG_COLOR = (80, 88, 96)
HEALTH_BAR_FILL_COLOR = (46, 204, 113)
SHIELD_BAR_COLOR = (100, 180, 255)


@dataclass(frozen=True)
class RectBounds:
    """Simple rectangle bounds used for placement validation.

    We keep this explicit instead of passing around anonymous tuples so later
    contributors can tell what each number means.
    """

    left: float
    top: float
    right: float
    bottom: float
