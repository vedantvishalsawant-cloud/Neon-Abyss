"""
player.py – Player entity with smooth physics, double-jump, invincibility frames,
            animation state machine, and complete health management.
"""

import pygame
from settings import *
from utils.helpers import (make_player_surf, ParticleSystem,
                            clamp, make_heart_surf)


class Player(pygame.sprite.Sprite):
    """
    The player character.

    Physics model:
        Horizontal: acceleration/friction model (feels snappy yet smooth).
        Vertical:   variable-height jump + coyote time + jump buffering.
    """

    # Animation frame durations (ticks per frame)
    ANIM_IDLE_SPD  = 24
    ANIM_RUN_SPD   = 6
    ANIM_JUMP_SPD  = 12

    def __init__(self, x, y):
        super().__init__()

        # ── Sprites ──────────────────────────────────────────────────────────
        self._build_sprites()

        self.image = self.sprites['idle'][0]
        self.rect  = self.image.get_rect(topleft=(x, y))

        # ── Physics ──────────────────────────────────────────────────────────
        self.vel_x      = 0.0
        self.vel_y      = 0.0
        self.on_ground  = False
        self.facing     = 1     # 1=right, -1=left

        # Jump helpers
        self.coyote_timer      = 0
        self.jump_buffer_timer = 0
        self.jumps_left        = 2   # allows double jump

        # ── Health ───────────────────────────────────────────────────────────
        self.max_health  = PLAYER_MAX_HEALTH
        self.health      = self.max_health
        self.alive       = True
        self.inv_timer   = 0    # invincibility frames remaining

        # ── Score / Collectibles ─────────────────────────────────────────────
        self.batteries   = 0
        self.score       = 0

        # ── Animation state ──────────────────────────────────────────────────
        self._anim_state  = 'idle'
        self._anim_frame  = 0
        self._anim_timer  = 0

        # ── Particles ────────────────────────────────────────────────────────
        self.particles    = ParticleSystem()

        # ── Misc ─────────────────────────────────────────────────────────────
        self.dead_timer   = 0
        self._was_grounded = False
        self.dash_timer   = 0
        self.respawn_x    = x
        self.respawn_y    = y

    # ─── Sprite sheet builder ──────────────────────────────────────────────────
    def _build_sprites(self):
        base   = make_player_surf()
        flip   = pygame.transform.flip(base, True, False)

        idle0  = base.copy()
        idle1  = base.copy()
        bright = pygame.Surface(base.get_size(), pygame.SRCALPHA)
        bright.fill((30, 30, 30, 0))
        idle1.blit(bright, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

        def make_run_frame(shift):
            s = base.copy()
            leg_region = pygame.Surface((PLAYER_WIDTH, 14), pygame.SRCALPHA)
            leg_region.fill((0,0,0,0))
            col2 = C_PLAYER_2
            lx = 6 + shift
            pygame.draw.rect(leg_region, col2, (lx, 0, 8, 14), border_radius=2)
            pygame.draw.rect(leg_region, col2, (PLAYER_WIDTH-14-shift, 0, 8, 14), border_radius=2)
            s.blit(leg_region, (0, PLAYER_HEIGHT-14))
            return s

        run0 = make_run_frame(0)
        run1 = make_run_frame(2)
        run2 = make_run_frame(0)
        run3 = make_run_frame(-2)

        jump0 = pygame.transform.scale(base, (PLAYER_WIDTH-2, PLAYER_HEIGHT+4))
        jump1 = pygame.transform.scale(base, (PLAYER_WIDTH+4, PLAYER_HEIGHT-4))

        hurt  = base.copy()
        tint  = pygame.Surface(base.get_size(), pygame.SRCALPHA)
        tint.fill((200, 0, 0, 100))
        hurt.blit(tint, (0,0), special_flags=pygame.BLEND_RGBA_MULT)

        dead  = pygame.transform.rotate(base, 90)

        self.sprites = {
            'idle': [idle0, idle1],
            'run' : [run0, run1, run2, run3],
            'jump': [jump0, jump1],
            'hurt': [hurt],
            'dead': [dead],
        }

    # ─── Update ───────────────────────────────────────────────────────────────
    def update(self, keys, platforms, hazards, dt=1.0):
        """Main update: input → physics → collision → animation."""
        if not self.alive:
            self._handle_death()
            self.particles.update()
            return

        self._handle_input(keys)
        self._apply_physics()
        self._collide_platforms(platforms)
        self._collide_hazards(hazards)
        self._tick_timers()
        self._animate()
        self.particles.update()

    # ─── Input ────────────────────────────────────────────────────────────────
    def _handle_input(self, keys):
        # Support both pygame key sequence and dict-like stubs
        def k(code):
            try:
                return bool(keys[code])
            except (KeyError, IndexError):
                return False

        # Horizontal movement
        if k(pygame.K_LEFT) or k(pygame.K_a):
            self.vel_x -= PLAYER_ACCEL * 1.5
            self.vel_x  = max(self.vel_x, -PLAYER_SPEED)
            self.facing = -1
        elif k(pygame.K_RIGHT) or k(pygame.K_d):
            self.vel_x += PLAYER_ACCEL * 1.5
            self.vel_x  = min(self.vel_x, PLAYER_SPEED)
            self.facing = 1
        else:
            self.vel_x *= PLAYER_FRICTION

        if abs(self.vel_x) < 0.1:
            self.vel_x = 0

        # Jump
        jump_pressed = k(pygame.K_SPACE) or k(pygame.K_UP) or k(pygame.K_w)
        if jump_pressed:
            self.jump_buffer_timer = JUMP_BUFFER_FRAMES

        if self.jump_buffer_timer > 0:
            if self.coyote_timer > 0 or self.jumps_left > 0:
                self._do_jump()
                self.jump_buffer_timer = 0

        # Variable jump height
        if not jump_pressed and self.vel_y < -4:
            self.vel_y *= 0.88

    def _do_jump(self):
        if self.coyote_timer > 0:
            self.vel_y = JUMP_STRENGTH
            self.coyote_timer = 0
            self.jumps_left = max(0, self.jumps_left - 1)
            self.on_ground = False
        elif self.jumps_left > 0:
            self.vel_y = DOUBLE_JUMP_STR
            self.jumps_left -= 1
        self.particles.emit_burst(
            self.rect.centerx, self.rect.bottom,
            C_CYAN, direction_y=1, count=8, speed=3)

    # ─── Physics ──────────────────────────────────────────────────────────────
    def _apply_physics(self):
        self.vel_y += GRAVITY
        self.vel_y  = min(self.vel_y, MAX_FALL_SPEED)
        self.rect.x += int(self.vel_x)
        self.rect.y += int(self.vel_y)

    # ─── Collision ────────────────────────────────────────────────────────────
    def _collide_platforms(self, platforms):
        self._was_grounded = self.on_ground
        self.on_ground = False

        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if (self.vel_y > 0
                        and self.rect.bottom - self.vel_y <= plat.rect.top + 4):
                    self.rect.bottom = plat.rect.top
                    self.vel_y       = 0
                    self.on_ground   = True
                    self.jumps_left  = 2
                    self.coyote_timer = COYOTE_TIME
                    if not self._was_grounded:
                        self.particles.emit_burst(
                            self.rect.centerx, self.rect.bottom,
                            C_TEXT_DIM, direction_y=-1, count=10, speed=2.5)
                elif (self.vel_y < 0
                        and self.rect.top - self.vel_y >= plat.rect.bottom - 4):
                    self.rect.top = plat.rect.bottom
                    self.vel_y    = 0
                elif self.vel_x > 0 and self.rect.right > plat.rect.left:
                    self.rect.right = plat.rect.left
                    self.vel_x      = 0
                elif self.vel_x < 0 and self.rect.left < plat.rect.right:
                    self.rect.left  = plat.rect.right
                    self.vel_x      = 0

        if not self.on_ground:
            self.coyote_timer = max(0, self.coyote_timer - 1)

    def _collide_hazards(self, hazards):
        if self.inv_timer > 0:
            return
        for haz in hazards:
            if self.rect.colliderect(haz.rect):
                self.take_damage(1, haz.rect.centerx, haz.rect.centery)
                break

    # ─── Health & Damage ──────────────────────────────────────────────────────
    def take_damage(self, amount, src_x=None, src_y=None):
        if self.inv_timer > 0 or not self.alive:
            return
        self.health   -= amount
        self.inv_timer = INVINCIBILITY_FRAMES
        if src_x is not None:
            direction = 1 if self.rect.centerx > src_x else -1
            self.vel_x = direction * 5
            self.vel_y = -5
        self.particles.emit(self.rect.centerx, self.rect.centery,
                            C_HEART_FULL, count=12, speed=4, life=25)
        if self.health <= 0:
            self.health = 0
            self.alive  = False
            self.dead_timer = 90

    def heal(self, amount=1):
        self.health = min(self.max_health, self.health + amount)

    # ─── Timers ───────────────────────────────────────────────────────────────
    def _tick_timers(self):
        if self.inv_timer > 0:
            self.inv_timer -= 1
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= 1

    def _handle_death(self):
        self.dead_timer -= 1
        self.vel_y += GRAVITY * 0.5
        self.rect.y += int(self.vel_y)
        self._set_anim('dead')

    # ─── Animation ────────────────────────────────────────────────────────────
    def _animate(self):
        if self.inv_timer > 0 and (self.inv_timer // 6) % 2 == 0:
            self.image = pygame.Surface((1,1), pygame.SRCALPHA)
            return

        if not self.on_ground:
            state = 'jump'
        elif abs(self.vel_x) > 0.5:
            state = 'run'
        else:
            state = 'idle'

        if state != self._anim_state:
            self._set_anim(state)

        frames     = self.sprites[self._anim_state]
        speed_map  = {'idle': self.ANIM_IDLE_SPD,
                       'run':  self.ANIM_RUN_SPD,
                       'jump': self.ANIM_JUMP_SPD,
                       'dead': 30, 'hurt': 20}
        anim_speed = speed_map.get(self._anim_state, 12)

        self._anim_timer += 1
        if self._anim_timer >= anim_speed:
            self._anim_timer = 0
            self._anim_frame = (self._anim_frame + 1) % len(frames)

        raw = frames[self._anim_frame]
        if self.facing == -1:
            raw = pygame.transform.flip(raw, True, False)
        self.image = raw

    def _set_anim(self, state):
        if self._anim_state != state:
            self._anim_state = state
            self._anim_frame = 0
            self._anim_timer = 0

    # ─── Draw ─────────────────────────────────────────────────────────────────
    def draw(self, surface, cam_x, cam_y):
        self.particles.draw(surface, cam_x, cam_y)
        if self.image.get_size() == (1,1):
            return
        surface.blit(self.image,
                     (self.rect.x - cam_x, self.rect.y - cam_y))

    # ─── Respawn ──────────────────────────────────────────────────────────────
    def respawn(self):
        self.rect.topleft = (self.respawn_x, self.respawn_y)
        self.vel_x = self.vel_y = 0
        self.health   = self.max_health
        self.alive    = True
        self.dead_timer = 0
        self.inv_timer  = 60
        self.jumps_left = 2
        self.particles.clear()