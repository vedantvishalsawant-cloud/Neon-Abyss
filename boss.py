"""
boss.py – Final boss: CORE-X

Three distinct phases with escalating attack patterns.
Phase 1: Slow aimed shots + slam
Phase 2: Spread shots + bouncing orbs + teleport
Phase 3: Megalovania-style bullet hell – walls, spirals, rings
"""

import pygame
import math
import random
from settings import *
from utils.helpers import (make_boss_surf, make_bullet_surf,
                            ParticleSystem, distance, clamp)
from enemy import Projectile


# ──────────────────────────────────────────────────────────────────────────────
class BossProjectile(Projectile):
    """Boss-specific projectile with homing or pattern options."""

    def __init__(self, x, y, vx, vy, color=C_BOSS_BULLET, damage=1,
                 size=7, homing=False, target=None, bounce=0):
        super().__init__(x, y, vx, vy, color, damage, size)
        self._homing   = homing
        self._target   = target
        self._bounce   = bounce
        self._life     = 480

    def update(self, platforms=None):
        if self._homing and self._target and self._target.alive:
            dx = self._target.rect.centerx - self.rect.centerx
            dy = self._target.rect.centery  - self.rect.centery
            spd = math.hypot(self.vx, self.vy)
            ang = math.atan2(self.vy, self.vx)
            target_ang = math.atan2(dy, dx)
            diff = (target_ang - ang + math.pi) % math.tau - math.pi
            ang += clamp(diff, -0.05, 0.05)
            self.vx = math.cos(ang) * spd
            self.vy = math.sin(ang) * spd

        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self._life  -= 1

        if self._bounce > 0 and platforms:
            for p in platforms:
                if self.rect.colliderect(p.rect):
                    self.vy       = -abs(self.vy)
                    self._bounce -= 1
                    break

        if (self._life <= 0
                or self.rect.right < -200 or self.rect.left  > 99999
                or self.rect.top   < -400 or self.rect.bottom > 99999):
            self.kill()


