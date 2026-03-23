"""Main game orchestration for Burst Defense.

This file coordinates the current vertical slice while keeping specialized
behavior in dedicated modules. It is intentionally readable rather than
over-generalized.

Phase 2 adds: multi-tower selection, tower info panel, sell/targeting,
layered enemy children, splash/pierce combat, support tower auras,
particle effects, game speed control, and 15 waves.
"""

from __future__ import annotations

import copy

import pygame

from burst_defense import settings
from burst_defense.data import ENEMY_DEFINITIONS, MAP_WAYPOINTS, TOWER_DEFINITIONS, TOWER_ORDER
from burst_defense.entities.enemy import Enemy
from burst_defense.entities.projectile import Projectile
from burst_defense.entities.tower import Tower
from burst_defense.effects.particles import ParticleSystem
from burst_defense.path import Path
from burst_defense.settings import RectBounds
from burst_defense.systems.placement import validate_tower_placement
from burst_defense.systems.wave_manager import WaveManager
from burst_defense.ui.hud import HudRenderer

# Hotkey map: pygame key -> tower_type
TOWER_HOTKEYS = {
    pygame.K_1: "dart",
    pygame.K_2: "bomb",
    pygame.K_3: "frost",
    pygame.K_4: "sniper",
    pygame.K_5: "pierce",
    pygame.K_6: "support",
}


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
        self.particles = ParticleSystem()

        self.placement_mode_enabled = False
        self.selected_tower_type: str | None = None
        self.selected_tower: Tower | None = None  # a placed tower the player clicked on
        self.game_speed = 1.0
        self.status_message = "Press 1-6 to select a tower, then click to place."
        self.status_message_timer = settings.STATUS_MESSAGE_DURATION_SECONDS
        self.game_over = False
        self.victory = False

    def run(self) -> None:
        """Run the main application loop until the window closes."""

        is_running = True
        while is_running:
            delta_time = self.clock.tick(settings.TARGET_FPS) / 1000.0
            delta_time = min(delta_time, 0.05)
            is_running = self._handle_events()
            self._update(delta_time * self.game_speed)
            self._draw()

        pygame.quit()

    def _handle_events(self) -> bool:
        """Handle user input and window events."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and (self.game_over or self.victory):
                    # A hard reset is the clearest option for a small project.
                    self.__init__()
                    return True

                if self.game_over or self.victory:
                    continue

                # Tower hotkeys (1-6)
                if event.key in TOWER_HOTKEYS:
                    tower_type = TOWER_HOTKEYS[event.key]
                    self._select_tower_type(tower_type)

                elif event.key == pygame.K_t:
                    # Legacy toggle — if a type is selected, toggle placement
                    if self.placement_mode_enabled:
                        self._cancel_placement()
                    elif self.selected_tower_type:
                        self.placement_mode_enabled = True

                elif event.key == pygame.K_SPACE:
                    if self.wave_manager.start_next_wave():
                        self._set_status_message(f"Wave {self.wave_manager.current_wave_number} started.")
                    elif self.wave_manager.wave_in_progress:
                        self._set_status_message("A wave is already in progress.")
                    else:
                        self._set_status_message("All waves complete!")

                elif event.key == pygame.K_ESCAPE:
                    if self.placement_mode_enabled:
                        self._cancel_placement()
                    elif self.selected_tower:
                        self._deselect_placed_tower()

                elif event.key == pygame.K_TAB:
                    speeds = settings.SPEED_OPTIONS
                    idx = speeds.index(self.game_speed) if self.game_speed in speeds else 0
                    self.game_speed = speeds[(idx + 1) % len(speeds)]

                elif event.key == pygame.K_m:
                    self.money += 500
                    self._set_status_message("Debug: +$500")

                elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                    if self.selected_tower:
                        self._sell_selected_tower()

                elif event.key == pygame.K_u:
                    self._upgrade_selected_tower()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not (self.game_over or self.victory):
                    self._handle_left_click(pygame.mouse.get_pos())

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.placement_mode_enabled:
                    self._cancel_placement()
                elif self.selected_tower:
                    self._deselect_placed_tower()

        return True

    def _handle_left_click(self, mouse_pos: tuple[int, int]) -> None:
        """Process left click — panel, placement, or tower selection."""

        # Check if clicking in the panel
        if self.hud.is_in_panel(mouse_pos):
            # Check tower shop buttons
            tower_key = self.hud.get_tower_at_panel_click(mouse_pos)
            if tower_key:
                self._select_tower_type(tower_key)
                return

            # Check if clicking the targeting mode area of a selected tower
            if self.selected_tower and self._upgrade_area_rect().collidepoint(mouse_pos):
                self._upgrade_selected_tower()
                return

            # Check if clicking the targeting mode area of a selected tower
            if self.selected_tower and not self.selected_tower.is_support:
                panel_x = settings.SCREEN_WIDTH - settings.RIGHT_PANEL_WIDTH
                target_area = pygame.Rect(panel_x + 14, settings.SCREEN_HEIGHT - 68, 200, 20)
                if target_area.collidepoint(mouse_pos):
                    self.selected_tower.cycle_targeting_mode()
                    self._set_status_message(f"Targeting: {self.selected_tower.targeting_mode}")
                    return
            return

        # Placement mode
        if self.placement_mode_enabled:
            self._try_place_tower_at_mouse()
            return

        # Try selecting a placed tower
        mouse_vec = pygame.Vector2(mouse_pos)
        for tower in self.towers:
            if mouse_vec.distance_to(tower.position) <= tower.body_radius + 4:
                self._select_placed_tower(tower)
                return

        # Clicked empty space
        self._deselect_placed_tower()

    def _select_tower_type(self, tower_type: str) -> None:
        """Select a tower type from the shop for placement."""
        self._deselect_placed_tower()
        self.selected_tower_type = tower_type
        self.placement_mode_enabled = True
        tdef = TOWER_DEFINITIONS[tower_type]
        self._set_status_message(f"Placing {tdef['display_name']}. Click to place, RMB to cancel.")

    def _cancel_placement(self) -> None:
        self.placement_mode_enabled = False
        self._set_status_message("Placement cancelled.")

    def _select_placed_tower(self, tower: Tower) -> None:
        if self.selected_tower:
            self.selected_tower.selected = False
        self.selected_tower = tower
        tower.selected = True
        self.placement_mode_enabled = False

    def _deselect_placed_tower(self) -> None:
        if self.selected_tower:
            self.selected_tower.selected = False
            self.selected_tower = None

    def _sell_selected_tower(self) -> None:
        if not self.selected_tower:
            return
        self.money += self.selected_tower.sell_value
        self.towers.remove(self.selected_tower)
        self._set_status_message(f"Sold {self.selected_tower.display_name} for ${self.selected_tower.sell_value}.")
        self.selected_tower = None

    def _upgrade_selected_tower(self) -> None:
        """Upgrade selected tower to increase its base range."""
        if not self.selected_tower:
            self._set_status_message("Select a tower to upgrade.")
            return

        upgrade_cost = self.selected_tower.get_upgrade_cost()
        if upgrade_cost is None:
            self._set_status_message(f"{self.selected_tower.display_name} already has infinite range.")
            return

        if self.money < upgrade_cost:
            self._set_status_message(f"Need ${upgrade_cost} to upgrade {self.selected_tower.display_name}.")
            return

        if self.selected_tower.upgrade_range():
            self.money -= upgrade_cost
            self._set_status_message(
                f"Upgraded {self.selected_tower.display_name} range to Lv{self.selected_tower.upgrade_level}."
            )

    def _upgrade_area_rect(self) -> pygame.Rect:
        panel_x = settings.SCREEN_WIDTH - settings.RIGHT_PANEL_WIDTH
        return pygame.Rect(panel_x + 14, settings.SCREEN_HEIGHT - 90, 240, 20)

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

        # Apply support tower auras
        self._update_auras()

        for tower in self.towers:
            tower.update(delta_time, self.enemies, self.projectiles)
            if tower.fired_this_frame:
                self.particles.emit_shot(tower.position.x, tower.position.y, tower.color)

        for projectile in self.projectiles:
            projectile.update(delta_time)
            # Check pierce hits against other enemies
            if projectile.is_active and projectile.pierce_remaining > 0:
                projectile.check_pierce_hit(self.enemies)

        # Handle splash damage from projectiles that just hit
        self._process_splash_damage()

        self._grant_rewards_and_spawn_children()
        self._remove_inactive_entities()

        self.particles.update(delta_time)

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
                self._set_status_message("Victory! All waves cleared! Press R to play again.")

    def _update_auras(self) -> None:
        """Apply support tower buffs to nearby towers."""
        support_towers = [t for t in self.towers if t.is_support and t.aura_config]
        support_ids = {id(t) for t in support_towers}

        # Clean stale buffs
        for tower in self.towers:
            if tower.is_support:
                continue
            stale = tower.buffed_by - support_ids
            for sid in stale:
                tower.buffed_by.discard(sid)

        for sup in support_towers:
            aura = sup.aura_config
            as_bonus = aura.get("attack_speed_bonus", 0)
            r_bonus = aura.get("range_bonus", 0)

            for tower in self.towers:
                if id(tower) == id(sup) or tower.is_support:
                    continue
                dist = sup.position.distance_to(tower.position)
                if dist <= sup.range_radius:
                    tower.apply_buff(id(sup), as_bonus, r_bonus)
                else:
                    tower.remove_buff(id(sup), as_bonus, r_bonus)

    def _process_splash_damage(self) -> None:
        """Deal splash damage for projectiles that have splash_radius > 0 and just deactivated."""
        for proj in self.projectiles:
            if proj.splash_radius > 0 and not proj.is_active and proj.hit_enemies:
                # Splash at the projectile's last position
                for enemy in self.enemies:
                    if not enemy.is_alive or enemy.has_leaked:
                        continue
                    if id(enemy) in proj.hit_enemies:
                        continue
                    if proj.position.distance_to(enemy.position) <= proj.splash_radius:
                        enemy.take_damage(proj.damage, proj.damage_type)
                        if proj.status_on_hit and enemy.is_alive:
                            from burst_defense.entities.status_effect import StatusEffect
                            effect = StatusEffect(
                                effect_type=proj.status_on_hit["type"],
                                duration=proj.status_on_hit["duration"],
                                magnitude=proj.status_on_hit.get("magnitude", 0.5),
                                source_id=proj.source_tower_id,
                            )
                            enemy.apply_status_effect(effect)

                self.particles.emit_splash(
                    proj.position.x, proj.position.y,
                    proj.splash_radius, proj.color, count=8,
                )

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

        self.particles.draw(self.screen)

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
            selected_tower=self.selected_tower,
            selected_tower_type=self.selected_tower_type,
            game_speed=self.game_speed,
        )

        if self.game_over:
            self._draw_overlay("Game Over", "Press R to restart.")
        elif self.victory:
            self._draw_overlay("Victory", "All waves cleared! Press R to replay.")

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

        if not self.selected_tower_type:
            return

        tower_definition = TOWER_DEFINITIONS[self.selected_tower_type]
        tower_range = tower_definition["range_radius"]
        tower_color = tower_definition.get("color", settings.TOWER_BODY_COLOR)

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
        if tower_range != float("inf"):
            pygame.draw.circle(range_surface, (*preview_color, 45), mouse_position, tower_range)
        pygame.draw.circle(body_surface, (*tower_color, range_alpha), mouse_position, settings.TOWER_RADIUS)
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

        total = self.wave_manager.total_waves

        if self.victory:
            return f"Wave: {self.wave_manager.current_wave_number} / {total}"

        if self.wave_manager.wave_in_progress:
            return f"Wave: {self.wave_manager.current_wave_number} / {total} (active)"

        next_wave_number = self.wave_manager.current_wave_number + 1
        if self.wave_manager.has_more_waves():
            return f"Wave: {next_wave_number} / {total} (ready)"
        return "Wave: complete"

    def _try_place_tower_at_mouse(self) -> None:
        """Attempt to place the currently selected tower type."""

        if not self.selected_tower_type:
            self._set_status_message("No tower type selected. Press 1-6.")
            return

        tower_definition = TOWER_DEFINITIONS[self.selected_tower_type]
        if self.money < tower_definition["cost"]:
            self._set_status_message(f"Not enough money for {tower_definition['display_name']}.")
            return

        mouse_position = pygame.Vector2(pygame.mouse.get_pos())

        # Don't place if clicking in the panel area
        if self.hud.is_in_panel(pygame.mouse.get_pos()):
            return

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

        # Deep copy status_on_hit and aura to avoid shared mutation
        status = copy.deepcopy(tower_definition.get("status_on_hit"))
        aura = copy.deepcopy(tower_definition.get("aura"))

        tower = Tower(
            tower_type=self.selected_tower_type,
            display_name=tower_definition["display_name"],
            position=mouse_position,
            range_radius=tower_definition["range_radius"],
            fire_rate=tower_definition["fire_rate"],
            damage=tower_definition["damage"],
            projectile_speed=tower_definition["projectile_speed"],
            cost=tower_definition["cost"],
            color=tower_definition.get("color", settings.TOWER_BODY_COLOR),
            attack_type=tower_definition.get("attack_type", "single"),
            damage_type=tower_definition.get("damage_type", "sharp"),
            pierce=tower_definition.get("pierce", 1),
            splash_radius=tower_definition.get("splash_radius", 0),
            status_on_hit=status,
            can_see_camo=tower_definition.get("can_see_camo", False),
            is_support=tower_definition.get("attack_type") == "support",
            aura_config=aura,
        )
        self.towers.append(tower)
        self.money -= tower.cost
        self._set_status_message(f"Placed a {tower.display_name}.")

    def _create_enemy(self, enemy_type: str, start_progress: float = 0.0) -> Enemy:
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
            traits=set(definition.get("traits", [])),
            children_spec=definition.get("children") or [],
            shield_hp=definition.get("shield_hp", 0),
            regen_rate=definition.get("regen_rate", 0.0),
            resistances=dict(definition.get("resistances", {})),
            start_progress=start_progress,
        )

    def _grant_rewards_and_spawn_children(self) -> None:
        """Pay the player and spawn children for each enemy destroyed this frame."""

        children_to_spawn: list[tuple[str, float]] = []

        for enemy in self.enemies:
            if not enemy.is_alive and not enemy.has_leaked and not enemy.reward_granted:
                self.money += enemy.reward
                enemy.reward_granted = True

                # Particle pop effect
                size_factor = max(4, int(enemy.radius * 0.6))
                self.particles.emit_pop(
                    enemy.position.x, enemy.position.y, enemy.color,
                    count=size_factor, speed=60 + enemy.radius * 2,
                )

                # Queue child spawns
                for child_def in enemy.children_spec:
                    for _ in range(child_def["count"]):
                        children_to_spawn.append((child_def["type"], enemy.distance_travelled))

        # Spawn children after iteration to avoid mutating during loop
        for child_type, progress in children_to_spawn:
            child = self._create_enemy(child_type, start_progress=progress)
            self.enemies.append(child)

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
