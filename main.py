import pygame
import sys
import json
import socket
import threading
import random
from cfg import *

class Player:
    def __init__(self):
        self.image = pygame.Surface((50,50))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect()
        self.speed = 3  # Normal speed
        self.base_speed = 3  # Normal speed
        self.sprint_speed = 6  # Sprinting speed
        self.base_sprint_speed = 6  # Sprinting speed
        self.is_sprinting = False
        self.x, self.y = float(initial_player_x), float(initial_player_y)
        self.hp = 10
        self.max_hp = 10
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_use_rate = self.max_stamina / 50  # Depletes over 3 seconds
        self.stamina_recovery_rate = self.stamina_use_rate  # Stamina recovered per update
        self.is_sprinting = False
        self.last_shot_time = 0
        self.shot_delay = 500
        self.base_shot_delay = 500
        self.damage_reduction = 0
        self.hp_regeneration_rate = 0
        self.invincible = False
        self.infinite_stamina = False
        self.powerup_timers = {}

    def handle_keys(self, keys):
        keys = pygame.key.get_pressed()
        sprint_requested = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        # Update sprinting status based on stamina level and sprint request
        if sprint_requested and self.stamina > 0:
            self.is_sprinting = True
        else:
            self.is_sprinting = False

        current_speed = self.sprint_speed if self.is_sprinting else self.speed
        if keys[pygame.K_a]:
            self.x -= current_speed
        if keys[pygame.K_d]:
            self.x += current_speed
        if keys[pygame.K_w]:
            self.y -= current_speed
        if keys[pygame.K_s]:
            self.y += current_speed

    def activate_powerup(self, powerup_type):
        if powerup_type == "invincibility":
            self.invincible = True
        elif powerup_type == "infinite_stamina":
            self.infinite_stamina = True
        elif powerup_type == "shoot_speed_boost":
            self.shot_delay = self.base_shot_delay * 0.5  # Example: 50% of original delay
        elif powerup_type == "move_speed_boost":
            self.sprint_speed = self.base_sprint_speed * 1.5
            self.speed = self.base_sprint_speed * 1.5
        elif powerup_type == "health_orb":
            self.hp = self.hp + 0.3*self.max_hp
            if (self.hp > self.max_hp):
                self.hp = self.max_hp

        # Set timer for power-up duration (e.g., 10 seconds)
        self.powerup_timers[powerup_type] = pygame.time.get_ticks() + 7000

    def deactivate_powerup(self, powerup_type):
        if powerup_type in self.powerup_timers:
            if powerup_type == "invincibility":
                self.invincible = False
            elif powerup_type == "infinite_stamina":
                self.infinite_stamina = False
            elif powerup_type == "shoot_speed_boost":
                self.shot_delay = self.base_shot_delay
            elif powerup_type == "move_speed_boost":
                self.speed = self.base_speed
                self.sprint_speed = self.base_sprint_speed

            del self.powerup_timers[powerup_type]

    def apply_upgrade(self, upgrade_name):
        if upgrade_name == "Increased Movement Speed":
            self.speed += self.base_speed * 0.1  # Increase speed by 10%
            self.sprint_speed += self.base_sprint_speed * 0.1  # Increase sprint speed as well

        elif upgrade_name == "Enhanced Fire Rate":
            self.shot_delay *= 0.9  # Decrease delay by 10%

        elif upgrade_name == "Extended Health":
            self.max_hp += self.max_hp * 0.1  # Increase maximum health by 10%
            self.hp = self.max_hp  # Refill health to the new max
            self.hp_regeneration_rate += self.hp_regeneration_rate*0.1

        elif upgrade_name == "Armor Upgrade":
            # Assuming you have a damage reduction attribute; if not, you'll need to create one
            self.damage_reduction = min(self.damage_reduction + 0.1, 0.8)  # Increase damage reduction by 10%, max of 100%

        elif upgrade_name == "Extended Stamina":
            self.max_stamina += self.max_stamina * 0.1  # Increase maximum stamina by 10%
            self.stamina = self.max_stamina  # Refill stamina to the new max

        elif upgrade_name == "Health Regeneration":
            self.hp_regeneration_rate += 0.01*self.max_hp  # Assuming you will handle this in the update method

        elif upgrade_name == "Stamina Regeneration Boost":
            self.stamina_recovery_rate += self.stamina_recovery_rate * 0.1  # Increase stamina recovery rate by 10%

    def update(self):
        # Sprinting depletes stamina
        # Sprinting depletes stamina, but only if infinite stamina is not active
        if self.is_sprinting and not self.infinite_stamina:
            self.stamina -= self.stamina_use_rate
            self.stamina = max(self.stamina, 0)

        # Regenerate stamina only when not sprinting and shift key is released
        keys = pygame.key.get_pressed()
        if not self.is_sprinting and not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
            self.stamina += self.stamina_recovery_rate
            self.stamina = min(self.stamina, self.max_stamina)

        current_time = pygame.time.get_ticks()
        for powerup_type in list(self.powerup_timers.keys()):
            if current_time > self.powerup_timers[powerup_type]:
                self.deactivate_powerup(powerup_type)

    def take_damage(self):
        current_time = pygame.time.get_ticks()
        if(self.invincible == False):
            self.hp = self.hp - 1 + self.damage_reduction  # Reduce HP by 1 - total damage reduction

    def shoot(self, target_x, target_y):
        # Calculate direction vector towards the target (mouse position)
        direction_x = target_x - self.x
        direction_y = target_y - self.y

        # Normalize the direction vector (to maintain constant projectile speed)
        magnitude = (direction_x**2 + direction_y**2)**0.5
        if magnitude != 0:
            direction_x /= magnitude
            direction_y /= magnitude

        # Set the speed of the projectile
        speed = 30
        x_velocity = direction_x * speed
        y_velocity = direction_y * speed

        # Create a new projectile
        projectile = Projectile(round(self.x + 25), round(self.y + 25), x_velocity, y_velocity)
        return projectile
            
    def draw(self, surface):
        surface.blit(self.image, (round(self.x), round(self.y)))

