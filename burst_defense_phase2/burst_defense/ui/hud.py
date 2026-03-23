"""Heads-up display rendering.

This module keeps the immediate-mode UI drawing out of `Game` so the main loop
stays readable.

Phase 2 extends the HUD with a multi-tower shop, selected tower info panel,
targeting mode display, and game speed indicator.
"""

from __future__ import annotations

import pygame

from burst_defense import settings
from burst_defense.data import TOWER_DEFINITIONS, TOWER_ORDER, TARGETING_MODES


class HudRenderer:
    """Draw the top bar, side panel, and short status text."""

    def __init__(self, large_font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        self.large_font = large_font
        self.small_font = small_font
        self.tiny_font = pygame.font.SysFont("arial", 15)

    def draw(
        self,
        surface: pygame.Surface,
        money: int,
        lives: int,
        wave_text: str,
        placement_mode_enabled: bool,
        status_message: str,
        selected_tower=None,
        selected_tower_type: str | None = None,
        game_speed: float = 1.0,
    ) -> None:
        """Draw all HUD elements for the current frame."""

        self._draw_top_bar(surface, money, lives, wave_text, game_speed)
        self._draw_side_panel(surface, money, placement_mode_enabled, selected_tower_type)

        if selected_tower is not None:
            self._draw_tower_info(surface, selected_tower)

        if status_message:
            self._draw_status_message(surface, status_message)

    def _draw_top_bar(self, surface: pygame.Surface, money: int, lives: int, wave_text: str, game_speed: float) -> None:
        top_bar_rect = pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.TOP_BAR_HEIGHT)
        pygame.draw.rect(surface, settings.PANEL_COLOR, top_bar_rect)
        pygame.draw.line(surface, settings.PANEL_BORDER_COLOR, top_bar_rect.bottomleft, top_bar_rect.bottomright, 2)

        left_text = self.large_font.render(f"Money: ${money}", True, settings.TEXT_COLOR)
        middle_text = self.large_font.render(f"Lives: {lives}", True, settings.TEXT_COLOR)
        right_text = self.large_font.render(wave_text, True, settings.TEXT_COLOR)

        surface.blit(left_text, (24, 24))
        surface.blit(middle_text, (250, 24))
        surface.blit(right_text, (460, 24))

        # Speed indicator
        speed_color = (255, 200, 80) if game_speed != 1.0 else settings.SUBTLE_TEXT_COLOR
        speed_text = self.small_font.render(f"{game_speed:.0f}x [Tab]", True, speed_color)
        surface.blit(speed_text, (780, 28))

        hint_text = self.small_font.render(
            "1-6: select tower   SPACE: next wave   U: upgrade   RMB: cancel   Tab: speed",
            True,
            settings.SUBTLE_TEXT_COLOR,
        )
        surface.blit(hint_text, (24, 64))

    def _draw_side_panel(self, surface: pygame.Surface, money: int, placement_mode_enabled: bool, selected_tower_type: str | None) -> None:
        panel_rect = pygame.Rect(
            settings.SCREEN_WIDTH - settings.RIGHT_PANEL_WIDTH,
            settings.TOP_BAR_HEIGHT,
            settings.RIGHT_PANEL_WIDTH,
            settings.SCREEN_HEIGHT - settings.TOP_BAR_HEIGHT,
        )
        pygame.draw.rect(surface, settings.PANEL_COLOR, panel_rect)
        pygame.draw.line(surface, settings.PANEL_BORDER_COLOR, panel_rect.topleft, panel_rect.bottomleft, 2)

        header = self.large_font.render("Build Menu", True, settings.TEXT_COLOR)
        surface.blit(header, (panel_rect.left + 20, panel_rect.top + 16))

        # Tower shop buttons
        y = panel_rect.top + 60
        for i, tower_key in enumerate(TOWER_ORDER):
            tdef = TOWER_DEFINITIONS[tower_key]
            cost = tdef["cost"]
            can_afford = money >= cost
            is_selected = selected_tower_type == tower_key

            # Button background
            btn_rect = pygame.Rect(panel_rect.left + 10, y, settings.RIGHT_PANEL_WIDTH - 20, 48)
            if is_selected:
                bg_color = (50, 65, 50)
            elif can_afford:
                bg_color = (35, 40, 48)
            else:
                bg_color = (28, 30, 35)

            pygame.draw.rect(surface, bg_color, btn_rect, border_radius=5)
            if is_selected:
                pygame.draw.rect(surface, settings.PLACEMENT_OK_COLOR, btn_rect, 1, border_radius=5)
            elif can_afford:
                pygame.draw.rect(surface, settings.PANEL_BORDER_COLOR, btn_rect, 1, border_radius=5)

            # Color swatch
            swatch_rect = pygame.Rect(btn_rect.left + 6, btn_rect.top + 6, 10, btn_rect.height - 12)
            pygame.draw.rect(surface, tdef.get("color", (160, 160, 170)), swatch_rect, border_radius=2)

            # Hotkey + name
            hotkey = str(i + 1)
            name_text = self.small_font.render(f"[{hotkey}] {tdef['display_name']}", True, settings.TEXT_COLOR if can_afford else settings.SUBTLE_TEXT_COLOR)
            surface.blit(name_text, (btn_rect.left + 22, btn_rect.top + 4))

            # Cost + description
            cost_color = (100, 220, 100) if can_afford else (200, 80, 80)
            cost_text = self.tiny_font.render(f"${cost}  -  {tdef.get('description', '')}", True, cost_color if can_afford else settings.SUBTLE_TEXT_COLOR)
            surface.blit(cost_text, (btn_rect.left + 22, btn_rect.top + 28))

            y += 54

    def _draw_tower_info(self, surface: pygame.Surface, tower) -> None:
        """Draw stats for the selected placed tower in the lower right panel."""
        panel_x = settings.SCREEN_WIDTH - settings.RIGHT_PANEL_WIDTH
        y = settings.SCREEN_HEIGHT - 210

        # Separator
        pygame.draw.line(surface, settings.PANEL_BORDER_COLOR, (panel_x + 10, y), (panel_x + settings.RIGHT_PANEL_WIDTH - 10, y), 1)
        y += 10

        # Tower name with color
        pygame.draw.rect(surface, tower.color, (panel_x + 14, y + 2, 10, 10), border_radius=2)
        name_text = self.small_font.render(tower.display_name, True, settings.TEXT_COLOR)
        surface.blit(name_text, (panel_x + 30, y))
        y += 24

        if tower.is_support:
            info_text = self.tiny_font.render("Support - buffs nearby towers", True, settings.SUBTLE_TEXT_COLOR)
            surface.blit(info_text, (panel_x + 14, y))
            y += 18
            if tower.aura_config:
                aura = tower.aura_config
                if aura.get("attack_speed_bonus"):
                    t = self.tiny_font.render(f"Atk Speed: +{aura['attack_speed_bonus']*100:.0f}%", True, (180, 160, 230))
                    surface.blit(t, (panel_x + 14, y))
                    y += 16
        else:
            range_text = "INF" if tower.has_infinite_range() else f"{tower.range_radius:.0f}"
            stats = [
                f"Dmg: {tower.damage}  Spd: {tower.fire_rate:.2f}/s",
                f"Range: {range_text}  Type: {tower.damage_type}",
            ]
            if tower.pierce > 1:
                stats.append(f"Pierce: {tower.pierce}")
            if tower.splash_radius > 0:
                stats.append(f"Splash: {tower.splash_radius:.0f}")
            if tower.status_on_hit:
                stats.append(f"Effect: {tower.status_on_hit['type']}")
            if tower.can_see_camo:
                stats.append("Sees camo")

            for line in stats:
                t = self.tiny_font.render(line, True, settings.SUBTLE_TEXT_COLOR)
                surface.blit(t, (panel_x + 14, y))
                y += 16

        # Upgrade action
        upgrade_cost = tower.get_upgrade_cost()
        if upgrade_cost is None:
            upgrade_text = "Upgrade: max range reached"
            upgrade_color = settings.SUBTLE_TEXT_COLOR
        else:
            upgrade_text = f"Upgrade range: ${upgrade_cost} [U/click]"
            upgrade_color = (130, 230, 150)
        t = self.tiny_font.render(upgrade_text, True, upgrade_color)
        surface.blit(t, (panel_x + 14, y))
        y += 18

        # Targeting mode
        if not tower.is_support:
            y += 4
            mode_text = self.tiny_font.render(f"Target: {tower.targeting_mode} [click to cycle]", True, (140, 200, 180))
            surface.blit(mode_text, (panel_x + 14, y))
            y += 18

        # Sell value
        sell_text = self.tiny_font.render(f"Sell: ${tower.sell_value}", True, (180, 140, 100))
        surface.blit(sell_text, (panel_x + 14, y))
        y += 18

        # Buff status
        if tower.buffed_by:
            buff_text = self.tiny_font.render(f"Buffed x{len(tower.buffed_by)}", True, (200, 180, 255))
            surface.blit(buff_text, (panel_x + 14, y))

    def _draw_status_message(self, surface: pygame.Surface, message: str) -> None:
        text_surface = self.small_font.render(message, True, settings.TEXT_COLOR)
        text_rect = text_surface.get_rect()
        text_rect.centerx = (settings.SCREEN_WIDTH - settings.RIGHT_PANEL_WIDTH) // 2
        text_rect.top = settings.SCREEN_HEIGHT - 42
        surface.blit(text_surface, text_rect)

    def get_tower_at_panel_click(self, mouse_pos: tuple[int, int]) -> str | None:
        """Check if a tower shop button was clicked, return tower key or None."""
        panel_x = settings.SCREEN_WIDTH - settings.RIGHT_PANEL_WIDTH
        if mouse_pos[0] < panel_x:
            return None

        y = settings.TOP_BAR_HEIGHT + 60
        for tower_key in TOWER_ORDER:
            btn_rect = pygame.Rect(panel_x + 10, y, settings.RIGHT_PANEL_WIDTH - 20, 48)
            if btn_rect.collidepoint(mouse_pos):
                return tower_key
            y += 54
        return None

    def is_in_panel(self, mouse_pos: tuple[int, int]) -> bool:
        """Check if mouse is in the right panel area."""
        return mouse_pos[0] >= settings.SCREEN_WIDTH - settings.RIGHT_PANEL_WIDTH
