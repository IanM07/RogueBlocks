import pygame

# Screen dimensions
screen_width, screen_height = 1080, 720
screen = pygame.display.set_mode((screen_width, screen_height))

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

# Player and Enemy variables
initial_player_x = screen_width // 2
initial_player_y = screen_height // 2
number_of_enemies = 10
projectiles = []
powerups = []
enemies_per_wave = 5
wave_increase_factor = 3

# Multiplayer variables
is_multiplayer = False  # Global flag
network_socket = None
is_host = False
