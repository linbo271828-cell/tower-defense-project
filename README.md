# tower-defense-project
challenge to create tower defense game in half an hour

# Burst Defense — Phase 2

## What I received

A clean Phase 1 tower defense game with one tower type (Dart), three basic enemies, three waves, and a solid project structure. The code was well-organized with good docstrings and a helpful README — made it easy to get oriented quickly.

## What I changed

- Added 5 more tower types: Bomb (area damage), Frost (slows enemies), Sniper (long range + camo detection), Pierce (hits multiple enemies), and Support (buffs nearby towers)
- Added 7 more enemy types with actual traits — camo enemies that most towers can't see, regen enemies that heal, armored ones that resist damage, shielded ones, and a boss
- Enemies now split into smaller enemies when killed (like Bloons — kill a yellow and two greens pop out)
- 4 targeting modes per tower: first, last, strongest, closest
- Frost tower applies a slow debuff on hit
- Support tower has an aura that speeds up nearby towers
- Particle effects for pops and shots
- 15 waves instead of 3, ending with a boss fight
- Game speed toggle (1x/2x/3x), tower selling, tower info panel
- Shop panel on the right with hotkeys 1-6

## What I kept

`main.py`, `path.py`, and `placement.py` are untouched. Everything else I extended rather than replaced — same class structures, same patterns, same variable naming style. Added two new files (`status_effect.py` for debuffs, `particles.py` for visual effects). Well over the 75% retention threshold.

## Challenges

The biggest thing was making the enemy children spawn at the right position along the path when their parent dies, not back at the start. Had to add a `start_progress` parameter and figure out which path segment the child should be on. Also had to be careful about deep-copying mutable dicts (like status effect configs) so towers don't accidentally share state.

## What I'd do with more time

Tower upgrades (two paths per tower), more maps, a pause menu, and better balance tuning. The framework supports all of this already.

## How to run

```
pip install pygame-ce
python main.py
```

## AI tools used

Used Chatgpt for the first section, and moving into phase two used mainly claude with some debugging help from cursor.