class Enemy:
    def __init__(self, x, y):
        self.image = pygame.Surface((40, 40))
        self.image.fill((255, 157, 0))  #Red color for the enemy
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 4
        self.x, self.y = float(x), float(y)
        self.damage = 1
        self.jitter_frequency = 120  # Adjust how often the enemy changes direction (in frames)
        self.jitter_strength = 0.1  # Adjust the strength of the direction change
        self.jitter_timer = 0
        self.target_dx = 0
        self.target_dy = 0

    def move_towards_player(self, player):
        # Increment jitter timer
        self.jitter_timer += 1

        # Regular movement towards the player
        dx = player.x - self.x
        dy = player.y - self.y
        distance = max((dx**2 + dy**2)**0.5, 1)  # Avoid division by zero
        dx, dy = dx / distance, dy / distance  # Normalize

        # Apply jitter to the direction
        if self.jitter_timer >= self.jitter_frequency:
            self.jitter_timer = 0
            self.target_dx = random.uniform(-self.jitter_strength, self.jitter_strength)
            self.target_dy = random.uniform(-self.jitter_strength, self.jitter_strength)

        # Update position
        self.x += dx * self.speed + self.target_dx
        self.y += dy * self.speed + self.target_dy

        self.rect.x, self.rect.y = round(self.x), round(self.y)  # Update rect position


    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Projectile:
    next_id = 0  # Class variable to generate unique IDs
    
    def __init__(self, x, y, x_velocity, y_velocity):
        self.image = pygame.Surface((10, 10))
        self.image.fill((255, 255, 255))  # White color for the projectile
        self.rect = self.image.get_rect(center=(x, y))
        self.x, self.y = float(self.rect.x), float(self.rect.y)
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.id = Projectile.next_id
        self.is_active = True  
        Projectile.next_id += 1

    def update(self):
        self.x += self.x_velocity
        self.y += self.y_velocity
        self.rect.x, self.rect.y = round(self.x), round(self.y)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class PowerUp:
    def __init__(self, x, y, powerup_types, color):
        self.x, self.y = x, y
        self.radius = 10
        self.types = powerup_types
        self.color = color
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Button:
    def __init__(self, text, x, y, width, height, action=None, action_args=[], bg_color=(255, 255, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.action = action
        self.action_args = action_args
        self.bg_color = bg_color

    def draw(self, screen):
        # Draw the button rectangle with the specified background color
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height))
        
        # Draw the text on the button
        font = pygame.font.SysFont("Arial", 20)
        text_surf = font.render(self.text, True, BLACK)  # White text
        text_rect = text_surf.get_rect(center=(self.x + self.width / 2, self.y + self.height / 2))
        screen.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        x, y = mouse_pos
        return (self.x <= x <= self.x + self.width) and (self.y <= y <= self.y + self.height)

    def activate(self):
        if self.action:
            return self.action(*self.action_args)  # Pass action_args to the function


