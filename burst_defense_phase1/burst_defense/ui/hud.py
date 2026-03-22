"""Heads-up display rendering.

This module keeps the immediate-mode UI drawing out of `Game` so the main loop
stays readable.
"""

from __future__ import annotations

import pygame

from burst_defense import settings


class HudRenderer:
    """Draw the top bar, side panel, and short status text."""

    def __init__(self, large_font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        self.large_font = large_font
        self.small_font = small_font

    def draw(
        self,
        surface: pygame.Surface,
        money: int,
        lives: int,
        wave_text: str,
        placement_mode_enabled: bool,
        status_message: str,
    ) -> None:
        """Draw all HUD elements for the current frame."""

        self._draw_top_bar(surface, money, lives, wave_text)
        self._draw_side_panel(surface, placement_mode_enabled)

        if status_message:
            self._draw_status_message(surface, status_message)

    def _draw_top_bar(self, surface: pygame.Surface, money: int, lives: int, wave_text: str) -> None:
        top_bar_rect = pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.TOP_BAR_HEIGHT)
        pygame.draw.rect(surface, settings.PANEL_COLOR, top_bar_rect)
        pygame.draw.line(surface, settings.PANEL_BORDER_COLOR, top_bar_rect.bottomleft, top_bar_rect.bottomright, 2)

        left_text = self.large_font.render(f"Money: ${money}", True, settings.TEXT_COLOR)
        middle_text = self.large_font.render(f"Lives: {lives}", True, settings.TEXT_COLOR)
        right_text = self.large_font.render(wave_text, True, settings.TEXT_COLOR)

        surface.blit(left_text, (24, 24))
        surface.blit(middle_text, (250, 24))
        surface.blit(right_text, (460, 24))

        hint_text = self.small_font.render(
            "T: toggle tower placement    SPACE: start next wave    Right click: cancel placement",
            True,
            settings.SUBTLE_TEXT_COLOR,
        )
        surface.blit(hint_text, (24, 60))

    def _draw_side_panel(self, surface: pygame.Surface, placement_mode_enabled: bool) -> None:
        panel_rect = pygame.Rect(
            settings.SCREEN_WIDTH - settings.RIGHT_PANEL_WIDTH,
            settings.TOP_BAR_HEIGHT,
            settings.RIGHT_PANEL_WIDTH,
            settings.SCREEN_HEIGHT - settings.TOP_BAR_HEIGHT,
        )
        pygame.draw.rect(surface, settings.PANEL_COLOR, panel_rect)
        pygame.draw.line(surface, settings.PANEL_BORDER_COLOR, panel_rect.topleft, panel_rect.bottomleft, 2)

        header = self.large_font.render("Build Menu", True, settings.TEXT_COLOR)
        tower_title = self.small_font.render("Dart Tower", True, settings.TEXT_COLOR)
        tower_cost = self.small_font.render("Cost: $100", True, settings.SUBTLE_TEXT_COLOR)
        tower_stats = self.small_font.render("Role: basic single-target", True, settings.SUBTLE_TEXT_COLOR)
        placement_text = self.small_font.render(
            "Placement: ON" if placement_mode_enabled else "Placement: OFF",
            True,
            settings.PLACEMENT_OK_COLOR if placement_mode_enabled else settings.SUBTLE_TEXT_COLOR,
        )

        surface.blit(header, (panel_rect.left + 24, panel_rect.top + 24))
        surface.blit(tower_title, (panel_rect.left + 24, panel_rect.top + 90))
        surface.blit(tower_cost, (panel_rect.left + 24, panel_rect.top + 120))
        surface.blit(tower_stats, (panel_rect.left + 24, panel_rect.top + 150))
        surface.blit(placement_text, (panel_rect.left + 24, panel_rect.top + 195))

        notes = [
            "Phase 1 focuses on readable architecture.",
            "Towers cannot overlap the path or each other.",
            "Later phases should add upgrades, targeting",
            "modes, special enemies, particles, and saves.",
        ]
        current_y = panel_rect.top + 270
        for note in notes:
            note_surface = self.small_font.render(note, True, settings.SUBTLE_TEXT_COLOR)
            surface.blit(note_surface, (panel_rect.left + 24, current_y))
            current_y += 28

    def _draw_status_message(self, surface: pygame.Surface, message: str) -> None:
        text_surface = self.small_font.render(message, True, settings.TEXT_COLOR)
        text_rect = text_surface.get_rect()
        text_rect.centerx = (settings.SCREEN_WIDTH - settings.RIGHT_PANEL_WIDTH) // 2
        text_rect.top = settings.SCREEN_HEIGHT - 42
        surface.blit(text_surface, text_rect)
