"""
level.py – Platform, Hazard, Collectible, Checkpoint entities,
            plus the Level class that loads one of 12 hand-designed stages.
"""

import pygame
import math
import random
from settings import *
from utils.helpers import (make_platform_surf, make_acid_surf, make_spike_surf,
                            make_battery_surf, make_checkpoint_surf, clamp)


# ──────────────────────────────────────────────────────────────────────────────
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, moving=False):
        super().__init__()
        self.image = make_platform_surf(w, h, moving)
        self.rect  = pygame.Rect(x, y, w, h)
        self.moving = moving

class MovingPlatform(Platform):
    def __init__(self, x, y, w, h, a, b, speed, axis='x'):
        super().__init__(x, y, w, h, moving=True)
        self._a     = float(a)
        self._b     = float(b)
        self._speed = speed
        self._axis  = axis
        self._t     = 0.0

    def update(self):
        if self._axis == 'x':
            span = self._b - self._a
            self._t = (self._t + self._speed / max(abs(span),1)) % 1.0
            self.rect.x = int(self._a + span * (0.5 - 0.5*math.cos(math.pi*2*self._t)))
        else:
            span = self._b - self._a
            self._t = (self._t + self._speed / max(abs(span),1)) % 1.0
            self.rect.y = int(self._a + span * (0.5 - 0.5*math.cos(math.pi*2*self._t)))


class Hazard(pygame.sprite.Sprite):
    def __init__(self, x, y, w, htype='acid'):
        super().__init__()
        h = 24
        if htype == 'acid':
            self.image = make_acid_surf(w, h)
        else:
            self.image = make_spike_surf(w, h)
        self.rect = pygame.Rect(x, y, w, h)
        self.htype = htype


