"""Particle system for visual feedback.

Lightweight particle effects for enemy pops, tower shots, and splash impacts.
"""

from __future__ import annotations

import math
import random

import pygame

from burst_defense import settings


class Particle:
    """A single particle with position, velocity, and lifetime."""

    __slots__ = ('x', 'y', 'vx', 'vy', 'lifetime', 'remaining', 'color', 'size', 'start_size', 'gravity')

    def __init__(self, x, y, vx, vy, lifetime, color, size, gravity=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.remaining = lifetime
        self.color = color
        self.size = size
        self.start_size = size
        self.gravity = gravity

    @property
    def alive(self):
        return self.remaining > 0

    def update(self, dt):
        self.remaining -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        t = max(0, self.remaining / self.lifetime)
        self.size = self.start_size * t


class ParticleSystem:
    """Manages a pool of particles with emitter presets."""

    def __init__(self, max_particles: int = settings.MAX_PARTICLES):
        self.particles: list[Particle] = []
        self.max_particles = max_particles

    def emit_pop(self, x: float, y: float, color: tuple, count: int = 8, speed: float = 80):
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed * 0.4, speed)
            size = random.uniform(2, 4.5)
            lifetime = random.uniform(0.2, 0.5)
            r = max(0, min(255, color[0] + random.randint(-20, 20)))
            g = max(0, min(255, color[1] + random.randint(-20, 20)))
            b = max(0, min(255, color[2] + random.randint(-20, 20)))
            self.particles.append(
                Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd, lifetime, (r, g, b), size, 60)
            )

    def emit_shot(self, x: float, y: float, color: tuple, count: int = 3):
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(20, 50)
            size = random.uniform(1.5, 3)
            lifetime = random.uniform(0.1, 0.2)
            self.particles.append(
                Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd, lifetime, color, size)
            )

    def emit_splash(self, x: float, y: float, radius: float, color: tuple, count: int = 10):
        for i in range(count):
            if len(self.particles) >= self.max_particles:
                break
            angle = (2 * math.pi / count) * i + random.uniform(-0.2, 0.2)
            spd = random.uniform(radius * 0.8, radius * 1.5)
            size = random.uniform(2, 4)
            lifetime = random.uniform(0.25, 0.45)
            self.particles.append(
                Particle(x, y, math.cos(angle) * spd, math.sin(angle) * spd, lifetime, color, size, 30)
            )

    def update(self, dt: float):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface: pygame.Surface):
        for p in self.particles:
            if p.size < 0.5:
                continue
            alpha = int(255 * (p.remaining / p.lifetime))
            alpha = max(0, min(255, alpha))
            s = max(2, int(p.size * 2))
            ps = pygame.Surface((s, s), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p.color, alpha), (s // 2, s // 2), max(1, s // 2))
            surface.blit(ps, (int(p.x) - s // 2, int(p.y) - s // 2))

    @property
    def count(self):
        return len(self.particles)
