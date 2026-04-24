"""
enemy.py – Three enemy archetypes with distinct AI behaviors.

PatrolEnemy  – walks back and forth, turns at edges/walls.
ChaserEnemy  – detects player within radius, rushes toward them.
RangedEnemy  – stands/floats, fires projectiles at player on cooldown.
"""

import pygame
import math
import random
from settings import *
from utils.helpers import (make_enemy_surf, make_bullet_surf,
                            ParticleSystem, distance)


class Projectile(pygame.sprite.Sprite):
    """A simple projectile fired by RangedEnemy (or boss)."""

    def __init__(self, x, y, vx, vy, color=C_BULLET, damage=1, size=5):
        super().__init__()
        self.image   = make_bullet_surf(size, color)
        self.rect    = self.image.get_rect(center=(x, y))
        self.vx      = vx
        self.vy      = vy
        self.damage  = damage
        self.color   = color
        self._life   = 300

    def update(self, platforms=None):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self._life  -= 1

        if (self._life <= 0
                or self.rect.right < 0
                or self.rect.left  > 99999
                or self.rect.bottom < -200
                or self.rect.top   > 99999):
            self.kill()

        if platforms:
            for p in platforms:
                if self.rect.colliderect(p.rect):
                    self.kill()
                    return

    def draw(self, surface, cam_x, cam_y):
        gx = self.rect.x - cam_x
        gy = self.rect.y - cam_y
        gs = pygame.Surface((self.rect.width+8, self.rect.height+8), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (*self.color, 60),
                            (0, 0, gs.get_width(), gs.get_height()))
        surface.blit(gs, (gx-4, gy-4))
        surface.blit(self.image, (gx, gy))


# ──────────────────────────────────────────────────────────────────────────────
class BaseEnemy(pygame.sprite.Sprite):
    """Shared logic for all enemies."""

    def __init__(self, x, y, width, height, health, etype):
        super().__init__()
        self._etype  = etype
        self._w, self._h = width, height
        self._base_surf  = make_enemy_surf(etype, width, height)
        self.image       = self._base_surf.copy()
        self.rect        = self.image.get_rect(topleft=(x, y))

        self.health      = health
        self.max_health  = health
        self.alive       = True
        self.damage      = 1
        self.score_value = ENEMY_SCORE

        self.vel_x       = 0.0
        self.vel_y       = 0.0
        self.on_ground   = False
        self.facing      = 1

        self.hit_timer   = 0
        self.particles   = ParticleSystem()

    # ─── Physics ──────────────────────────────────────────────────────────────
    def _apply_gravity(self):
        self.vel_y += GRAVITY * 0.7
        self.vel_y  = min(self.vel_y, MAX_FALL_SPEED)

    def _move_and_collide(self, platforms):
        self.rect.x    += int(self.vel_x)
        self.on_ground  = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_x > 0:
                    self.rect.right = p.rect.left; self.vel_x = 0
                elif self.vel_x < 0:
                    self.rect.left  = p.rect.right; self.vel_x = 0

        self.rect.y += int(self.vel_y)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    self.rect.bottom = p.rect.top
                    self.vel_y       = 0
                    self.on_ground   = True
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel_y    = 0

    # ─── Damage ───────────────────────────────────────────────────────────────
    def take_damage(self, amount):
        if not self.alive:
            return
        self.health   -= amount
        self.hit_timer = 10
        self.particles.emit(self.rect.centerx, self.rect.centery,
                            C_WHITE, count=6, speed=3, life=18)
        if self.health <= 0:
            self.die()

    def die(self):
        self.alive = False
        self.particles.emit(self.rect.centerx, self.rect.centery,
                            [C_ENEMY_1, C_ENEMY_2, C_ENEMY_3][self._etype-1],
                            count=18, speed=5, life=35)
        self.kill()

    # ─── Sprite tinting ───────────────────────────────────────────────────────
    def _update_image(self):
        self.particles.update()
        if self.hit_timer > 0:
            self.hit_timer -= 1
            tinted = self._base_surf.copy()
            tint   = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
            tint.fill((255,255,255,160))
            tinted.blit(tint, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
            img = tinted
        else:
            img = self._base_surf.copy()

        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)
        self.image = img

    def draw(self, surface, cam_x, cam_y):
        self.particles.draw(surface, cam_x, cam_y)
        ex = self.rect.x - cam_x
        ey = self.rect.y - cam_y
        surface.blit(self.image, (ex, ey))
        if self.health < self.max_health:
            bw = self._w
            bh = 4
            bx, by = ex, ey - 8
            pygame.draw.rect(surface, (60,20,20), (bx, by, bw, bh), border_radius=2)
            fill = int(bw * (self.health / self.max_health))
            pygame.draw.rect(surface, C_ENEMY_1, (bx, by, fill, bh), border_radius=2)


