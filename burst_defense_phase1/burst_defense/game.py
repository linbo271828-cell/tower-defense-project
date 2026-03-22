"""Main game orchestration for Burst Defense.

This file coordinates the current vertical slice while keeping specialized
behavior in dedicated modules. It is intentionally readable rather than
over-generalized.
"""

from __future__ import annotations

import pygame

from burst_defense import settings
from burst_defense.data import ENEMY_DEFINITIONS, MAP_WAYPOINTS, TOWER_DEFINITIONS
from burst_defense.entities.enemy import Enemy
from burst_defense.entities.projectile import Projectile
from burst_defense.entities.tower import Tower
from burst_defense.path import Path
from burst_defense.settings import RectBounds
from burst_defense.systems.placement import validate_tower_placement
from burst_defense.systems.wave_manager import WaveManager
from burst_defense.ui.hud import HudRenderer


class Game:
    """Own the application loop and current gameplay state."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(settings.WINDOW_TITLE)

        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.large_font = pygame.font.SysFont("arial", 28)
        self.small_font = pygame.font.SysFont("arial", 20)
        self.hud = HudRenderer(self.large_font, self.small_font)

        self.path = Path.from_points(MAP_WAYPOINTS, settings.PATH_THICKNESS)
        self.playable_bounds = RectBounds(
            left=settings.PLAY_AREA_PADDING,
            top=settings.TOP_BAR_HEIGHT + settings.PLAY_AREA_PADDING,
            right=settings.SCREEN_WIDTH - settings.RIGHT_PANEL_WIDTH - settings.PLAY_AREA_PADDING,
            bottom=settings.SCREEN_HEIGHT - settings.PLAY_AREA_PADDING,
        )

        self.money = settings.STARTING_MONEY
        self.lives = settings.STARTING_LIVES
        self.towers: list[Tower] = []
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.wave_manager = WaveManager()

        self.placement_mode_enabled = False
        self.status_message = "Press T to enter tower placement mode."
        self.status_message_timer = settings.STATUS_MESSAGE_DURATION_SECONDS
        self.game_over = False
        self.victory = False

    def run(self) -> None:
        """Run the main application loop until the window closes."""

        is_running = True
        while is_running:
            delta_time = self.clock.tick(settings.TARGET_FPS) / 1000.0
            is_running = self._handle_events()
            self._update(delta_time)
            self._draw()

        pygame.quit()

    def _handle_events(self) -> bool:
        """Handle user input and window events."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t and not (self.game_over or self.victory):
                    self.placement_mode_enabled = not self.placement_mode_enabled
                    if self.placement_mode_enabled:
                        self._set_status_message("Placement mode enabled. Left click to place a tower.")
                    else:
                        self._set_status_message("Placement mode cancelled.")

                elif event.key == pygame.K_SPACE and not (self.game_over or self.victory):
                    if self.wave_manager.start_next_wave():
                        self._set_status_message(f"Wave {self.wave_manager.current_wave_number} started.")
                    elif self.wave_manager.wave_in_progress:
                        self._set_status_message("A wave is already in progress.")
                    else:
                        self._set_status_message("No more waves remain in Phase 1.")

                elif event.key == pygame.K_r and (self.game_over or self.victory):
                    # A hard reset is the clearest option for a small project.
                    self.__init__()
                    return True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.placement_mode_enabled and not (self.game_over or self.victory):
                    self._try_place_tower_at_mouse()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.placement_mode_enabled:
                    self.placement_mode_enabled = False
                    self._set_status_message("Placement mode cancelled.")

        return True

    def _update(self, delta_time: float) -> None:
        """Advance the game simulation by one frame."""

        if self.status_message_timer > 0:
            self.status_message_timer = max(0.0, self.status_message_timer - delta_time)
            if self.status_message_timer == 0:
                self.status_message = ""

        if self.game_over or self.victory:
            return

        for enemy_type in self.wave_manager.update(delta_time):
            self.enemies.append(self._create_enemy(enemy_type))

        for enemy in self.enemies:
            leaked = enemy.update(delta_time)
            if leaked:
                self.lives -= enemy.leak_damage
                self._set_status_message(f"A balloon leaked! Lives remaining: {self.lives}")

        for tower in self.towers:
            tower.update(delta_time, self.enemies, self.projectiles)

        for projectile in self.projectiles:
            projectile.update(delta_time)

        self._grant_rewards_for_destroyed_enemies()
        self._remove_inactive_entities()

        if self.lives <= 0:
            self.game_over = True
            self.placement_mode_enabled = False
            self._set_status_message("Game over. Press R to restart.")
            return

        if self.wave_manager.maybe_finish_wave(active_enemy_count=len(self.enemies)):
            if self.wave_manager.has_more_waves():
                self._set_status_message("Wave cleared. Press SPACE for the next wave.")
            else:
                self.victory = True
                self.placement_mode_enabled = False
                self._set_status_message("Phase 1 victory! Press R to play again.")

    def _draw(self) -> None:
        """Render the current frame."""

        self.screen.fill(settings.BACKGROUND_COLOR)
        self._draw_grid()
        self.path.draw(self.screen)

        for tower in self.towers:
            tower.draw(self.screen)

        for projectile in self.projectiles:
            projectile.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        if self.placement_mode_enabled and not (self.game_over or self.victory):
            self._draw_tower_preview()

        wave_text = self._build_wave_text()
        self.hud.draw(
            surface=self.screen,
            money=self.money,
            lives=self.lives,
            wave_text=wave_text,
            placement_mode_enabled=self.placement_mode_enabled,
            status_message=self.status_message,
        )

        if self.game_over:
            self._draw_overlay("Game Over", "Press R to restart.")
        elif self.victory:
            self._draw_overlay("Victory", "Phase 1 complete. Press R to replay.")

        pygame.display.flip()

    def _draw_grid(self) -> None:
        """Draw a subtle grid to improve spatial readability.

        This is mostly a development aid right now, but it also helps players
        judge tower spacing without needing art assets.
        """

        grid_size = 40
        for x in range(0, settings.SCREEN_WIDTH, grid_size):
            pygame.draw.line(self.screen, settings.GRID_COLOR, (x, 0), (x, settings.SCREEN_HEIGHT), 1)
        for y in range(0, settings.SCREEN_HEIGHT, grid_size):
            pygame.draw.line(self.screen, settings.GRID_COLOR, (0, y), (settings.SCREEN_WIDTH, y), 1)

    def _draw_tower_preview(self) -> None:
        """Draw a ghost preview so the player can see range and validity."""

        mouse_position = pygame.Vector2(pygame.mouse.get_pos())
        is_valid, _ = validate_tower_placement(
            center=mouse_position,
            tower_radius=settings.TOWER_RADIUS,
            path=self.path,
            existing_towers=self.towers,
            playable_bounds=self.playable_bounds,
        )
        preview_color = settings.PLACEMENT_OK_COLOR if is_valid else settings.PLACEMENT_BAD_COLOR

        range_surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        body_surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)

        range_alpha = settings.PREVIEW_GOOD_ALPHA if is_valid else settings.PREVIEW_BAD_ALPHA
        pygame.draw.circle(range_surface, (*preview_color, 45), mouse_position, settings.TOWER_RANGE)
        pygame.draw.circle(body_surface, (*preview_color, range_alpha), mouse_position, settings.TOWER_RADIUS)
        pygame.draw.circle(body_surface, (20, 24, 29, range_alpha), mouse_position, settings.TOWER_RADIUS, 2)

        self.screen.blit(range_surface, (0, 0))
        self.screen.blit(body_surface, (0, 0))

    def _draw_overlay(self, title: str, subtitle: str) -> None:
        """Draw a pause-like overlay for end states."""

        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        title_surface = self.large_font.render(title, True, settings.TEXT_COLOR)
        subtitle_surface = self.small_font.render(subtitle, True, settings.TEXT_COLOR)
        title_rect = title_surface.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 20))
        subtitle_rect = subtitle_surface.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(title_surface, title_rect)
        self.screen.blit(subtitle_surface, subtitle_rect)

    def _build_wave_text(self) -> str:
        """Return the top-bar wave label."""

        if self.victory:
            return f"Wave: {self.wave_manager.current_wave_number} / 3"

        if self.wave_manager.wave_in_progress:
            return f"Wave: {self.wave_manager.current_wave_number} / 3 (active)"

        next_wave_number = self.wave_manager.current_wave_number + 1
        if self.wave_manager.has_more_waves():
            return f"Wave: {next_wave_number} / 3 (ready)"
        return "Wave: complete"

    def _try_place_tower_at_mouse(self) -> None:
        """Attempt to place the currently selected tower type."""

        tower_definition = TOWER_DEFINITIONS["dart"]
        if self.money < tower_definition["cost"]:
            self._set_status_message("Not enough money to place a Dart Tower.")
            return

        mouse_position = pygame.Vector2(pygame.mouse.get_pos())
        is_valid, reason = validate_tower_placement(
            center=mouse_position,
            tower_radius=settings.TOWER_RADIUS,
            path=self.path,
            existing_towers=self.towers,
            playable_bounds=self.playable_bounds,
        )
        if not is_valid:
            self._set_status_message(reason)
            return

        tower = Tower(
            tower_type="dart",
            display_name=tower_definition["display_name"],
            position=mouse_position,
            range_radius=tower_definition["range_radius"],
            fire_rate=tower_definition["fire_rate"],
            damage=tower_definition["damage"],
            projectile_speed=tower_definition["projectile_speed"],
            cost=tower_definition["cost"],
        )
        self.towers.append(tower)
        self.money -= tower.cost
        self._set_status_message("Placed a Dart Tower.")

    def _create_enemy(self, enemy_type: str) -> Enemy:
        """Instantiate an enemy using the static data table."""

        definition = ENEMY_DEFINITIONS[enemy_type]
        return Enemy(
            enemy_type=enemy_type,
            display_name=definition["display_name"],
            path=self.path,
            max_health=definition["max_health"],
            speed=definition["speed"],
            reward=definition["reward"],
            leak_damage=definition["leak_damage"],
            color=definition["color"],
        )

    def _grant_rewards_for_destroyed_enemies(self) -> None:
        """Pay the player once for each enemy destroyed this frame."""

        for enemy in self.enemies:
            if not enemy.is_alive and not enemy.has_leaked and not enemy.reward_granted:
                self.money += enemy.reward
                enemy.reward_granted = True

    def _remove_inactive_entities(self) -> None:
        """Delete entities that should no longer be simulated or drawn."""

        # Rewards are handled before this method runs, so at this point we can
        # safely delete anything that died or leaked.
        self.enemies = [enemy for enemy in self.enemies if enemy.is_alive and not enemy.has_leaked]
        self.projectiles = [projectile for projectile in self.projectiles if projectile.is_active]

    def _set_status_message(self, message: str) -> None:
        """Show a short message in the HUD for player feedback."""

        self.status_message = message
        self.status_message_timer = settings.STATUS_MESSAGE_DURATION_SECONDS
