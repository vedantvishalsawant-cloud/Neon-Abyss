"""
settings.py - Global game configuration and constants.
All tunable parameters live here so nothing is hard-coded elsewhere.
"""

# ─── Window ───────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60
TITLE         = "NEON ABYSS: Circuit Breaker"

# ─── Physics ──────────────────────────────────────────────────────────────────
GRAVITY          = 0.55
MAX_FALL_SPEED   = 18
PLAYER_SPEED     = 5.2
PLAYER_ACCEL     = 0.55
PLAYER_FRICTION  = 0.82
JUMP_STRENGTH    = -13.5
DOUBLE_JUMP_STR  = -11.0

# ─── Player ───────────────────────────────────────────────────────────────────
PLAYER_MAX_HEALTH   = 5
PLAYER_WIDTH        = 32
PLAYER_HEIGHT       = 44
INVINCIBILITY_FRAMES = 90
COYOTE_TIME         = 8
JUMP_BUFFER_FRAMES  = 10

# ─── Camera ───────────────────────────────────────────────────────────────────
CAMERA_LERP = 0.12

# ─── Enemies ──────────────────────────────────────────────────────────────────
PATROL_SPEED    = 1.8
CHASER_SPEED    = 2.4
RANGED_SPEED    = 1.2
PROJECTILE_SPD  = 5.0
BOSS_PROJ_SPD   = 4.5

# ─── Score & Collectibles ─────────────────────────────────────────────────────
BATTERY_SCORE   = 100
ENEMY_SCORE     = 250
BOSS_SCORE      = 5000

# ─── Colors (neon cyberpunk palette) ─────────────────────────────────────────
C_BG_DARK    = (8,   10,  24)
C_BG_MID     = (14,  18,  42)
C_PLATFORM   = (20,  30,  70)
C_PLAT_EDGE  = (60,  90, 200)
C_PLAYER     = (80, 220, 255)
C_PLAYER_2   = (40, 140, 220)
C_ENEMY_1    = (255,  80,  80)
C_ENEMY_2    = (255, 160,  40)
C_ENEMY_3    = (220,  60, 255)
C_BOSS       = (255,  50, 120)
C_BOSS_2     = (255, 120,  30)
C_BATTERY    = (60,  255, 160)
C_ACID       = (80,  255,  60)
C_SPIKE      = (200, 200, 220)
C_BULLET     = (255, 255,  80)
C_BOSS_BULLET= (255,  80, 180)
C_UI_BAR     = (40,   50, 110)
C_HEART_FULL = (255,  80, 120)
C_HEART_EMPTY= (60,   20,  40)
C_WHITE      = (255, 255, 255)
C_BLACK      = (0,    0,   0)
C_GOLD       = (255, 220,  50)
C_CYAN       = (0,  220, 255)
C_TEXT_MAIN  = (200, 230, 255)
C_TEXT_DIM   = (80,  100, 160)
C_CHECKPOINT = (255, 200,  50)
C_MOVING_PLAT= (30,  80, 180)

# ─── Tile size ────────────────────────────────────────────────────────────────
TILE = 40

# ─── UI ───────────────────────────────────────────────────────────────────────
HUD_HEIGHT = 56

# ─── Level metadata ───────────────────────────────────────────────────────────
LEVEL_NAMES = [
    "SECTOR 01 – Bootstrap",
    "SECTOR 02 – Overclock",
    "SECTOR 03 – Acid Rain",
    "SECTOR 04 – Moving Parts",
    "SECTOR 05 – Dark Matter",
    "SECTOR 06 – Voltage",
    "SECTOR 07 – Overload",
    "SECTOR 08 – The Grid",
    "SECTOR 09 – Deep Core",
    "SECTOR 10 – Zero Hour",
    "SECTOR 11 – Meltdown",
    "SECTOR 12 – FINAL BOSS",
]
TOTAL_LEVELS = len(LEVEL_NAMES)