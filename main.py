"""
main.py – Entry point and Game class.

State machine:
    MAIN_MENU   → show title screen
    CONTROLS    → show controls
    PLAYING     → main game loop
    PAUSED      → pause overlay
    LEVEL_TITLE → cinematic level name display
    LEVEL_END   → score tally between levels
    GAME_OVER   → death screen
    VICTORY     → end-game celebration

Run:
    python main.py
"""

import sys
import os
import pygame
import math
import random

sys.path.insert(0, os.path.dirname(__file__))

from settings import *
from player  import Player
from level   import Level
from ui      import (HUD, MainMenu, ControlsScreen, PauseMenu,
                     LevelTitle, GameOver, LevelComplete, VictoryScreen,
                     Transition)
from utils.helpers import (StarField, ScreenShake, FlashOverlay,
                            ParticleSystem, draw_glow_text, lerp, clamp,
                            make_bullet_surf)


# ──────────────────────────────────────────────────────────────────────────────
class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, target_rect, level_w, level_h):
        tx = target_rect.centerx - SCREEN_WIDTH  // 2
        ty = target_rect.centery - SCREEN_HEIGHT // 2
        self.x = lerp(self.x, tx, CAMERA_LERP)
        self.y = lerp(self.y, ty, CAMERA_LERP)
        self.x = clamp(self.x, 0, max(0, level_w  - SCREEN_WIDTH))
        self.y = clamp(self.y, 0, max(0, level_h  - SCREEN_HEIGHT))


