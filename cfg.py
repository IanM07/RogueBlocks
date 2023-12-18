import pygame

# Screen dimensions
screen_width, screen_height = 1800, 900
screen = pygame.display.set_mode((screen_width, screen_height))

UI_WIDTH = 335
SCREEN_WIDTH = 1200  
SCREEN_HEIGHT = 900


# HP and Stamina Bar Constants
BAR_WIDTH = 200
BAR_HEIGHT = 30
BAR_X = screen_width - BAR_WIDTH - 10
BAR_Y = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (40, 224, 70)
BLUE = (128, 220, 255)
DARK_BLUE = (50, 50, 255)
GRAY = (171, 197, 207)
YELLOW = (255, 255, 0)
PURPLE = (129, 0, 204)

# Player and Enemy variables
initial_player_x = screen_width // 2
initial_player_y = screen_height // 2
number_of_enemies = 10
projectiles = []
powerups = []
upgrade_tile_groups = []
enemies_per_wave = 5
wave_increase_factor = 3
upgrade_selected = False
powerup_info = {
    "health_orb": {"chance": 10, "color": RED},       
    "invincibility": {"chance": 2.5, "color": YELLOW},   
    "infinite_stamina": {"chance": 2.5, "color": GREEN},
    "shoot_speed_boost": {"chance": 5, "color": WHITE},
    "move_speed_boost": {"chance": 5, "color": PURPLE}
}