class UpgradeTile:
    def __init__(self, upgrade_name, description, x, y, width, height):
        self.upgrade_name = upgrade_name
        self.description = description
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.button = Button("Choose", x + 10, y + height - 40, width - 20, 30, action=self.select_upgrade)

    def draw(self, screen):
        # Set the colors
        tile_color = (50, 50, 50)  # Dark gray background for the tile
        text_color = (255, 255, 255)  # White text
        button_color = (100, 100, 100)  # Light gray button
        border_color = (255, 255, 255)  # White border
        
        # Draw the tile background with border
        pygame.draw.rect(screen, border_color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, tile_color, (self.x + 2, self.y + 2, self.width - 4, self.height - 4))
        
        # Draw the upgrade name
        font = pygame.font.SysFont("Arial", 16)
        text_surf = font.render(self.upgrade_name, True, text_color)
        text_rect = text_surf.get_rect()
        text_rect.topleft = (self.x + 10, self.y + 10)
        screen.blit(text_surf, text_rect)

        # Draw the description text below the upgrade name
        desc_surf = font.render(self.description, True, text_color)
        desc_rect = desc_surf.get_rect()
        desc_rect.topleft = (self.x + 10, text_rect.bottom + 5)
        screen.blit(desc_surf, desc_rect)

        # Update the button color and draw it
        self.button.bg_color = button_color
        self.button.draw(screen)

    def select_upgrade(self):
        global local_player
        print(f"Upgrading to: {self.upgrade_name}")  # Debug print
        local_player.apply_upgrade(self.upgrade_name)


class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.buttons = []

    def add_button(self, button):
        self.buttons.append(button)

    def draw(self):
        for button in self.buttons:
            button.draw(self.screen)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            for button in self.buttons:
                if button.is_clicked(mouse_pos):
                    return button.activate()


def draw_bar(surface, value, max_value, x, y, width, height, bar_color, background_color):
    # Draw the background of the bar (empty part)
    pygame.draw.rect(surface, background_color, (x, y, width, height))

    # Calculate the width of the bar (current value)
    current_width = (value / max_value) * width

    # Draw the current value
    pygame.draw.rect(surface, bar_color, (x, y, current_width, height))

def draw_player_stats(screen, player):
    # Define the starting position
    start_x = 870  # adjust as needed for your screen layout
    start_y = 85
    line_height = 20  # space between lines

    # Calculate shots per second (Hz) and round to 2 decimal places for readability
    if player.shot_delay > 0:  # Prevent division by zero
        shots_per_second = round(1 / (player.shot_delay / 1000), 2)
    else:
        shots_per_second = 'Max'

    # Define stats to display
    stats = [
        f"Health: {player.hp}/{player.max_hp}",
        f"Health Regeneration: {player.hp_regeneration_rate}/s",
        f"Stamina: {player.stamina}/{player.max_stamina}",
        f"Stamina Regeneration: {player.stamina_recovery_rate}/s",
        f"Movement Speed: {player.speed} pixels/s",
        f"Fire Rate: {shots_per_second} shots/s",
        f"Damage Reduction: {player.damage_reduction}/hit",
    ]

    # Set the font for the stats
    font = pygame.font.SysFont("Arial", 16)
    
    # Draw each stat
    for i, stat in enumerate(stats):
        text_surface = font.render(stat, True, (255, 255, 255))  # White color text
        screen.blit(text_surface, (start_x, start_y + i * line_height))

