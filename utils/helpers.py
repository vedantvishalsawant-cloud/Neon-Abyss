"""
utils/helpers.py – Utility functions used across the game.
Includes procedural asset generation so the game runs without external image files.
"""

import pygame
import math
import random
from settings import *


# ─── Procedural sprite generators ─────────────────────────────────────────────

def make_player_surf(w=PLAYER_WIDTH, h=PLAYER_HEIGHT, color=C_PLAYER, color2=C_PLAYER_2):
    """Generate a crisp pixel-art player surface with glow effect."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # Body
    pygame.draw.rect(surf, color2, (4, 10, w-8, h-10), border_radius=4)
    pygame.draw.rect(surf, color,  (6, 12, w-12, h-14), border_radius=3)
    # Visor
    pygame.draw.rect(surf, (30, 200, 255), (8, 13, w-16, 10), border_radius=2)
    pygame.draw.rect(surf, (180, 240, 255, 180), (9, 14, 6, 4))
    # Legs
    pygame.draw.rect(surf, color2, (6, h-14, 8, 14), border_radius=2)
    pygame.draw.rect(surf, color2, (w-14, h-14, 8, 14), border_radius=2)
    # Glow outline
    pygame.draw.rect(surf, (*color, 120), (3, 9, w-6, h-9), 1, border_radius=4)
    return surf


def make_enemy_surf(etype=1, w=32, h=36):
    """Generate enemy surfaces for each type."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if etype == 1:   # Patrol – red brute
        col = C_ENEMY_1; col2 = (180, 40, 40)
        pygame.draw.rect(surf, col2, (2, 8, w-4, h-8), border_radius=3)
        pygame.draw.rect(surf, col,  (4, 10, w-8, h-12), border_radius=2)
        # Eye slots
        pygame.draw.rect(surf, (255,200,50), (6, 12, 6, 5))
        pygame.draw.rect(surf, (255,200,50), (w-12, 12, 6, 5))
    elif etype == 2: # Chaser – orange speeder
        col = C_ENEMY_2; col2 = (180, 100, 20)
        pygame.draw.ellipse(surf, col2, (2, 6, w-4, h-6))
        pygame.draw.ellipse(surf, col,  (4, 8, w-8, h-10))
        pygame.draw.ellipse(surf, (255,255,100), (8, 10, 8, 8))
    else:            # Ranged – purple sniper
        col = C_ENEMY_3; col2 = (140, 30, 180)
        pygame.draw.polygon(surf, col2, [(w//2,2),(w-2,h-4),(2,h-4)])
        pygame.draw.polygon(surf, col,  [(w//2,6),(w-6,h-6),(6,h-6)])
        pygame.draw.circle(surf, (255,180,255), (w//2, h//2+2), 5)
    pygame.draw.rect(surf, (*col, 100), (1,1,w-2,h-2), 1, border_radius=3)
    return surf


def make_platform_surf(w, h, moving=False):
    """Generate a glowing platform surface."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    col = C_MOVING_PLAT if moving else C_PLATFORM
    edge = (100, 160, 255) if moving else C_PLAT_EDGE
    pygame.draw.rect(surf, col, (0, 0, w, h), border_radius=4)
    # Top glow strip
    pygame.draw.rect(surf, edge, (0, 0, w, 4), border_radius=2)
    # Side lines
    for x in range(0, w, 20):
        pygame.draw.line(surf, (*edge, 40), (x, 4), (x, h-2))
    pygame.draw.rect(surf, (*edge, 180), (0, 0, w, h), 1, border_radius=4)
    return surf


def make_battery_surf(w=20, h=32):
    """Glowing battery collectible."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    col = C_BATTERY
    # Body
    pygame.draw.rect(surf, (20, 80, 50), (2, 6, w-4, h-8), border_radius=3)
    pygame.draw.rect(surf, col, (4, 8, w-8, h-12), border_radius=2)
    # Terminal
    pygame.draw.rect(surf, col, (w//2-4, 2, 8, 6), border_radius=1)
    # Charge bars
    bar_h = (h-16)//3
    for i in range(3):
        alpha = 255 - i*60
        pygame.draw.rect(surf, (*col, alpha), (6, 10+i*(bar_h+2), w-12, bar_h-1), border_radius=1)
    return surf


def make_spike_surf(w=TILE, h=24, count=3):
    """Spike hazard surface."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    sw = w // count
    for i in range(count):
        x = i * sw
        pts = [(x+2, h), (x+sw//2, 2), (x+sw-2, h)]
        pygame.draw.polygon(surf, C_SPIKE, pts)
        pygame.draw.polygon(surf, (255,255,255,100), pts, 1)
    return surf


def make_acid_surf(w, h=24):
    """Animated acid pool surface."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (20, 120, 20), (0, 0, w, h))
    pygame.draw.rect(surf, C_ACID, (0, 0, w, 6))
    for x in range(0, w, 16):
        pygame.draw.ellipse(surf, (*C_ACID, 160), (x, 2, 14, 8))
    return surf


def make_bullet_surf(r=5, color=C_BULLET):
    surf = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (r+2, r+2), r)
    pygame.draw.circle(surf, C_WHITE, (r+2, r+2), r, 1)
    return surf


def make_heart_surf(full=True, size=24):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    col = C_HEART_FULL if full else C_HEART_EMPTY
    cx, cy = size//2, size//2
    r = size//4
    pygame.draw.circle(surf, col, (cx-r+1, cy-2), r)
    pygame.draw.circle(surf, col, (cx+r-1, cy-2), r)
    pts = [(2, cy), (cx, size-4), (size-2, cy)]
    pygame.draw.polygon(surf, col, pts)
    if full:
        pygame.draw.circle(surf, (*col, 100), (cx, cy), r+2, 2)
    return surf


def make_checkpoint_surf(w=28, h=48):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (80, 60, 0), (w//2-3, 8, 6, h-8))
    pygame.draw.rect(surf, C_CHECKPOINT, (w//2-3, 8, 6, h-10), 1)
    pygame.draw.polygon(surf, C_CHECKPOINT, [(w//2-2, 8),(w-4, 20),(w//2-2, 32)])
    return surf


def make_boss_surf(phase=1):
    w, h = 80, 90
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if phase == 1:
        body_col = C_BOSS; accent = (255,130,160)
    elif phase == 2:
        body_col = C_BOSS_2; accent = (255,200,80)
    else:
        body_col = (200, 0, 255); accent = (255, 50, 255)

    # Core body
    pygame.draw.rect(surf, (body_col[0]//3, body_col[1]//3, body_col[2]//3),
                     (8, 16, w-16, h-20), border_radius=8)
    pygame.draw.rect(surf, body_col, (12, 20, w-24, h-28), border_radius=6)
    # Face / visor
    pygame.draw.rect(surf, (10, 10, 30), (18, 24, w-36, 22), border_radius=4)
    pygame.draw.rect(surf, accent, (18, 24, w-36, 22), 2, border_radius=4)
    # Eyes
    pygame.draw.circle(surf, accent, (28, 35), 6)
    pygame.draw.circle(surf, accent, (w-28, 35), 6)
    pygame.draw.circle(surf, C_WHITE, (28, 35), 3)
    pygame.draw.circle(surf, C_WHITE, (w-28, 35), 3)
    # Shoulder pads
    pygame.draw.rect(surf, accent, (2, 22, 12, 20), border_radius=3)
    pygame.draw.rect(surf, accent, (w-14, 22, 12, 20), border_radius=3)
    # Glow border
    pygame.draw.rect(surf, (*accent, 140), (8, 16, w-16, h-20), 2, border_radius=8)
    return surf


# ─── Particle system ──────────────────────────────────────────────────────────

class Particle:
    __slots__ = ['x','y','vx','vy','life','max_life','color','radius']
    def __init__(self, x, y, vx, vy, life, color, radius=3):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.radius = radius

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.vx *= 0.96
        self.life -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        alpha = int(255 * (self.life / self.max_life))
        r = max(1, int(self.radius * (self.life / self.max_life)))
        col = (*self.color[:3], alpha)
        s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, col, (r+1, r+1), r)
        surface.blit(s, (self.x - offset_x - r - 1, self.y - offset_y - r - 1))

    @property
    def dead(self):
        return self.life <= 0


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=8, speed=3.0, radius=3, life=30):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(0.5, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            lf = int(life * random.uniform(0.6, 1.4))
            self.particles.append(Particle(x, y, vx, vy, lf, color, radius))

    def emit_burst(self, x, y, color, direction_x=0, direction_y=-1, count=12, speed=4.0):
        """Directional burst (e.g., landing dust)."""
        for _ in range(count):
            spread = random.uniform(-1.2, 1.2)
            spd = random.uniform(1, speed)
            vx = direction_x * spd + spread
            vy = direction_y * spd + spread * 0.3
            lf = random.randint(15, 35)
            self.particles.append(Particle(x, y, vx, vy, lf, color, random.randint(2,4)))

    def update(self):
        self.particles = [p for p in self.particles if not p.dead]
        for p in self.particles:
            p.update()

    def draw(self, surface, cam_x=0, cam_y=0):
        for p in self.particles:
            p.draw(surface, cam_x, cam_y)

    def clear(self):
        self.particles.clear()


# ─── Screen shake ─────────────────────────────────────────────────────────────

class ScreenShake:
    def __init__(self):
        self.intensity = 0
        self.duration  = 0

    def shake(self, intensity=6, duration=12):
        self.intensity = max(self.intensity, intensity)
        self.duration  = max(self.duration,  duration)

    def update(self):
        if self.duration > 0:
            self.duration -= 1
            if self.duration == 0:
                self.intensity = 0

    @property
    def offset(self):
        if self.duration > 0:
            return (random.randint(-self.intensity, self.intensity),
                    random.randint(-self.intensity, self.intensity))
        return (0, 0)


# ─── Flash overlay ────────────────────────────────────────────────────────────

class FlashOverlay:
    def __init__(self):
        self.alpha    = 0
        self.color    = C_WHITE
        self.fade_spd = 12

    def flash(self, color=C_WHITE, alpha=180, fade_speed=10):
        self.color    = color
        self.alpha    = alpha
        self.fade_spd = fade_speed

    def update(self):
        if self.alpha > 0:
            self.alpha = max(0, self.alpha - self.fade_spd)

    def draw(self, surface):
        if self.alpha > 0:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((*self.color[:3], int(self.alpha)))
            surface.blit(s, (0,0))


# ─── Background star field ────────────────────────────────────────────────────

class StarField:
    def __init__(self, count=120):
        self.stars = [
            (random.randint(0, SCREEN_WIDTH),
             random.randint(0, SCREEN_HEIGHT),
             random.uniform(0.2, 1.0),
             random.uniform(0.1, 0.5))
            for _ in range(count)
        ]

    def draw(self, surface, cam_x, cam_y):
        for sx, sy, bright, para in self.stars:
            px = int((sx - cam_x * para) % SCREEN_WIDTH)
            py = int((sy - cam_y * para * 0.3) % SCREEN_HEIGHT)
            col = int(bright * 200)
            r = 1 if bright < 0.6 else 2
            pygame.draw.circle(surface, (col, col, col+40), (px, py), r)


# ─── Misc helpers ─────────────────────────────────────────────────────────────

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def distance(ax, ay, bx, by):
    return math.hypot(ax-bx, ay-by)

def draw_glow_text(surface, text, font, color, x, y, glow_color=None, glow_r=3, center=False):
    """Render text with a soft glow halo."""
    if glow_color is None:
        glow_color = tuple(min(255, c+80) for c in color[:3])
    for dx in range(-glow_r, glow_r+1, glow_r):
        for dy in range(-glow_r, glow_r+1, glow_r):
            if dx == 0 and dy == 0:
                continue
            gs = font.render(text, True, (*glow_color, 80))
            gs.set_alpha(60)
            if center:
                rect = gs.get_rect(center=(x+dx, y+dy))
                surface.blit(gs, rect)
            else:
                surface.blit(gs, (x+dx, y+dy))
    ts = font.render(text, True, color)
    if center:
        rect = ts.get_rect(center=(x, y))
        surface.blit(ts, rect)
    else:
        surface.blit(ts, (x, y))
