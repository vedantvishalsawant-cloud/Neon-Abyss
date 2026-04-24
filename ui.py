"""
ui.py – All UI rendering: HUD, menus, screens, transitions.
"""

import pygame
import math
import random
from settings import *
from utils.helpers import (make_heart_surf, draw_glow_text,
                            StarField, clamp)


def _get_fonts():
    if not hasattr(_get_fonts, '_cache'):
        pygame.font.init()
        try:
            title  = pygame.font.SysFont('impact', 72, bold=True)
            big    = pygame.font.SysFont('impact', 48, bold=True)
            med    = pygame.font.SysFont('monospace', 28, bold=True)
            small  = pygame.font.SysFont('monospace', 18, bold=True)
            tiny   = pygame.font.SysFont('monospace', 14)
        except Exception:
            title  = pygame.font.Font(None, 72)
            big    = pygame.font.Font(None, 48)
            med    = pygame.font.Font(None, 28)
            small  = pygame.font.Font(None, 18)
            tiny   = pygame.font.Font(None, 14)
        _get_fonts._cache = dict(title=title, big=big, med=med,
                                  small=small, tiny=tiny)
    return _get_fonts._cache


# ──────────────────────────────────────────────────────────────────────────────
class HUD:
    def __init__(self):
        self._hearts = [make_heart_surf(True,  28) for _ in range(PLAYER_MAX_HEALTH)]
        self._empty  = [make_heart_surf(False, 28) for _ in range(PLAYER_MAX_HEALTH)]
        self._bat_icon = _make_battery_icon()
        self._timer  = 0

    def draw(self, surface, player, level_name, level_idx, total_levels):
        f = _get_fonts()
        self._timer += 1

        bar = pygame.Surface((SCREEN_WIDTH, HUD_HEIGHT), pygame.SRCALPHA)
        bar.fill((8, 10, 28, 200))
        pygame.draw.line(bar, (*C_PLAT_EDGE, 180),
                         (0, HUD_HEIGHT-1), (SCREEN_WIDTH, HUD_HEIGHT-1), 1)
        surface.blit(bar, (0, 0))

        for i in range(player.max_health):
            img = self._hearts[i] if i < player.health else self._empty[i]
            if player.health == 1 and i == 0:
                s = 1.0 + 0.12 * math.sin(self._timer * 0.15)
                w, h = int(28*s), int(28*s)
                img = pygame.transform.scale(img, (w, h))
                surface.blit(img, (12 + i*34 - (w-28)//2, 12 - (h-28)//2))
            else:
                surface.blit(img, (12 + i*34, 12))

        surface.blit(self._bat_icon, (12 + PLAYER_MAX_HEALTH*34 + 10, 10))
        bx = 12 + PLAYER_MAX_HEALTH*34 + 10 + 24
        draw_glow_text(surface, f"x{player.batteries:02d}",
                       f['small'], C_BATTERY, bx, 14)

        score_str = f"SCORE  {player.score:07d}"
        draw_glow_text(surface, score_str,
                       f['small'], C_TEXT_MAIN, SCREEN_WIDTH//2, 16,
                       center=True)

        ts = f['tiny'].render(f"{level_name}   [{level_idx+1}/{total_levels}]",
                              True, C_TEXT_DIM)
        surface.blit(ts, (SCREEN_WIDTH - ts.get_width() - 12, 20))


def _make_battery_icon():
    from utils.helpers import make_battery_surf
    return pygame.transform.scale(make_battery_surf(), (20, 30))


# ──────────────────────────────────────────────────────────────────────────────
class MainMenu:
    def __init__(self):
        self._stars   = StarField(150)
        self._timer   = 0
        self._options = ["NEW GAME", "CONTROLS", "QUIT"]
        self._sel     = 0
        self._result  = None

    @property
    def result(self):
        return self._result

    def reset(self):
        self._result = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._sel = (self._sel - 1) % len(self._options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._sel = (self._sel + 1) % len(self._options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                opt = self._options[self._sel]
                if opt == "NEW GAME":
                    self._result = 'new_game'
                elif opt == "CONTROLS":
                    self._result = 'controls'
                elif opt == "QUIT":
                    self._result = 'quit'

    def draw(self, surface):
        f = _get_fonts()
        self._timer += 1

        surface.fill(C_BG_DARK)
        self._stars.draw(surface, 0, 0)

        for i in range(0, SCREEN_WIDTH, 80):
            alpha = int(20 + 10 * math.sin(self._timer * 0.02 + i * 0.01))
            pygame.draw.line(surface, (*C_PLAT_EDGE, alpha),
                             (i, 0), (i, SCREEN_HEIGHT))
        for j in range(0, SCREEN_HEIGHT, 80):
            alpha = int(20 + 10 * math.sin(self._timer * 0.02 + j * 0.01))
            pygame.draw.line(surface, (*C_PLAT_EDGE, alpha),
                             (0, j), (SCREEN_WIDTH, j))

        title_col = (
            int(clamp(80 + 80*math.sin(self._timer*0.03), 60, 200)),
            int(clamp(160 + 60*math.sin(self._timer*0.04+1), 120, 255)),
            255
        )
        draw_glow_text(surface, "NEON ABYSS",
                       f['title'], title_col,
                       SCREEN_WIDTH//2, 160, glow_r=6, center=True)
        draw_glow_text(surface, "CIRCUIT BREAKER",
                       f['big'], C_CYAN,
                       SCREEN_WIDTH//2, 240, glow_r=4, center=True)

        sub = f['small'].render("A skill-based cyberpunk platformer",
                                True, C_TEXT_DIM)
        surface.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 296))

        for i, opt in enumerate(self._options):
            y  = 380 + i * 58
            if i == self._sel:
                bw = 280; bh = 42
                bx = SCREEN_WIDTH//2 - bw//2
                sel_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
                sel_surf.fill((*C_PLAT_EDGE, 60))
                pygame.draw.rect(sel_surf, C_CYAN, (0,0,bw,bh), 1,
                                 border_radius=4)
                surface.blit(sel_surf, (bx, y - 6))
                col = C_GOLD
                prefix = "▶ "
            else:
                col = C_TEXT_MAIN
                prefix = "  "
            draw_glow_text(surface, prefix + opt, f['med'], col,
                           SCREEN_WIDTH//2, y + 8, center=True)

        foot = f['tiny'].render(
            "© NEON ABYSS STUDIOS  |  ARROW KEYS: NAVIGATE  |  ENTER: SELECT",
            True, C_TEXT_DIM)
        surface.blit(foot, (SCREEN_WIDTH//2 - foot.get_width()//2,
                             SCREEN_HEIGHT - 30))


# ──────────────────────────────────────────────────────────────────────────────
class ControlsScreen:
    def __init__(self):
        self._done = False

    @property
    def done(self):
        return self._done

    def reset(self):
        self._done = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self._done = True

    def draw(self, surface):
        f = _get_fonts()
        surface.fill(C_BG_DARK)

        draw_glow_text(surface, "CONTROLS", f['big'], C_CYAN,
                       SCREEN_WIDTH//2, 80, center=True)

        controls = [
            ("A / ←", "Move Left"),
            ("D / →", "Move Right"),
            ("W / ↑ / SPACE", "Jump (tap for small, hold for high)"),
            ("SPACE (air)", "Double Jump"),
            ("ESC", "Pause"),
            ("", ""),
            ("TIPS:", ""),
            ("", "Jump on enemies to damage them"),
            ("", "Collect batteries for score"),
            ("", "Reach checkpoints to save progress"),
            ("", "During boss STUN phase – deal damage!"),
        ]
        y = 160
        for key, desc in controls:
            if key == "TIPS:":
                draw_glow_text(surface, "TIPS:", f['small'], C_GOLD,
                               SCREEN_WIDTH//2, y, center=True)
            elif key:
                ks = f['small'].render(f"  {key:<20}", True, C_CYAN)
                ds = f['small'].render(desc, True, C_TEXT_MAIN)
                surface.blit(ks, (SCREEN_WIDTH//2 - 320, y))
                surface.blit(ds, (SCREEN_WIDTH//2 - 60, y))
            else:
                ds = f['tiny'].render(desc, True, C_TEXT_DIM)
                surface.blit(ds, (SCREEN_WIDTH//2 - 60, y))
            y += 32

        foot = f['small'].render("Press any key to return", True, C_GOLD)
        surface.blit(foot, (SCREEN_WIDTH//2 - foot.get_width()//2,
                             SCREEN_HEIGHT - 60))


# ──────────────────────────────────────────────────────────────────────────────
class PauseMenu:
    def __init__(self):
        self._result = None
        self._sel    = 0
        self._options = ["RESUME", "MAIN MENU", "QUIT"]

    @property
    def result(self):
        return self._result

    def reset(self):
        self._result = None
        self._sel    = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._result = 'resume'
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._sel = (self._sel - 1) % len(self._options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._sel = (self._sel + 1) % len(self._options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._result = self._options[self._sel].lower().replace(' ', '_')

    def draw(self, surface):
        f = _get_fonts()
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 20, 160))
        surface.blit(dim, (0, 0))

        pw, ph = 380, 280
        px, py = SCREEN_WIDTH//2 - pw//2, SCREEN_HEIGHT//2 - ph//2
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((10, 14, 40, 230))
        pygame.draw.rect(panel, C_PLAT_EDGE, (0,0,pw,ph), 2, border_radius=8)
        surface.blit(panel, (px, py))

        draw_glow_text(surface, "PAUSED", f['big'], C_CYAN,
                       SCREEN_WIDTH//2, py + 30, center=True)

        for i, opt in enumerate(self._options):
            y = py + 100 + i * 52
            col = C_GOLD if i == self._sel else C_TEXT_MAIN
            pfx = "▶ " if i == self._sel else "  "
            draw_glow_text(surface, pfx + opt, f['med'], col,
                           SCREEN_WIDTH//2, y, center=True)


# ──────────────────────────────────────────────────────────────────────────────
class LevelTitle:
    DURATION = 150

    def __init__(self):
        self._timer  = 0
        self._name   = ""
        self._active = False

    def show(self, name):
        self._name   = name
        self._timer  = 0
        self._active = True

    @property
    def active(self):
        return self._active

    def update(self):
        if self._active:
            self._timer += 1
            if self._timer >= self.DURATION:
                self._active = False

    def draw(self, surface):
        if not self._active:
            return
        f = _get_fonts()
        t = self._timer
        if t < 30:
            alpha = int(255 * t / 30)
        elif t > self.DURATION - 30:
            alpha = int(255 * (self.DURATION - t) / 30)
        else:
            alpha = 255

        overlay = pygame.Surface((SCREEN_WIDTH, 120), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, int(alpha * 0.7)))
        surface.blit(overlay, (0, SCREEN_HEIGHT//2 - 60))

        draw_glow_text(surface, self._name, f['big'], C_CYAN,
                       SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20,
                       glow_r=5, center=True)
        sub = f['small'].render("NEW AREA DISCOVERED", True, C_TEXT_DIM)
        sub.set_alpha(alpha)
        surface.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2,
                           SCREEN_HEIGHT//2 + 22))


# ──────────────────────────────────────────────────────────────────────────────
class GameOver:
    def __init__(self):
        self._timer  = 0
        self._result = None

    @property
    def result(self):
        return self._result

    def reset(self):
        self._result = None
        self._timer  = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self._timer > 60:
            if event.key == pygame.K_r:
                self._result = 'respawn'
            elif event.key == pygame.K_m:
                self._result = 'menu'
            elif event.key == pygame.K_ESCAPE:
                self._result = 'menu'

    def update(self):
        self._timer += 1

    def draw(self, surface):
        f = _get_fonts()
        t = self._timer
        alpha = clamp(int(255 * t / 60), 0, 255)

        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((40, 0, 0, min(alpha, 180)))
        surface.blit(dim, (0,0))

        if t < 10: return

        draw_glow_text(surface, "SYSTEM FAILURE",
                       f['title'], C_HEART_FULL,
                       SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80,
                       glow_color=(200,0,0), glow_r=8, center=True)
        draw_glow_text(surface, "CONNECTION LOST",
                       f['med'], C_TEXT_DIM,
                       SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10,
                       center=True)

        if t > 60:
            pulse = int(180 + 60 * math.sin(t * 0.1))
            draw_glow_text(surface, "[R] RESPAWN AT CHECKPOINT",
                           f['small'], (pulse, pulse//2, 50),
                           SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60,
                           center=True)
            draw_glow_text(surface, "[M] MAIN MENU",
                           f['small'], C_TEXT_DIM,
                           SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 96,
                           center=True)


# ──────────────────────────────────────────────────────────────────────────────
class LevelComplete:
    DURATION = 180

    def __init__(self):
        self._timer   = 0
        self._active  = False
        self._score   = 0
        self._bats    = 0
        self._result  = None

    @property
    def result(self):
        return self._result

    @property
    def active(self):
        return self._active

    def show(self, score, batteries):
        self._timer  = 0
        self._active = True
        self._score  = score
        self._bats   = batteries
        self._result = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self._timer > 80:
            self._result = 'next'

    def update(self):
        if self._active:
            self._timer += 1
            if self._timer >= self.DURATION:
                self._result = 'next'

    def draw(self, surface):
        if not self._active:
            return
        f = _get_fonts()
        t = self._timer
        alpha = clamp(int(255 * t / 40), 0, 255)

        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 20, 10, min(alpha, 160)))
        surface.blit(dim, (0,0))

        draw_glow_text(surface, "SECTOR CLEARED",
                       f['big'], C_BATTERY,
                       SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 70,
                       glow_r=5, center=True)

        if t > 30:
            draw_glow_text(surface,
                           f"SCORE   {self._score:07d}",
                           f['med'], C_TEXT_MAIN,
                           SCREEN_WIDTH//2, SCREEN_HEIGHT//2,
                           center=True)
        if t > 50:
            draw_glow_text(surface,
                           f"BATTERIES   x{self._bats:02d}",
                           f['small'], C_BATTERY,
                           SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 44,
                           center=True)
        if t > 80:
            pulse = int(180 + 60 * math.sin(t * 0.15))
            draw_glow_text(surface, "Press any key to continue...",
                           f['tiny'], (pulse, pulse, pulse),
                           SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 90,
                           center=True)


# ──────────────────────────────────────────────────────────────────────────────
class VictoryScreen:
    def __init__(self):
        self._timer      = 0
        self._stars      = StarField(200)
        self._result     = None
        self._particles  = []

    @property
    def result(self):
        return self._result

    def reset(self):
        self._result = None
        self._timer  = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self._timer > 120:
            self._result = 'menu'

    def update(self):
        self._timer += 1
        if random.random() < 0.4:
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            col = random.choice([C_GOLD, C_CYAN, C_BATTERY,
                                  C_BOSS_BULLET, C_WHITE])
            self._particles.append([x, y, col,
                                     random.uniform(-3, 3),
                                     random.uniform(-5, -1), 60])
        self._particles = [p for p in self._particles if p[5] > 0]
        for p in self._particles:
            p[0] += p[3]; p[1] += p[4]; p[4] += 0.15; p[5] -= 1

    def draw(self, surface):
        f = _get_fonts()
        t = self._timer

        surface.fill(C_BG_DARK)
        self._stars.draw(surface, 0, 0)

        for p in self._particles:
            alpha = int(255 * p[5] / 60)
            s = pygame.Surface((6,6), pygame.SRCALPHA)
            s.fill((*p[2][:3], alpha))
            surface.blit(s, (int(p[0]), int(p[1])))

        col = (
            int(200 + 55*math.sin(t*0.04)),
            int(180 + 60*math.sin(t*0.05+1)),
            int(50 + 80*math.sin(t*0.06+2))
        )
        draw_glow_text(surface, "SYSTEM RESTORED",
                       f['title'], col,
                       SCREEN_WIDTH//2, 180, glow_r=8, center=True)
        draw_glow_text(surface, "CORE-X DEFEATED",
                       f['big'], C_BATTERY,
                       SCREEN_WIDTH//2, 272, glow_r=4, center=True)

        if t > 60:
            draw_glow_text(surface,
                           "You have conquered the Neon Abyss.",
                           f['med'], C_TEXT_MAIN,
                           SCREEN_WIDTH//2, 360, center=True)
        if t > 90:
            draw_glow_text(surface,
                           "The circuit has been broken.",
                           f['small'], C_TEXT_DIM,
                           SCREEN_WIDTH//2, 404, center=True)
        if t > 120:
            pulse2 = int(180 + 60 * math.sin(t * 0.1))
            draw_glow_text(surface, "Press any key for Main Menu",
                           f['small'], (pulse2, pulse2, pulse2),
                           SCREEN_WIDTH//2, SCREEN_HEIGHT - 80,
                           center=True)


# ──────────────────────────────────────────────────────────────────────────────
class Transition:
    def __init__(self):
        self._alpha   = 0
        self._dir     = 0
        self._done    = False
        self._speed   = 8

    def fade_out(self, speed=8):
        self._alpha = 0
        self._dir   = 1
        self._speed = speed
        self._done  = False

    def fade_in(self, speed=8):
        self._alpha = 255
        self._dir   = -1
        self._speed = speed
        self._done  = False

    @property
    def done(self):
        return self._done

    @property
    def fully_black(self):
        return self._alpha >= 255

    def update(self):
        self._alpha = clamp(self._alpha + self._dir * self._speed, 0, 255)
        if self._dir == 1 and self._alpha >= 255:
            self._done = True
        elif self._dir == -1 and self._alpha <= 0:
            self._done = True

    def draw(self, surface):
        if self._alpha > 0:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.fill(C_BLACK)
            s.set_alpha(self._alpha)
            surface.blit(s, (0,0))