def handle_player_input(player):
    current_time = pygame.time.get_ticks()
    keys = pygame.key.get_pressed()
    player.handle_keys(keys)

    # Mouse button handling for shooting
    mouse_button_down = pygame.mouse.get_pressed()[0]
    if mouse_button_down and current_time - player.last_shot_time > player.shot_delay:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        new_projectile = player.shoot(mouse_x, mouse_y)
        projectiles.append(new_projectile)
        player.last_shot_time = current_time

def initialize_upgrade_tiles(round_number):
    global upgrade_tiles
    available_upgrades = [
        ("Increased Movement Speed", "+10% Base Movement Speed"),
        ("Enhanced Fire Rate", "Decreases the delay between shots by 10%"),
        ("Extended Health", "+10% Base Health Points"),
        ("Armor Upgrade", "Reduces damage taken by 10%"),
        ("Extended Stamina", "+10% Maximum Stamina"),
        ("Health Regeneration", "Slowly regenerates health over time"),
        ("Stamina Regeneration Boost", "Increases stamina regeneration rate by 10%"),
        # Add other upgrades here if needed
    ]

    # Randomly select three unique upgrades
    selected_upgrades = random.sample(available_upgrades, 3)

    upgrade_tiles = []
    for i, (name, desc) in enumerate(selected_upgrades):
        tile_x = 10  # Adjust as needed
        tile_y = 50 + i * 110  # Adjust the vertical position based on the tile number
        tile_width = 300
        tile_height = 100
        upgrade_tiles.append(UpgradeTile(name, desc, tile_x, tile_y, tile_width, tile_height))

    return upgrade_tiles
        
def draw_text(surface, text, font_size, x, y, color=(255, 255, 255), center_x=False):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center_x:
        text_rect.centerx = surface.get_rect().centerx
    else:
        text_rect.x = x
    text_rect.y = y
    surface.blit(text_surface, text_rect)