class Battery(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self._base_img = make_battery_surf()
        self.image     = self._base_img.copy()
        self.rect      = self.image.get_rect(center=(x, y))
        self._timer    = random.randint(0, 60)

    def update(self):
        self._timer += 1
        offset = int(math.sin(self._timer * 0.08) * 4)
        self.rect.centery += offset - int(math.sin((self._timer-1) * 0.08) * 4)
        bright = int(40 * abs(math.sin(self._timer * 0.05)))
        img = self._base_img.copy()
        tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        tint.fill((0, bright, bright//2, 0))
        img.blit(tint, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
        self.image = img

    def draw(self, surface, cam_x, cam_y):
        surface.blit(self.image,
                     (self.rect.x - cam_x, self.rect.y - cam_y))


class Checkpoint(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self._inact_img = make_checkpoint_surf()
        self._act_img   = make_checkpoint_surf()
        tint = pygame.Surface(self._act_img.get_size(), pygame.SRCALPHA)
        tint.fill((*C_CYAN, 80))
        self._act_img.blit(tint, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
        self.active = False
        self.image  = self._inact_img
        self.rect   = self.image.get_rect(midbottom=(x, y))

    def activate(self):
        if not self.active:
            self.active = True
            self.image  = self._act_img

    def draw(self, surface, cam_x, cam_y):
        surface.blit(self.image,
                     (self.rect.x - cam_x, self.rect.y - cam_y))


class ExitZone(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.rect   = pygame.Rect(x, y, w, h)
        self._timer = 0

    def update(self):
        self._timer += 1

    def draw(self, surface, cam_x, cam_y):
        t  = self._timer
        alpha = 120 + int(80 * math.sin(t * 0.05))
        s  = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        col = (40, 255, 140)
        pygame.draw.rect(s, (*col, alpha//2), (0,0,self.rect.w,self.rect.h),
                         border_radius=8)
        pygame.draw.rect(s, (*col, alpha), (0,0,self.rect.w,self.rect.h),
                         2, border_radius=8)
        font = pygame.font.SysFont('monospace', 14, bold=True)
        txt  = font.render("EXIT", True, (*col, alpha))
        s.blit(txt, (self.rect.w//2 - txt.get_width()//2, 6))
        surface.blit(s, (self.rect.x-cam_x, self.rect.y-cam_y))


# ──────────────────────────────────────────────────────────────────────────────
T = TILE

def _level_01():
    cmds = [
        ('START', 80, 500),
        ('PLAT', 0, 560, 1600, T),
        ('PLAT', 240, 480, 160, 16),
        ('PLAT', 480, 400, 200, 16),
        ('PLAT', 760, 320, 160, 16),
        ('PLAT', 1000, 400, 200, 16),
        ('PLAT', 1280, 480, 200, 16),
        ('BAT', 300, 450), ('BAT', 560, 370), ('BAT', 840, 290),
        ('BAT', 1080, 370), ('BAT', 1350, 450),
        ('SPIKE', 360, 536, T),
        ('ENEMY', 1, 600, 520),
        ('ENEMY', 1, 1100, 360),
        ('CHECK', 840, 560),
        ('END', 1440, 480, 80, T),
    ]
    return cmds, 1600, 600

def _level_02():
    cmds = [
        ('START', 60, 480),
        ('PLAT', 0, 520, 400, T),
        ('PLAT', 460, 440, 160, 16),
        ('PLAT', 680, 360, 160, 16),
        ('PLAT', 900, 280, 200, 16),
        ('PLAT', 1160, 360, 160, 16),
        ('PLAT', 1380, 440, 160, 16),
        ('PLAT', 1600, 520, 600, T),
        ('SPIKE', 400, 496, T*3),
        ('SPIKE', 1540, 496, T*3),
        ('BAT', 540, 410), ('BAT', 760, 330), ('BAT', 980, 250),
        ('BAT', 1240, 330), ('BAT', 1700, 490),
        ('ENEMY', 1, 200, 480),
        ('ENEMY', 2, 980, 240),
        ('ENEMY', 1, 1700, 480),
        ('CHECK', 1000, 280),
        ('END', 2050, 480, 80, T),
    ]
    return cmds, 2200, 580

def _level_03():
    cmds = [
        ('START', 80, 400),
        ('PLAT', 0, 440, 300, T),
        ('PLAT', 360, 360, 120, 16),
        ('PLAT', 540, 280, 120, 16),
        ('PLAT', 720, 200, 200, 16),
        ('PLAT', 980, 280, 120, 16),
        ('PLAT', 1160, 360, 160, 16),
        ('PLAT', 1380, 440, 400, T),
        ('ACID', 300, 416, T*3),
        ('ACID', 860, 416, T*5),
        ('ACID', 1140, 416, T*3),
        ('BAT', 420, 330), ('BAT', 600, 250), ('BAT', 810, 170),
        ('BAT', 1060, 250), ('BAT', 1550, 410),
        ('ENEMY', 1, 400, 320),
        ('ENEMY', 3, 900, 240),
        ('ENEMY', 2, 1200, 320),
        ('CHECK', 800, 200),
        ('END', 1700, 400, 80, T),
    ]
    return cmds, 1900, 500

def _level_04():
    cmds = [
        ('START', 80, 440),
        ('PLAT', 0, 480, 280, T),
        ('MPLAT', 340, 440, 120, 16, 340, 560, 1.2),
        ('MPLAT', 640, 360, 120, 16, 640, 800, 1.0),
        ('PLAT', 880, 400, 160, 16),
        ('MPLAT', 1080, 320, 120, 16, 1080, 1240, 1.5),
        ('PLAT', 1320, 400, 200, 16),
        ('MPLAT', 1560, 440, 120, 16, 1560, 1720, 1.0),
        ('PLAT', 1800, 480, 400, T),
        ('ACID', 280, 456, T*2),
        ('ACID', 840, 456, T*3),
        ('SPIKE', 1760, 456, T*2),
        ('BAT', 400, 410), ('BAT', 700, 330), ('BAT', 1140, 290),
        ('BAT', 1620, 410), ('BAT', 1950, 450),
        ('ENEMY', 2, 450, 440),
        ('ENEMY', 3, 900, 360),
        ('ENEMY', 1, 1950, 440),
        ('CHECK', 900, 400),
        ('END', 2100, 440, 80, T),
    ]
    return cmds, 2300, 540

def _level_05():
    cmds = [
        ('START', 80, 500),
        ('PLAT', 0, 540, 240, T),
        ('VPLAT', 300, 460, 120, 16, 320, 460, 1.0),
        ('VPLAT', 480, 380, 120, 16, 260, 420, 1.2),
        ('VPLAT', 660, 300, 120, 16, 180, 340, 1.0),
        ('PLAT', 820, 260, 200, 16),
        ('VPLAT', 1080, 300, 120, 16, 200, 360, 1.3),
        ('VPLAT', 1260, 380, 120, 16, 280, 420, 1.1),
        ('PLAT', 1440, 460, 400, T),
        ('ACID', 240, 516, T*4),
        ('ACID', 770, 516, T*6),
        ('SPIKE', 1400, 436, T*2),
        ('BAT', 360, 430), ('BAT', 540, 350), ('BAT', 900, 230),
        ('BAT', 1140, 270), ('BAT', 1600, 430),
        ('ENEMY', 3, 500, 340),
        ('ENEMY', 3, 1000, 220),
        ('ENEMY', 2, 1200, 340),
        ('CHECK', 840, 260),
        ('END', 1760, 420, 80, T),
    ]
    return cmds, 2000, 580

def _level_06():
    cmds = [
        ('START', 80, 480),
        ('PLAT', 0, 520, 2400, T),
        ('PLAT', 0,  320, 2400, 16),
        *[('PLAT', 200+i*200, 336, T, 184) for i in range(9)],
        ('ACID',  160, 496, T), ('ACID', 360, 496, T),
        ('ACID',  560, 496, T), ('ACID',  760, 496, T),
        ('ACID',  960, 496, T), ('ACID', 1160, 496, T),
        ('ACID', 1360, 496, T), ('ACID', 1560, 496, T),
        ('SPIKE',1760, 496, T), ('SPIKE',1960, 496, T),
        ('BAT', 100, 280), ('BAT', 300, 480), ('BAT', 500, 280),
        ('BAT', 700, 480), ('BAT', 900, 280), ('BAT',1100, 480),
        ('BAT',1300, 280), ('BAT',1500, 480), ('BAT',1700, 280),
        ('BAT',1900, 480), ('BAT',2100, 280),
        ('ENEMY', 1,  150, 480), ('ENEMY', 1,  350, 480),
        ('ENEMY', 1,  550, 280), ('ENEMY', 2,  750, 480),
        ('ENEMY', 3,  950, 280), ('ENEMY', 1, 1150, 480),
        ('ENEMY', 2, 1350, 280), ('ENEMY', 3, 1550, 480),
        ('ENEMY', 1, 1750, 280), ('ENEMY', 2, 1950, 480),
        ('CHECK', 1200, 280),
        ('END', 2250, 480, 80, T),
    ]
    return cmds, 2500, 560

def _level_07():
    cmds = [
        ('START', 80, 440),
        ('PLAT', 0, 480, 200, T),
        ('MPLAT', 240, 440, 100, 16, 240, 400, 1.5),
        ('MPLAT', 440, 360, 100, 16, 440, 640, 1.2),
        ('VPLAT', 640, 280, 100, 16, 200, 330, 1.0),
        ('PLAT', 780, 240, 200, 16),
        ('MPLAT', 1040, 280, 100, 16, 1040, 1220, 1.8),
        ('VPLAT', 1260, 300, 100, 16, 220, 350, 1.4),
        ('MPLAT', 1400, 360, 100, 16, 1400, 1600, 1.3),
        ('PLAT', 1640, 420, 200, 16),
        ('PLAT', 1880, 480, 400, T),
        ('ACID', 200, 456, T*4), ('ACID', 760, 456, T*5),
        ('SPIKE', 1600, 396, T*2),
        ('BAT', 280, 400), ('BAT', 500, 320), ('BAT', 820, 200),
        ('BAT', 1100, 240), ('BAT', 1480, 320), ('BAT', 2000, 450),
        ('ENEMY', 1, 300, 440), ('ENEMY', 2, 850, 200),
        ('ENEMY', 3, 1100, 200), ('ENEMY', 2, 1700, 380),
        ('ENEMY', 3, 1950, 440),
        ('CHECK', 840, 240),
        ('END', 2200, 440, 80, T),
    ]
    return cmds, 2400, 540

def _level_08():
    cmds = [
        ('START', 80, 500),
        ('PLAT', 0, 540, 200, T),
    ]
    for col in range(8):
        for row in range(3):
            bx = 240 + col * 220
            by = 420 - row * 100
            spd = 0.8 + col * 0.15
            if (col + row) % 2 == 0:
                cmds.append(('MPLAT', bx, by, 100, 16, bx-60, bx+60, spd))
            else:
                cmds.append(('VPLAT', bx, by, 100, 16, by-50, by+50, spd))
    cmds += [
        ('PLAT', 2040, 500, 400, T),
        *[('ACID', 200+i*160, 516, 120) for i in range(11)],
        ('BAT', 340, 400), ('BAT', 560, 310), ('BAT', 780, 220),
        ('BAT', 1000, 310), ('BAT', 1220, 400), ('BAT', 1440, 310),
        ('BAT', 1660, 220), ('BAT', 1880, 310), ('BAT', 2150, 470),
        ('ENEMY', 3, 600, 290), ('ENEMY', 2, 1000, 290),
        ('ENEMY', 3, 1400, 290), ('ENEMY', 2, 1800, 290),
        ('ENEMY', 1, 2150, 460),
        ('CHECK', 1120, 220),
        ('END', 2350, 460, 80, T),
    ]
    return cmds, 2600, 580

def _level_09():
    cmds = [
        ('START', 400, 80),
        ('PLAT', 200, 120, 400, 16),
        ('PLAT', 600, 220, 120, 16), ('PLAT', 100, 340, 120, 16),
        ('PLAT', 500, 460, 200, 16), ('PLAT', 200, 580, 120, 16),
        ('PLAT', 600, 700, 200, 16), ('PLAT', 100, 820, 120, 16),
        ('PLAT', 500, 940, 200, 16), ('PLAT', 200,1060, 120, 16),
        ('PLAT', 600,1180, 200, 16), ('PLAT', 100,1300, 120, 16),
        ('PLAT', 400,1420, 500, T),
        ('ACID', 700, 96, T*3),
        ('ACID',   0, 96, T*3),
        ('ACID', 360, 216, T*5),
        ('SPIKE', 700, 436, T), ('SPIKE', 100, 556, T),
        ('ACID', 0, 1396, T*10),
        ('BAT', 650, 190), ('BAT', 150, 310), ('BAT', 550, 430),
        ('BAT', 250, 550), ('BAT', 650, 670), ('BAT', 150, 790),
        ('BAT', 550, 910), ('BAT', 250,1030), ('BAT', 660,1150),
        ('ENEMY', 3, 650, 180), ('ENEMY', 2, 600, 640),
        ('ENEMY', 1, 550, 900), ('ENEMY', 3, 600,1140),
        ('CHECK', 600, 700),
        ('END', 550, 1380, 80, T),
    ]
    return cmds, 900, 1480

def _level_10():
    cmds = [
        ('START', 80, 480),
        ('PLAT', 0, 520, 3200, T),
        ('SPIKE', 200, 496, T*2), ('ACID', 360, 496, T*3),
        ('SPIKE', 720, 496, T*2), ('ACID', 960, 496, T*4),
        ('SPIKE',1440, 496, T*2), ('ACID',1680, 496, T*4),
        ('SPIKE',2160, 496, T*2), ('ACID',2400, 496, T*5),
        ('SPIKE',2880, 496, T*2),
        ('PLAT', 480,  360, 160, 16), ('PLAT',  800, 280, 200, 16),
        ('PLAT',1160,  360, 160, 16), ('PLAT', 1400, 280, 200, 16),
        ('PLAT',1800,  360, 160, 16), ('PLAT', 2200, 280, 160, 16),
        ('MPLAT',2400, 360, 120, 16, 2400, 2600, 1.5),
        ('MPLAT',2600, 280, 120, 16, 2600, 2800, 1.8),
        ('PLAT', 2850, 360, 200, 16),
        ('BAT',  140, 490), ('BAT',  540, 330), ('BAT',  860, 250),
        ('BAT', 1240, 330), ('BAT', 1480, 250), ('BAT', 1880, 330),
        ('BAT', 2280, 250), ('BAT', 2480, 330), ('BAT', 2700, 250),
        ('BAT', 2940, 330), ('BAT', 3100, 490),
        ('ENEMY', 1,  140, 480), ('ENEMY', 2,  600, 480),
        ('ENEMY', 3,  880, 240), ('ENEMY', 1, 1160, 480),
        ('ENEMY', 2, 1480, 240), ('ENEMY', 3, 1700, 480),
        ('ENEMY', 1, 1880, 480), ('ENEMY', 3, 2280, 240),
        ('ENEMY', 2, 2600, 480), ('ENEMY', 1, 2900, 480),
        ('ENEMY', 3, 3050, 320), ('ENEMY', 2, 3100, 480),
        ('CHECK', 1600, 480), ('CHECK', 2600, 480),
        ('END', 3100, 480, 80, T),
    ]
    return cmds, 3300, 580

def _level_11():
    cmds = [
        ('START', 80, 440),
        ('PLAT', 0, 480, 160, T),
        ('MPLAT', 200, 440, 100, 16, 200, 440, 2.0),
        ('MPLAT', 380, 360, 100, 16, 380, 600, 2.0),
        ('VPLAT', 600, 280, 100, 16, 160, 320, 2.0),
        ('MPLAT', 760, 240, 100, 16, 760, 980, 2.2),
        ('VPLAT', 1000, 280, 100, 16, 180, 330, 1.8),
        ('MPLAT', 1160, 320, 100, 16, 1160, 1380, 2.4),
        ('PLAT',  1380, 400, 120, 16),
        ('VPLAT', 1540, 360, 100, 16, 200, 380, 2.0),
        ('PLAT',  1680, 440, 400, T),
        ('ACID', 160, 456, T*3), ('ACID', 580, 456, T*4),
        ('ACID', 980, 456, T*4), ('ACID',1380, 416, T*2),
        ('SPIKE', 340, 416, T), ('SPIKE', 760, 416, T),
        ('BAT', 280, 400), ('BAT', 460, 320), ('BAT', 820, 200),
        ('BAT', 1040, 240), ('BAT', 1240, 280), ('BAT', 1800, 410),
        ('ENEMY', 2, 300, 400), ('ENEMY', 3, 480, 320),
        ('ENEMY', 2, 840, 200), ('ENEMY', 3, 1060, 240),
        ('ENEMY', 1, 1400, 360), ('ENEMY', 2, 1750, 400),
        ('CHECK', 840, 240),
        ('END', 2000, 400, 80, T),
    ]
    return cmds, 2200, 540

def _level_12():
    cmds = [
        ('START', 200, 500),
        ('PLAT', 0, 560, 1200, T),
        ('PLAT', -T, 0, T, 600),
        ('PLAT', 1200, 0, T, 600),
        ('PLAT', 360, 440, 80, 120),
        ('PLAT', 760, 440, 80, 120),
        ('PLAT', 160, 360, 120, 16),
        ('PLAT', 920, 360, 120, 16),
        ('PLAT', 540, 280, 120, 16),
        ('ACID', 0, 536, T*2),
        ('ACID', 1080, 536, T*2),
        ('BOSS', 600, 320),
        ('BAT', 200, 330), ('BAT', 540, 250), ('BAT', 900, 330),
        ('BAT', 200, 530), ('BAT', 600, 530), ('BAT', 1000, 530),
    ]
    return cmds, 1200, 600


_LEVEL_FUNCS = [
    _level_01, _level_02, _level_03, _level_04,
    _level_05, _level_06, _level_07, _level_08,
    _level_09, _level_10, _level_11, _level_12,
]


# ──────────────────────────────────────────────────────────────────────────────
class Level:
    def __init__(self, level_index):
        from enemy import PatrolEnemy, ChaserEnemy, RangedEnemy

        self.index       = level_index
        self.name        = LEVEL_NAMES[level_index]
        self.is_boss     = (level_index == 11)

        func = _LEVEL_FUNCS[level_index]
        cmds, self.width, self.height = func()

        self.platforms   = pygame.sprite.Group()
        self.hazards     = pygame.sprite.Group()
        self.batteries   = pygame.sprite.Group()
        self.checkpoints = pygame.sprite.Group()
        self.enemies     = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.exits       = pygame.sprite.Group()

        self.player_start = (80, 480)
        self.boss         = None

        self._parse(cmds)

    def _parse(self, cmds):
        from enemy import PatrolEnemy, ChaserEnemy, RangedEnemy
        from boss import Boss

        for cmd in cmds:
            kind = cmd[0]
            if kind == 'START':
                self.player_start = (cmd[1], cmd[2])
            elif kind == 'PLAT':
                _, x, y, w, h = cmd
                self.platforms.add(Platform(x, y, w, h))
            elif kind == 'MPLAT':
                _, x, y, w, h, ax, bx, spd = cmd
                self.platforms.add(MovingPlatform(x, y, w, h, ax, bx, spd, 'x'))
            elif kind == 'VPLAT':
                _, x, y, w, h, ay, by, spd = cmd
                self.platforms.add(MovingPlatform(x, y, w, h, ay, by, spd, 'y'))
            elif kind == 'ACID':
                _, x, y, w = cmd
                self.hazards.add(Hazard(x, y, w, 'acid'))
            elif kind == 'SPIKE':
                _, x, y, w = cmd
                self.hazards.add(Hazard(x, y, w, 'spike'))
            elif kind == 'BAT':
                self.batteries.add(Battery(cmd[1], cmd[2]))
            elif kind == 'CHECK':
                self.checkpoints.add(Checkpoint(cmd[1], cmd[2]))
            elif kind == 'ENEMY':
                etype = cmd[1]; x = cmd[2]; y = cmd[3]
                if etype == 1:
                    rng = cmd[4] if len(cmd) > 4 else 180
                    self.enemies.add(PatrolEnemy(x, y, rng))
                elif etype == 2:
                    self.enemies.add(ChaserEnemy(x, y))
                elif etype == 3:
                    self.enemies.add(RangedEnemy(x, y))
            elif kind == 'END':
                _, x, y, w, h = cmd
                self.exits.add(ExitZone(x, y, w, h))
            elif kind == 'BOSS':
                self.boss = Boss(cmd[1], cmd[2])

    def update(self, player):
        for p in self.platforms:
            if hasattr(p, 'update'):
                p.update()
        self.batteries.update()
        self.exits.update()
        for enemy in self.enemies:
            enemy.update(player, self.platforms, self.projectiles)
        for proj in list(self.projectiles):
            proj.update(self.platforms)
        if self.boss:
            self.boss.update(player, self.platforms)

    def draw(self, surface, cam_x, cam_y):
        for p in self.platforms:
            surface.blit(p.image, (p.rect.x - cam_x, p.rect.y - cam_y))
        for h in self.hazards:
            surface.blit(h.image, (h.rect.x - cam_x, h.rect.y - cam_y))
        for b in self.batteries:
            b.draw(surface, cam_x, cam_y)
        for c in self.checkpoints:
            c.draw(surface, cam_x, cam_y)
        for e in self.exits:
            e.draw(surface, cam_x, cam_y)
        for enemy in self.enemies:
            enemy.draw(surface, cam_x, cam_y)
        for proj in self.projectiles:
            proj.draw(surface, cam_x, cam_y)
        if self.boss:
            self.boss.draw(surface, cam_x, cam_y)