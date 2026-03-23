# Changes Made - Burst Defense Phase 2

This file explains what was changed from Phase 1, what the new work was built on, and what parts of the original project were kept as-is.

## What was built on top of Phase 1

The Phase 2 work was built on the existing Phase 1 gameplay loop and structure:

- Same `main.py` entry flow (`Game().run()`).
- Same core `Game` update/draw loop style.
- Same path/placement foundation.
- Same module layout (`entities`, `systems`, `ui`, `data`, `settings`).

No rewrite was done. New behavior was added to the existing architecture.

## Main changes added in Phase 2

### Towers and combat

- Expanded from 1 tower to 6 towers: Dart, Bomb, Frost, Sniper, Pierce, Support.
- Added tower-specific behavior:
  - Bomb: splash damage.
  - Frost: slow status effect.
  - Pierce: multi-hit projectiles.
  - Support: aura buffs (attack speed + range).
  - Sniper: camo detection and infinite range.
- Added targeting modes for non-support towers:
  - first, last, strong, close.
- Added tower upgrades:
  - Select a tower and press `U` (or click in panel) to increase range.
  - Upgrade cost scales with upgrade level.
- Added selling:
  - `Delete` / `Backspace` sells selected tower for 70% base value, adjusted by upgrade investment.

### Enemies and waves

- Expanded enemy set to 10 types:
  Red, Blue, Green, Yellow, Pink, Camo, Regen, Armored, Shield, Boss.
- Added layered/splitting behavior so stronger enemies spawn child enemies.
- Added traits/resistances systems:
  - Camo visibility checks.
  - Regen healing over time.
  - Shield HP and armored resistance behavior.
- Expanded progression from 3 waves to 15 waves, ending with a boss wave.

### UI and game feedback

- Added right-side tower shop panel with all tower choices.
- Added selected-tower info panel (damage, speed, range, type, targeting, sell value).
- Added in-panel targeting cycling and upgrade interaction.
- Added top-bar speed indicator and status messaging improvements.
- Added particle effects for shooting, pops, and splash impacts.

### Quality of life / controls

- Added game speed toggle (`Tab`: 1x/2x/3x).
- Added restart after win/loss (`R`).
- Added debug money hotkey (`M`) for quick testing.

## What was preserved from Phase 1

The following foundations were intentionally preserved:

- Existing code organization and naming style.
- Dataclass-based entity approach.
- Centralized data-driven definitions in `data.py`.
- Placement validation pattern in `systems/placement.py`.
- Wave scheduling approach in `systems/wave_manager.py`.
- Readability-first coding style (explicit logic over heavy abstraction).

## Notes on newest update (post-Phase-2 pass)

Additional follow-up updates were made after the main Phase 2 feature set:

- Sniper tower range set to true infinite range.
- Tower range upgrade flow added/refined in gameplay + HUD.
- README was simplified to be shorter and more human-readable.