# ──────────────────────────────────────────────────────────────────────────────
class PatrolEnemy(BaseEnemy):
    """Walks left/right on platforms. Turns at edges and walls."""

    def __init__(self, x, y, patrol_range=180):
        super().__init__(x, y, 32, 36, health=3, etype=1)
        self._start_x    = x
        self._patrol_rng = patrol_range
        self.vel_x       = PATROL_SPEED
        self.facing      = 1

    def update(self, player, platforms, projectiles):
        self._apply_gravity()
        self._patrol(platforms)
        self._move_and_collide(platforms)
        self._update_image()

    def _patrol(self, platforms):
        if abs(self.rect.centerx - self._start_x) >= self._patrol_rng:
            self.vel_x  = -self.vel_x
            self.facing = -1 if self.vel_x < 0 else 1

        check_x = self.rect.right + 4 if self.vel_x > 0 else self.rect.left - 4
        ground_ahead = any(
            p.rect.left <= check_x <= p.rect.right
            and p.rect.top >= self.rect.bottom
            and p.rect.top <= self.rect.bottom + 12
            for p in platforms
        )
        if not ground_ahead and self.on_ground:
            self.vel_x  = -self.vel_x
            self.facing = -1 if self.vel_x < 0 else 1


# ──────────────────────────────────────────────────────────────────────────────
class ChaserEnemy(BaseEnemy):
    """Detects player within radius, accelerates toward them."""

    DETECT_RADIUS = 280
    LOSE_RADIUS   = 400
    JUMP_COOLDOWN = 60

    def __init__(self, x, y):
        super().__init__(x, y, 30, 34, health=4, etype=2)
        self._idle_x     = x
        self._chasing    = False
        self._jump_cd    = 0
        self.damage      = 1

    def update(self, player, platforms, projectiles):
        self._apply_gravity()
        self._chase_ai(player, platforms)
        self._move_and_collide(platforms)
        self._update_image()

    def _chase_ai(self, player, platforms):
        if self._jump_cd > 0:
            self._jump_cd -= 1

        dist = distance(self.rect.centerx, self.rect.centery,
                        player.rect.centerx, player.rect.centery)

        if dist < self.DETECT_RADIUS:
            self._chasing = True
        elif dist > self.LOSE_RADIUS:
            self._chasing = False

        if self._chasing and player.alive:
            dx = player.rect.centerx - self.rect.centerx
            target_vx = CHASER_SPEED * (1 if dx > 0 else -1)
            self.vel_x += (target_vx - self.vel_x) * 0.18
            self.facing = 1 if dx > 0 else -1
            if (player.rect.centery < self.rect.centery - 40
                    and self.on_ground
                    and self._jump_cd == 0):
                self.vel_y     = JUMP_STRENGTH * 0.8
                self._jump_cd  = self.JUMP_COOLDOWN
        else:
            if abs(self.rect.centerx - self._idle_x) > 10:
                dx = self._idle_x - self.rect.centerx
                self.vel_x = PATROL_SPEED * 0.7 * (1 if dx > 0 else -1)
                self.facing = 1 if dx > 0 else -1
            else:
                self.vel_x *= 0.85


# ──────────────────────────────────────────────────────────────────────────────
class RangedEnemy(BaseEnemy):
    """Floats in place. Fires projectiles at player when in range."""

    ATTACK_RANGE  = 500
    SHOOT_COOLDOWN = 90

    def __init__(self, x, y, floating=True):
        super().__init__(x, y, 32, 36, health=2, etype=3)
        self._floating    = floating
        self._float_base  = float(y)
        self._float_timer = random.uniform(0, math.tau)
        self._shoot_cd    = random.randint(0, self.SHOOT_COOLDOWN)
        self.damage       = 1

    def update(self, player, platforms, projectiles):
        self._float_timer += 0.04
        if self._floating:
            target_y  = self._float_base + math.sin(self._float_timer) * 18
            self.rect.y = int(target_y)
        else:
            self._apply_gravity()
            self._move_and_collide(platforms)

        self._shoot_ai(player, projectiles)
        self._update_image()

    def _shoot_ai(self, player, projectiles):
        if self._shoot_cd > 0:
            self._shoot_cd -= 1
            return
        if not player.alive:
            return

        dist = distance(self.rect.centerx, self.rect.centery,
                        player.rect.centerx, player.rect.centery)
        if dist > self.ATTACK_RANGE:
            return

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery  - self.rect.centery
        length = math.hypot(dx, dy) or 1
        vx = (dx / length) * PROJECTILE_SPD
        vy = (dy / length) * PROJECTILE_SPD

        proj = Projectile(self.rect.centerx, self.rect.centery,
                          vx, vy, color=C_ENEMY_3, damage=1)
        projectiles.add(proj)
        self._shoot_cd = self.SHOOT_COOLDOWN
        self.facing    = 1 if dx > 0 else -1