# ──────────────────────────────────────────────────────────────────────────────
class Game:
    ST_MAIN_MENU   = 'main_menu'
    ST_CONTROLS    = 'controls'
    ST_PLAYING     = 'playing'
    ST_PAUSED      = 'paused'
    ST_LEVEL_TITLE = 'level_title'
    ST_LEVEL_END   = 'level_end'
    ST_GAME_OVER   = 'game_over'
    ST_VICTORY     = 'victory'

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)

        flags = pygame.HWSURFACE | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        self.clock  = pygame.time.Clock()

        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self._sounds = {}
        self._sfx_vol   = 0.7
        self._init_sounds()

        self.hud          = HUD()
        self.main_menu    = MainMenu()
        self.controls     = ControlsScreen()
        self.pause_menu   = PauseMenu()
        self.level_title  = LevelTitle()
        self.game_over_ui = GameOver()
        self.level_end_ui = LevelComplete()
        self.victory_ui   = VictoryScreen()
        self.transition   = Transition()

        self.shake        = ScreenShake()
        self.flash        = FlashOverlay()
        self.bg_stars     = StarField(120)
        self.world_particles = ParticleSystem()

        self.state         = self.ST_MAIN_MENU
        self.level_index   = 0
        self.player        = None
        self.level         = None
        self.camera        = Camera()

    # ─── Sound ────────────────────────────────────────────────────────────────
    def _init_sounds(self):
        try:
            import numpy as np

            def _beep(freq, dur, vol=0.5, wave='sine'):
                sr = 44100
                n  = int(sr * dur)
                t  = np.linspace(0, dur, n, False)
                if wave == 'sine':
                    data = np.sin(2*np.pi*freq*t)
                elif wave == 'square':
                    data = np.sign(np.sin(2*np.pi*freq*t))
                elif wave == 'noise':
                    data = np.random.uniform(-1, 1, n)
                else:
                    data = np.sin(2*np.pi*freq*t)
                env = np.ones(n)
                fade = min(int(sr*0.01), n//4)
                env[:fade]  = np.linspace(0, 1, fade)
                env[-fade:] = np.linspace(1, 0, fade)
                data = (data * env * vol * 32767).astype(np.int16)
                stereo = np.column_stack([data, data])
                return pygame.sndarray.make_sound(stereo)

            self._sounds['jump']      = _beep(440, 0.06, wave='sine')
            self._sounds['land']      = _beep(180, 0.05, wave='square')
            self._sounds['collect']   = _beep(880, 0.08, wave='sine')
            self._sounds['hurt']      = _beep(200, 0.12, wave='noise')
            self._sounds['enemy_die'] = _beep(300, 0.10, wave='square')
            self._sounds['shoot']     = _beep(660, 0.05, wave='square')
            self._sounds['boss_hit']  = _beep(150, 0.08, wave='noise')
            self._sounds['phase']     = _beep(100, 0.30, wave='square')
            self._sounds['checkpoint']= _beep(550, 0.15, wave='sine')
            self._sounds['victory']   = _beep(880, 0.5,  wave='sine')

        except Exception:
            pass

    def _play(self, name):
        s = self._sounds.get(name)
        if s:
            s.set_volume(self._sfx_vol)
            s.play()

    # ─── Main loop ────────────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / (1000/FPS)
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

    # ─── Events ───────────────────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()

            if self.state == self.ST_MAIN_MENU:
                self.main_menu.handle_event(event)
            elif self.state == self.ST_CONTROLS:
                self.controls.handle_event(event)
            elif self.state == self.ST_PAUSED:
                self.pause_menu.handle_event(event)
            elif self.state == self.ST_GAME_OVER:
                self.game_over_ui.handle_event(event)
            elif self.state == self.ST_LEVEL_END:
                self.level_end_ui.handle_event(event)
            elif self.state == self.ST_VICTORY:
                self.victory_ui.handle_event(event)
            elif self.state == self.ST_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.pause_menu.reset()
                        self.state = self.ST_PAUSED

    # ─── Update ───────────────────────────────────────────────────────────────
    def _update(self, dt):
        self.transition.update()
        self.flash.update()
        self.shake.update()

        if self.state == self.ST_MAIN_MENU:
            self._upd_main_menu()
        elif self.state == self.ST_CONTROLS:
            self._upd_controls()
        elif self.state == self.ST_PLAYING:
            self._upd_playing(dt)
        elif self.state == self.ST_PAUSED:
            self._upd_paused()
        elif self.state == self.ST_LEVEL_TITLE:
            self._upd_level_title()
        elif self.state == self.ST_LEVEL_END:
            self._upd_level_end()
        elif self.state == self.ST_GAME_OVER:
            self._upd_game_over()
        elif self.state == self.ST_VICTORY:
            self._upd_victory()

    def _upd_main_menu(self):
        r = self.main_menu.result
        if r == 'new_game':
            self.main_menu.reset()
            self._start_game()
        elif r == 'controls':
            self.main_menu.reset()
            self.controls.reset()
            self.state = self.ST_CONTROLS
        elif r == 'quit':
            self._quit()

    def _upd_controls(self):
        if self.controls.done:
            self.controls.reset()
            self.state = self.ST_MAIN_MENU

    def _upd_paused(self):
        r = self.pause_menu.result
        if r == 'resume':
            self.pause_menu.reset()
            self.state = self.ST_PLAYING
        elif r == 'main_menu':
            self.pause_menu.reset()
            self.state = self.ST_MAIN_MENU
        elif r == 'quit':
            self._quit()

    def _upd_level_title(self):
        self.level_title.update()
        if not self.level_title.active:
            self.state = self.ST_PLAYING

    def _upd_level_end(self):
        self.level_end_ui.update()
        r = self.level_end_ui.result
        if r == 'next':
            self.level_end_ui._active = False
            self.level_index += 1
            if self.level_index >= TOTAL_LEVELS:
                self.state = self.ST_VICTORY
                self.victory_ui.reset()
            else:
                self._load_level(self.level_index)

    def _upd_game_over(self):
        self.game_over_ui.update()
        r = self.game_over_ui.result
        if r == 'respawn':
            self.game_over_ui.reset()
            self._respawn_player()
        elif r == 'menu':
            self.game_over_ui.reset()
            self.state = self.ST_MAIN_MENU

    def _upd_victory(self):
        self.victory_ui.update()
        if self.victory_ui.result == 'menu':
            self.victory_ui.reset()
            self.state = self.ST_MAIN_MENU

    # ─── Core gameplay update ─────────────────────────────────────────────────
    def _upd_playing(self, dt):
        if self.player is None or self.level is None:
            return

        keys = pygame.key.get_pressed()

        self.level.update(self.player)
        self.player.update(keys, self.level.platforms, self.level.hazards, dt)
        self.camera.update(self.player.rect,
                           self.level.width, self.level.height)

        self._check_battery_collect()
        self._check_checkpoint()
        self._check_enemy_contact()
        self._check_projectile_hit()
        self._check_boss_projectiles()
        self._check_exit()

        if self.level.boss and self.level.boss.alive:
            self._check_boss_hit()

        self.world_particles.update()

        if not self.player.alive and self.player.dead_timer <= 0:
            self.game_over_ui.reset()
            self.state = self.ST_GAME_OVER

        if self.player.rect.top > self.level.height + 100:
            self.player.take_damage(self.player.health)

        if (self.level.boss
                and self.level.boss.dead
                and self.state == self.ST_PLAYING):
            self._play('victory')
            self.flash.flash(C_GOLD, 255, fade_speed=4)
            self.shake.shake(12, 60)
            self._trigger_level_end()

    def _check_battery_collect(self):
        p = self.player
        for bat in list(self.level.batteries):
            if p.rect.colliderect(bat.rect):
                self.level.batteries.remove(bat)
                p.batteries += 1
                p.score     += BATTERY_SCORE
                self._play('collect')
                self.world_particles.emit(
                    bat.rect.centerx, bat.rect.centery,
                    C_BATTERY, count=10, speed=4, life=25)

    def _check_checkpoint(self):
        p = self.player
        for cp in self.level.checkpoints:
            if not cp.active and p.rect.colliderect(cp.rect):
                cp.activate()
                p.respawn_x = cp.rect.centerx
                p.respawn_y = cp.rect.top
                p.heal(1)
                self._play('checkpoint')
                self.flash.flash(C_CHECKPOINT, 80, fade_speed=6)
                self.world_particles.emit(
                    cp.rect.centerx, cp.rect.top,
                    C_CHECKPOINT, count=14, speed=5, life=30)

    def _check_enemy_contact(self):
        p = self.player
        if p.inv_timer > 0:
            return
        for enemy in list(self.level.enemies):
            if not p.rect.colliderect(enemy.rect):
                continue
            if (p.vel_y > 1
                    and p.rect.bottom <= enemy.rect.top + 16
                    and p.rect.bottom >= enemy.rect.top - 8):
                enemy.take_damage(enemy.health)
                p.vel_y = JUMP_STRENGTH * 0.65
                p.score += ENEMY_SCORE
                self._play('enemy_die')
                self.shake.shake(3, 6)
                self.world_particles.emit(
                    enemy.rect.centerx, enemy.rect.centery,
                    C_ENEMY_1, count=14, speed=5, life=28)
            else:
                p.take_damage(enemy.damage,
                               enemy.rect.centerx, enemy.rect.centery)
                self._play('hurt')
                self.shake.shake(5, 10)
                self.flash.flash(C_HEART_FULL, 80, fade_speed=8)

    def _check_projectile_hit(self):
        p = self.player
        if p.inv_timer > 0:
            return
        for proj in list(self.level.projectiles):
            if p.rect.colliderect(proj.rect):
                p.take_damage(proj.damage, proj.rect.centerx, proj.rect.centery)
                proj.kill()
                self._play('hurt')
                self.shake.shake(4, 8)
                self.flash.flash(C_HEART_FULL, 70, fade_speed=7)

    def _check_boss_projectiles(self):
        if not self.level.boss:
            return
        p = self.player
        if p.inv_timer > 0:
            return
        for proj in list(self.level.boss.projectiles):
            if p.rect.colliderect(proj.rect):
                p.take_damage(proj.damage, proj.rect.centerx, proj.rect.centery)
                proj.kill()
                self._play('hurt')
                self.shake.shake(6, 12)
                self.flash.flash(C_HEART_FULL, 100, fade_speed=8)

    def _check_boss_hit(self):
        b  = self.level.boss
        p  = self.player
        if not b or not b.alive:
            return
        if not p.rect.colliderect(b.rect):
            return

        stomp = (p.vel_y > 1
                 and p.rect.bottom <= b.rect.top + 20
                 and p.rect.bottom >= b.rect.top - 8)
        stun_touch = (b._state == 'stun')

        if stomp or stun_touch:
            b.take_damage(1,
                          shake_cb=self.shake.shake,
                          flash_cb=self.flash.flash)
            p.vel_y = JUMP_STRENGTH * 0.55
            self._play('boss_hit')
            if b._state == 'stun':
                self.shake.shake(5, 10)
        elif p.inv_timer == 0:
            p.take_damage(1, b.rect.centerx, b.rect.centery)
            self._play('hurt')
            self.shake.shake(5, 10)
            self.flash.flash(C_HEART_FULL, 80, fade_speed=8)

    def _check_exit(self):
        p = self.player
        if not p.alive:
            return
        if self.level.is_boss:
            return
        for ex in self.level.exits:
            if p.rect.colliderect(ex.rect):
                self._trigger_level_end()
                return

    def _trigger_level_end(self):
        self.level_end_ui.show(self.player.score, self.player.batteries)
        self.state = self.ST_LEVEL_END
        self.transition.fade_out(speed=12)

    # ─── Setup helpers ────────────────────────────────────────────────────────
    def _start_game(self):
        self.level_index = 0
        self._load_level(0)

    def _load_level(self, idx):
        self.level  = Level(idx)
        sx, sy      = self.level.player_start

        if self.player is None:
            self.player = Player(sx, sy)
        else:
            score    = self.player.score
            bats     = self.player.batteries
            health   = max(1, self.player.health)
            self.player = Player(sx, sy)
            self.player.score     = score
            self.player.batteries = bats
            self.player.health    = health

        self.player.respawn_x = sx
        self.player.respawn_y = sy
        self.camera.x = 0
        self.camera.y = 0
        self.world_particles.clear()

        self.level_title.show(LEVEL_NAMES[idx])
        self.state = self.ST_LEVEL_TITLE
        self.transition.fade_in(speed=10)

    def _respawn_player(self):
        self.player.respawn()
        score = self.player.score
        bats  = self.player.batteries
        self.level = Level(self.level_index)
        self.player.respawn_x, self.player.respawn_y = self.level.player_start
        self.player.rect.topleft = self.level.player_start
        self.player.score     = score
        self.player.batteries = bats
        self.world_particles.clear()
        self.state = self.ST_PLAYING
        self.transition.fade_in(speed=10)

    def _quit(self):
        pygame.quit()
        sys.exit()

    # ─── Draw ─────────────────────────────────────────────────────────────────
    def _draw(self):
        ox, oy = self.shake.offset
        cam_x  = int(self.camera.x) + ox
        cam_y  = int(self.camera.y) + oy

        surface = self.screen

        if self.state == self.ST_MAIN_MENU:
            self.main_menu.draw(surface)

        elif self.state == self.ST_CONTROLS:
            self.controls.draw(surface)

        elif self.state in (self.ST_PLAYING,
                             self.ST_PAUSED,
                             self.ST_LEVEL_TITLE,
                             self.ST_GAME_OVER):
            self._draw_game(surface, cam_x, cam_y)
            self.hud.draw(surface, self.player,
                          self.level.name, self.level_index, TOTAL_LEVELS)

            if self.state == self.ST_PAUSED:
                self.pause_menu.draw(surface)
            elif self.state == self.ST_LEVEL_TITLE:
                self.level_title.draw(surface)
            elif self.state == self.ST_GAME_OVER:
                self.game_over_ui.draw(surface)

        elif self.state == self.ST_LEVEL_END:
            if self.level:
                self._draw_game(surface, cam_x, cam_y)
            self.level_end_ui.draw(surface)

        elif self.state == self.ST_VICTORY:
            self.victory_ui.draw(surface)

        self.flash.draw(surface)
        self.transition.draw(surface)

    def _draw_game(self, surface, cam_x, cam_y):
        surface.fill(C_BG_DARK)
        self.bg_stars.draw(surface, cam_x, cam_y)
        self._draw_bg_grid(surface, cam_x, cam_y)

        if self.level is None:
            return

        self.level.draw(surface, cam_x, cam_y)
        self.world_particles.draw(surface, cam_x, cam_y)
        self.player.draw(surface, cam_x, cam_y)

    def _draw_bg_grid(self, surface, cam_x, cam_y):
        grid_size = 160
        ox = int(cam_x * 0.3) % grid_size
        oy = int(cam_y * 0.3) % grid_size
        for x in range(-ox, SCREEN_WIDTH + grid_size, grid_size):
            pygame.draw.line(surface, (*C_BG_MID, 80),
                             (x, 0), (x, SCREEN_HEIGHT))
        for y in range(-oy, SCREEN_HEIGHT + grid_size, grid_size):
            pygame.draw.line(surface, (*C_BG_MID, 80),
                             (0, y), (SCREEN_WIDTH, y))


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    game = Game()
    game.run()