# ──────────────────────────────────────────────────────────────────────────────
class Boss(pygame.sprite.Sprite):
    """
    CORE-X – The final boss.

    State machine:
        'intro'   – drops from ceiling
        'idle'    – brief pause between attacks
        'attack'  – executing an attack routine
        'stun'    – vulnerable window (flashes cyan)
        'dead'    – death sequence
    """

    MAX_HEALTH   = 300
    PHASE2_HP    = 200
    PHASE3_HP    = 100
    STUN_FRAMES  = 45
    W, H         = 80, 90

    def __init__(self, x, y):
        super().__init__()

        self.phase      = 1
        self._phase_surf = {
            1: make_boss_surf(1),
            2: make_boss_surf(2),
            3: make_boss_surf(3),
        }
        self.image      = self._phase_surf[1]
        self.rect       = self.image.get_rect(center=(x, y))

        self.health     = self.MAX_HEALTH
        self.alive      = True
        self.score_value = BOSS_SCORE

        self.vel_x      = 0.0
        self.vel_y      = 0.0
        self.on_ground  = False

        self._state        = 'intro'
        self._state_timer  = 0
        self._idle_timer   = 0
        self._attack_index = 0
        self._attack_timer = 0
        self._attack_phase = 0
        self._stun_timer   = 0

        self._hit_timer    = 0
        self._target_y     = float(y)
        self._origin_x     = float(x)

        self.particles     = ParticleSystem()
        self.projectiles   = pygame.sprite.Group()

        self._phase_flash  = 0
        self._dead_timer   = 0
        self._death_done   = False

        self._float_timer  = 0.0
        self._attacks_done = 0

    # ─── Public interface ─────────────────────────────────────────────────────
    @property
    def dead(self):
        return self._death_done

    def take_damage(self, amount, shake_cb=None, flash_cb=None):
        if not self.alive or self._state in ('intro', 'dead'):
            return
        self.health    -= amount
        self._hit_timer = 8
        self.particles.emit(self.rect.centerx, self.rect.centery,
                            C_BOSS, count=8, speed=4, life=20)
        if shake_cb:
            shake_cb(4, 8)

        if self.health <= self.PHASE2_HP and self.phase == 1:
            self._start_phase(2, flash_cb)
        elif self.health <= self.PHASE3_HP and self.phase == 2:
            self._start_phase(3, flash_cb)

        if self.health <= 0:
            self.health = 0
            self._begin_death(shake_cb)

    def _start_phase(self, new_phase, flash_cb=None):
        self.phase         = new_phase
        self._phase_flash  = 60
        self._stun_timer   = 90
        self._state        = 'stun'
        self._attacks_done = 0
        self.image         = self._phase_surf[new_phase]
        if flash_cb:
            flash_cb([C_WHITE, C_BOSS_BULLET, (200,0,255)][new_phase-1],
                     alpha=220, fade_speed=6)
        self.particles.emit(self.rect.centerx, self.rect.centery,
                            [C_BOSS, C_BOSS_2, (200,0,255)][new_phase-1],
                            count=40, speed=8, life=50)

    def _begin_death(self, shake_cb=None):
        self.alive      = False
        self._state     = 'dead'
        self._dead_timer = 180
        if shake_cb:
            shake_cb(12, 60)
        self.particles.emit(self.rect.centerx, self.rect.centery,
                            C_GOLD, count=60, speed=10, life=80)

    # ─── Main update ──────────────────────────────────────────────────────────
    def update(self, player, platforms, dt=1.0):
        self.particles.update()
        for p in self.projectiles:
            p.update(platforms)

        if self._state == 'intro':
            self._do_intro()
        elif self._state == 'idle':
            self._do_idle(player)
        elif self._state == 'attack':
            self._do_attack(player, platforms)
        elif self._state == 'stun':
            self._do_stun()
        elif self._state == 'dead':
            self._do_dead()

        self._float_timer += 0.04
        if self._state not in ('intro', 'dead', 'attack'):
            offset = math.sin(self._float_timer) * 4
            self.rect.y = int(self._target_y + offset)

        if self._state == 'intro':
            self.vel_y += GRAVITY * 0.4
            self.rect.y += int(self.vel_y)
            for p in platforms:
                if self.rect.colliderect(p.rect) and self.vel_y > 0:
                    self.rect.bottom = p.rect.top
                    self.vel_y       = 0
                    self.on_ground   = True
                    self._target_y   = float(self.rect.y)
                    self._state      = 'idle'
                    self._idle_timer = 80

        self._update_image()

    # ─── State handlers ───────────────────────────────────────────────────────
    def _do_intro(self):
        if random.random() < 0.3:
            self.particles.emit(self.rect.centerx, self.rect.bottom,
                                C_BOSS, count=3, speed=2, life=20)

    def _do_idle(self, player):
        self._idle_timer -= 1
        if self._idle_timer <= 0:
            self._state       = 'attack'
            self._attack_timer = 0
            self._attack_phase = 0
            self._pick_attack()

    def _pick_attack(self):
        if self.phase == 1:
            patterns = [self._atk_aimed_burst, self._atk_spiral, self._atk_slam]
        elif self.phase == 2:
            patterns = [self._atk_spread, self._atk_homing, self._atk_wall,
                        self._atk_bouncing, self._atk_spiral]
        else:
            patterns = [self._atk_ring, self._atk_wall, self._atk_chaos,
                        self._atk_homing, self._atk_spiral_fast, self._atk_grid]
        self._current_atk = patterns[self._attack_index % len(patterns)]
        self._attack_index += 1

    def _do_attack(self, player, platforms):
        self._attack_timer += 1
        done = self._current_atk(player, platforms)
        if done:
            self._attacks_done += 1
            stun_every = 3 if self.phase < 3 else 4
            if self._attacks_done % stun_every == 0:
                self._state      = 'stun'
                self._stun_timer = self.STUN_FRAMES
            else:
                self._state      = 'idle'
                self._idle_timer = 40 if self.phase < 3 else 20

    def _do_stun(self):
        self._stun_timer -= 1
        if self._stun_timer <= 0:
            self._state      = 'idle'
            self._idle_timer = 30

    def _do_dead(self):
        self._dead_timer -= 1
        if random.random() < 0.4:
            self.particles.emit(
                self.rect.centerx + random.randint(-30,30),
                self.rect.centery + random.randint(-30,30),
                random.choice([C_BOSS, C_GOLD, C_WHITE]),
                count=6, speed=5, life=30)
        if self._dead_timer <= 0:
            self._death_done = True

    # ─── Attack patterns ──────────────────────────────────────────────────────
    def _fire(self, vx, vy, color=C_BOSS_BULLET, size=7, homing=False,
              target=None, bounce=0, damage=1):
        p = BossProjectile(
            self.rect.centerx, self.rect.centery,
            vx, vy, color, damage, size, homing, target, bounce)
        self.projectiles.add(p)

    # ── Phase 1 ───────────────────────────────────────────────────────────────
    def _atk_aimed_burst(self, player, platforms):
        T = self._attack_timer
        SHOTS = 5; GAP = 18; DONE = SHOTS*GAP + 30
        if T % GAP == 0 and T // GAP < SHOTS:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery  - self.rect.centery
            ang = math.atan2(dy, dx)
            spread = (T//GAP - SHOTS//2) * 0.18
            vx = math.cos(ang+spread) * BOSS_PROJ_SPD
            vy = math.sin(ang+spread) * BOSS_PROJ_SPD
            self._fire(vx, vy)
        return T >= DONE

    def _atk_spiral(self, player, platforms):
        T   = self._attack_timer
        SPD = BOSS_PROJ_SPD * (1 + (self.phase-1)*0.3)
        if T < 120:
            if T % 6 == 0:
                base = math.tau * T / 60
                for arm in range(3):
                    ang = base + arm * (math.tau/3)
                    vx  = math.cos(ang) * SPD
                    vy  = math.sin(ang) * SPD
                    self._fire(vx, vy, size=6)
        return T >= 130

    def _atk_slam(self, player, platforms):
        T = self._attack_timer
        if T == 10:
            self.rect.centerx = clamp(player.rect.centerx, 80, 99999-80)
            self.rect.y -= 120
            self._target_y = float(self.rect.y)
        if T == 40:
            self.vel_y = 14
            self._state = 'intro'
        if T > 40 and self.on_ground:
            for ang_deg in range(0, 360, 30):
                ang = math.radians(ang_deg)
                vx  = math.cos(ang) * BOSS_PROJ_SPD
                vy  = math.sin(ang) * BOSS_PROJ_SPD * 0.5
                self._fire(vx, vy, color=C_BOSS, size=8)
            self.on_ground = False
            self._state    = 'idle'
            self._idle_timer = 50
            return True
        return T > 200

    # ── Phase 2 ───────────────────────────────────────────────────────────────
    def _atk_spread(self, player, platforms):
        T = self._attack_timer
        if T % 35 == 0 and T < 140:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery  - self.rect.centery
            base = math.atan2(dy, dx)
            for spread in [-0.35, 0, 0.35]:
                ang = base + spread
                spd = BOSS_PROJ_SPD * 1.2
                self._fire(math.cos(ang)*spd, math.sin(ang)*spd,
                           color=C_BOSS_2, size=7)
        return T >= 160

    def _atk_homing(self, player, platforms):
        T = self._attack_timer
        if T in (5, 30, 55):
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery  - self.rect.centery
            spd = BOSS_PROJ_SPD * 0.8
            ang = math.atan2(dy, dx)
            vx  = math.cos(ang) * spd
            vy  = math.sin(ang) * spd
            self._fire(vx, vy, color=(200,80,255), size=8,
                       homing=True, target=player)
        return T >= 120

    def _atk_bouncing(self, player, platforms):
        T = self._attack_timer
        if T == 5:
            for ang_deg in [30, 60, 120, 150]:
                ang = math.radians(ang_deg)
                spd = BOSS_PROJ_SPD
                self._fire(math.cos(ang)*spd, math.sin(ang)*spd,
                           color=(100,200,255), size=9, bounce=3)
        return T >= 200

    def _atk_wall(self, player, platforms):
        T = self._attack_timer
        WARN = 40; FIRE = 60
        if T == WARN:
            dx    = player.rect.centerx - self.rect.centerx
            self._wall_dir = 1 if dx > 0 else -1
            self._gap_y = player.rect.centery + random.randint(-60,60)
        if T == FIRE:
            cx = self.rect.centerx
            for y_off in range(-300, 301, 50):
                ty = self.rect.centery + y_off
                if abs(ty - self._gap_y) < 55:
                    continue
                vx = self._wall_dir * BOSS_PROJ_SPD * 1.3
                vy = 0
                p = BossProjectile(cx, ty, vx, vy,
                                   color=C_BOSS, size=10, damage=1)
                self.projectiles.add(p)
        return T >= 160

    # ── Phase 3 ───────────────────────────────────────────────────────────────
    def _atk_ring(self, player, platforms):
        T   = self._attack_timer
        SPD = BOSS_PROJ_SPD * 1.4
        if T in (5, 30, 55, 80, 105):
            offset = (T//25) * 0.2
            for deg in range(0, 360, 18):
                ang = math.radians(deg) + offset
                self._fire(math.cos(ang)*SPD, math.sin(ang)*SPD,
                           color=(255, 80+int(T), 200), size=6)
        return T >= 130

    def _atk_chaos(self, player, platforms):
        T   = self._attack_timer
        SPD = BOSS_PROJ_SPD * 1.5
        if T < 180 and T % 4 == 0:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery  - self.rect.centery
            ang = math.atan2(dy, dx)
            spread = random.uniform(-0.7, 0.7)
            ang += spread
            self._fire(math.cos(ang)*SPD, math.sin(ang)*SPD,
                       color=(200, random.randint(50,255), 255), size=7)
        return T >= 200

    def _atk_spiral_fast(self, player, platforms):
        T   = self._attack_timer
        SPD = BOSS_PROJ_SPD * 1.6
        if T < 150:
            if T % 3 == 0:
                base = math.tau * T / 40
                for arm in range(5):
                    ang = base + arm * (math.tau/5)
                    self._fire(math.cos(ang)*SPD, math.sin(ang)*SPD,
                               color=(255, 50, 180+(arm*15)%75), size=6)
        return T >= 165

    def _atk_grid(self, player, platforms):
        T = self._attack_timer
        SPD = BOSS_PROJ_SPD * 1.3
        if T % 25 == 0 and T < 200:
            row = (T // 25) % 2
            if row == 0:
                self._fire( SPD, 0, color=C_BOSS_BULLET, size=8)
                self._fire(-SPD, 0, color=C_BOSS_BULLET, size=8)
            else:
                vx = random.uniform(-1,1)
                self._fire(vx, SPD, color=C_BOSS_2, size=7)
        return T >= 220

    # ─── Image ────────────────────────────────────────────────────────────────
    def _update_image(self):
        if self._hit_timer > 0:
            self._hit_timer -= 1
            img = self._phase_surf[self.phase].copy()
            tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            tint.fill((255,255,255,180))
            img.blit(tint, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = img
        elif self._state == 'stun':
            img = self._phase_surf[self.phase].copy()
            tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            alpha = 100 + int(80 * math.sin(self._stun_timer * 0.3))
            tint.fill((*C_CYAN, alpha))
            img.blit(tint, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = img
        else:
            self.image = self._phase_surf[self.phase]

    # ─── Draw ─────────────────────────────────────────────────────────────────
    def draw(self, surface, cam_x, cam_y):
        self.particles.draw(surface, cam_x, cam_y)

        for p in self.projectiles:
            p.draw(surface, cam_x, cam_y)

        bx = self.rect.x - cam_x
        by = self.rect.y - cam_y
        surface.blit(self.image, (bx, by))

        if self.alive:
            bw = 320
            bh = 16
            hx = SCREEN_WIDTH//2 - bw//2
            hy = SCREEN_HEIGHT - 40
            pygame.draw.rect(surface, (30,10,20), (hx-2, hy-2, bw+4, bh+4),
                             border_radius=5)
            pygame.draw.rect(surface, (80, 20, 40), (hx, hy, bw, bh),
                             border_radius=4)
            fill = int(bw * (self.health / self.MAX_HEALTH))
            col  = [C_BOSS, C_BOSS_2, (200,0,255)][self.phase-1]
            pygame.draw.rect(surface, col, (hx, hy, fill, bh),
                             border_radius=4)
            for pct in [self.PHASE2_HP/self.MAX_HEALTH,
                        self.PHASE3_HP/self.MAX_HEALTH]:
                mx = hx + int(bw * pct)
                pygame.draw.line(surface, C_WHITE, (mx, hy), (mx, hy+bh), 2)
            pygame.draw.rect(surface, C_BOSS, (hx-2,hy-2,bw+4,bh+4), 1,
                             border_radius=5)

        if self._state == 'stun':
            from utils.helpers import draw_glow_text
            font_sm = pygame.font.SysFont('monospace', 16, bold=True)
            draw_glow_text(surface, "[ VULNERABLE – ATTACK NOW ]",
                           font_sm, C_CYAN,
                           SCREEN_WIDTH//2, SCREEN_HEIGHT - 62,
                           center=True)