def draw_game(screen, player, enemies, projectiles):
    screen.fill((0, 0, 0))  # Clear screen with black background

    # Draw player and remote player (in multiplayer mode)
    player.draw(screen)

    # Draw enemies and projectiles
    for enemy in enemies:
        enemy.draw(screen)

    # Draw power-ups
    for powerup in powerups:
        powerup.draw(screen)

    # Draw projectiles
    for projectile in projectiles:
        if projectile.is_active:
            projectile.draw(screen)

    # Draw UI elements (HP bar, Stamina bar, etc.)
    draw_bar(screen, player.hp, player.max_hp, BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT, RED, GRAY)
    draw_bar(screen, player.stamina, player.max_stamina, BAR_X, BAR_Y + 40, BAR_WIDTH, BAR_HEIGHT, GREEN, GRAY)
    draw_text(screen, f"Enemies Killed: {enemies_killed}", 55, 10, 10, WHITE)
    draw_text(screen, f"Wave: {current_wave}", 55, screen_width // 2 - 75, 10, WHITE)

    if in_intermission:
        time_left = max(0, (intermission_timer - pygame.time.get_ticks()) // 1000)
        draw_text(screen, f"Next Round Begins in: {time_left}s", 36, screen_width // 2, BAR_Y + BAR_HEIGHT + 10, WHITE, center_x=True)
        for tile_group in upgrade_tile_groups:
            for tile in tile_group:
                tile.draw(screen)
                
    # Updates player stats
    draw_player_stats(screen, local_player)


    pygame.display.flip()  # Update the full display Surface to the screen

def update_enemies(enemies, received_enemies_data):
    # Assuming that the number and order of enemies are the same
    # between the host and the remote player
    for i, enemy_data in enumerate(received_enemies_data):
        if i < len(enemies):
            enemy = enemies[i]
            enemy.x = enemy_data['x']
            enemy.y = enemy_data['y']
            # Update any other necessary attributes, like health, state, etc.
            # Example: enemy.hp = enemy_data['hp']

def update_game_state(local_player, enemies, projectiles):
    global enemies_killed

    # Update local player
    local_player.update()

    # Update enemies
    for enemy in enemies:
        # The enemy should move towards the nearest player
        enemy.move_towards_player(local_player)

    # Update projectiles
    for projectile in projectiles[:]:
        if projectile.is_active:
            projectile.update()

            # Check if the projectile is out of bounds or collides with enemies
            if projectile_out_of_bounds(projectile):
                projectile.is_active = False
            else:
                for enemy in enemies[:]:
                    if float_based_collision(projectile, enemy):
                        # Check for power-up spawn
                        powerup_types = spawn_powerups(enemy.x, enemy.y)
                        powerup = create_combined_powerup(enemy.x, enemy.y, powerup_types)
                        if powerup:
                            powerups.append(powerup)
                            
                        enemies.remove(enemy)
                        projectile.is_active = False
                        enemies_killed += 1
                        break
                    
    # Check for collisions between player and power-ups
    for powerup in powerups[:]:
        if float_based_collision(powerup, local_player):
            for p_type in powerup.types:
                local_player.activate_powerup(p_type)
            powerups.remove(powerup)

    # Check for collisions between enemies and players
    for enemy in enemies[:]:
        if float_based_collision(enemy, local_player):
            local_player.take_damage()
            enemies.remove(enemy)

def spawn_powerups(enemy_x, enemy_y):
    spawned_powerups = []
    for powerup_type, info in powerup_info.items():
        if random.randint(1, 100) <= info["chance"]:
            spawned_powerups.append(powerup_type)

    return spawned_powerups

def create_combined_powerup(x, y, powerup_types):
    if not powerup_types:
        return None

    # Mix colors
    total_color = [0, 0, 0]
    for p_type in powerup_types:
        color = powerup_info[p_type]["color"]
        total_color = [sum(x) for x in zip(total_color, color)]

    # Normalize the color
    max_color = max(total_color)
    if max_color > 255:
        total_color = [int(c * 255 / max_color) for c in total_color]

    return PowerUp(x, y, powerup_types, tuple(total_color))

def projectile_out_of_bounds(projectile):
    return (projectile.x < 0 or projectile.x > screen_width or
            projectile.y < 0 or projectile.y > screen_height)

def manage_waves(enemies, player):
    global in_intermission, intermission_timer, current_wave, enemies_per_wave, wave_increase_factor, upgrade_tile_groups, upgrade_selected

    current_time = pygame.time.get_ticks()

    if len(enemies) == 0 and not in_intermission:
        in_intermission = True
        intermission_timer = current_time + 5000  # 5 seconds
        upgrade_tile_groups.append(initialize_upgrade_tiles(current_wave))
        upgrade_selected = False  # Reset the flag at the start of intermission

    if in_intermission and current_time >= intermission_timer and upgrade_selected:
        in_intermission = False
        upgrade_selected = False  # Reset the flag after the intermission ends
        current_wave += 1
        enemies_per_wave += wave_increase_factor
        enemies.clear()
        enemies.extend([spawn_enemy(player.x, player.y) for _ in range(enemies_per_wave)])
        upgrade_tile_groups.clear()  # Clear the upgrades after selection

def main_menu(screen):
    global is_multiplayer

    # Create the main menu instance
    main_menu = Menu(screen)

    # Add buttons to the main menu
    main_menu.add_button(Button("Play", 100, 200, 200, 50, action=gameLoop))
    main_menu.add_button(Button("Instructions", 100, 300, 150, 50, action=instructions, action_args=[screen]))
    main_menu.add_button(Button("Quit", 100, 400, 100, 50, action=quit_game))

    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                main_menu.handle_event(event)

        # Drawing the menu
        screen.fill(BLACK)  # Clear screen with black background
        main_menu.draw()
        pygame.display.update()

def instructions(screen):
    instructions_menu = Menu(screen)
    instructions_menu.add_button(Button("Back", 100, 500, 100, 50, action=back_to_main_menu))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            else:
                instructions_menu.handle_event(event)

        screen.fill((0, 0, 0))  # Fill screen with background color
        draw_text(screen, "Game Instructions:", 36, 50, 50, WHITE)
        draw_text(screen, "Use arrow keys to move", 30, 50, 100, WHITE)
        draw_text(screen, "Click to shoot", 30, 50, 150, WHITE)
        # Add more instructions as needed
        instructions_menu.draw()
        pygame.display.update()

def pause_menu(screen):
    pause_menu = Menu(screen)
    pause_menu.add_button(Button("Resume", screen_width // 2 - 100, 200, 200, 50, action=lambda: "resume"))
    pause_menu.add_button(Button("Quit", screen_width // 2 - 100, 300, 200, 50, action=lambda: "quit"))

    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(128)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    pause = True
    while pause:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            else:
                action = pause_menu.handle_event(event)
                if action:
                    return action

        screen.fill((0, 0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        pause_menu.draw()
        pygame.display.flip()
        
def game_over(screen, current_wave, enemies_killed):
    game_over_menu = Menu(screen)
    game_over_menu.add_button(Button("Main Menu", screen_width // 2 - 125, 300, 250, 50, action=back_to_main_menu))  # Add the button to the menu

    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(128)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            else:
                # Delegate event handling to the menu
                game_over_menu.handle_event(event)

        screen.fill((0, 0, 0), special_flags=pygame.BLEND_RGBA_MULT)  # Apply the overlay
        game_over_menu.draw()
        draw_text(screen, "Game Over", 55, screen_width // 2 - 100, 100, WHITE, center_x=True)
        draw_text(screen, f"Wave: {current_wave}", 55, screen_width // 2 - 100, 150, WHITE, center_x=True)
        draw_text(screen, f"Enemies Killed: {enemies_killed}", 55, screen_width // 2 - 100, 200, WHITE, center_x=True)
        
        pygame.display.flip()

def handle_enemy_collisions(enemies):
    for i, enemy1 in enumerate(enemies):
        for j, enemy2 in enumerate(enemies):
            if i != j and enemy1.rect.colliderect(enemy2.rect):
                # Simple collision response
                if enemy1.rect.x < enemy2.rect.x:
                    enemy1.x -= enemy1.speed
                else:
                    enemy1.x += enemy1.speed

                if enemy1.rect.y < enemy2.rect.y:
                    enemy1.y -= enemy1.speed
                else:
                    enemy1.y += enemy1.speed

                # Update the rect position
                enemy1.rect.x, enemy1.rect.y = round(enemy1.x), round(enemy1.y)

def float_based_collision(obj1, obj2):
    # Extract position and size for the first object
    x1, y1 = obj1.x, obj1.y
    width1, height1 = obj1.image.get_size()

    # Extract position and size for the second object
    x2, y2 = obj2.x, obj2.y
    width2, height2 = obj2.image.get_size()

    # Check for collision
    if (x1 + width1 > x2 and x1 < x2 + width2 and
            y1 + height1 > y2 and y1 < y2 + height2):
        return True  # Collision detected

    return False

def spawn_enemy(player_x, player_y):
    # Choose a random side to spawn from: 0 = top, 1 = right, 2 = bottom, 3 = left
    side = random.randint(0, 3)
    
    if side == 0:  # Top
        x = random.randint(0, screen_width)
        y = -40  # Slightly above the top edge
    elif side == 1:  # Right
        x = screen_width + 40  # Slightly to the right of the right edge
        y = random.randint(0, screen_height)
    elif side == 2:  # Bottom
        x = random.randint(0, screen_width)
        y = screen_height + 40  # Slightly below the bottom edge
    else:  # Left
        x = -40  # Slightly to the left of the left edge
        y = random.randint(0, screen_height)

    return Enemy(x, y)

def update_projectiles(projectiles, received_projectiles):
    for p_data in received_projectiles:
        projectile = next((p for p in projectiles if p.id == p_data['id']), None)
        
        if projectile:
            projectile.x = p_data['x']
            projectile.y = p_data['y']
            projectile.is_active = p_data.get('is_active', True)  # Default to True if not present
        else:
            new_projectile = Projectile(p_data['x'], p_data['y'], 0, 0)
            new_projectile.id = p_data['id']
            new_projectile.is_active = p_data.get('is_active', True)
            projectiles.append(new_projectile)

def gameLoop():
    global local_player, enemies_killed, current_wave, in_intermission, intermission_timer, projectiles, enemies_per_wave, projectiles, upgrade_tile_groups, upgrade_selected

    # Initialization
    running = True
    enemies_killed = 0
    current_wave = 1
    last_shot_time = 0
    shot_delay = 500 # milliseconds
    in_intermission = False
    intermission_timer = 0
    mouse_button_down = False
    upgrade_selected = False
    clock = pygame.time.Clock()
    fps = 60
    
    # Player initialization
    local_player = Player()
    enemies = [spawn_enemy(local_player.x, local_player.y) for _ in range(enemies_per_wave)]
    group_to_remove = None

    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                action = pause_menu(screen)
                if action == "quit":
                    running = False
                elif action == "resume":
                    continue
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_button_down = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_button_down = False

            # Separate handling for mouse button down
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Handle firing a bullet
                current_time = pygame.time.get_ticks()
                if current_time - local_player.last_shot_time > local_player.shot_delay:
                    new_projectile = local_player.shoot(mouse_x, mouse_y)
                    projectiles.append(new_projectile)
                    local_player.last_shot_time = current_time

                # Check for button clicks on upgrade tiles during intermission
                if in_intermission:
                    for tile_group in upgrade_tile_groups:
                        for tile in tile_group:
                            if tile.button.is_clicked((mouse_x, mouse_y)):
                                tile.select_upgrade()
                                upgrade_selected = True  # Set the flag to True after selecting an upgrade
                                upgrade_tile_groups.clear()  # Clear all upgrade tiles
                                break
                        if upgrade_selected:
                            break
        
        # Player input handling
        handle_player_input(local_player)

        # Handle collisions between enemies
        handle_enemy_collisions(enemies)

        # Update game state
        update_game_state(local_player, enemies, projectiles)

        # Manage game waves
        manage_waves(enemies, local_player)
        
        # Drawing
        draw_game(screen, local_player, enemies, projectiles)

        # Check for game over
        if local_player.hp <= 0:
            action = game_over(screen, current_wave, enemies_killed)
            if action == "restart":
                reset_game()
                return "restart"
            elif action == "menu":
                return "menu"

        clock.tick(fps)

def back_to_main_menu():
    main_menu(screen)

def quit_game():
    pygame.quit()
    sys.exit()

def reset_game():
    global player, enemies, projectiles, enemies_killed, current_wave
    player = Player()
    player.x, player.y = initial_player_x, initial_player_y
    enemies = [spawn_enemy(initial_player_x, initial_player_y) for _ in range(number_of_enemies)]
    projectiles = []
    enemies_killed = 0
    current_wave = 1

def main():
    global enemies, player
    #Initialize pygame
    pygame.init()
    #Set up game loop
    pygame.display.set_caption("Roguelike Shooter")
    enemies = [spawn_enemy(initial_player_x, initial_player_y) for _ in range(number_of_enemies)]
    main_menu(screen)
    pygame.quit()

if __name__ == "__main__":
    main()
