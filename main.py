import pygame
import sys
import random
import importlib
import time
from cfg import *
import cfg

class Player:
    def __init__(self):
        self.image = pygame.Surface((50,50))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect()
        self.base_speed = 3
        self.speed = 3  # Normal speed
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
        self.inventory = []  # Initialize the inventory
        self.powerup_use_cooldown = 500  # 500 milliseconds cooldown
        self.last_powerup_use_time = 0
        self.is_knocked_back = False
        self.knockback_velocity_x = 0
        self.knockback_velocity_y = 0
        self.knockback_end_time = 0
        self.last_wall_hit_time = 0

    def keep_in_bounds(self):
        sound_effect = pygame.mixer.Sound("audio/hitWall.wav")
        sound_effect.set_volume(0.18)
        current_time = time.time()  # Get the current time in seconds
        if self.rect.left < 0:
            self.rect.left = 0
            if current_time - self.last_wall_hit_time > 1:  # Check if 1 second has passed
                sound_effect.play()
                self.last_wall_hit_time = current_time  # Update the last wall hit time
        if self.rect.right > cfg.screen_width:
            self.rect.right = cfg.screen_width
            if current_time - self.last_wall_hit_time > 1:  # Check if 1 second has passed
                sound_effect.play()
                self.last_wall_hit_time = current_time  # Update the last wall hit time
        if self.rect.top < 0:
            self.rect.top = 0
            if current_time - self.last_wall_hit_time > 1:  # Check if 1 second has passed
                sound_effect.play()
                self.last_wall_hit_time = current_time  # Update the last wall hit time
        if self.rect.bottom > cfg.screen_height:
            self.rect.bottom = cfg.screen_height
            if current_time - self.last_wall_hit_time > 1:  # Check if 1 second has passed
                sound_effect.play()
                self.last_wall_hit_time = current_time  # Update the last wall hit time


    def handle_keys(self, keys):
        keys = pygame.key.get_pressed()
        sprint_requested = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if sprint_requested and self.stamina > 0:
            self.is_sprinting = True
        else:
            self.is_sprinting = False
        
        current_speed = self.sprint_speed if self.is_sprinting else self.speed
        new_x, new_y = self.x, self.y

        # Proposed change: Move X and Y independently
        if keys[pygame.K_a]:
            new_x -= current_speed
            if self.can_move(new_x, self.y):
                self.x = new_x
        if keys[pygame.K_d]:
            new_x += current_speed
            if self.can_move(new_x, self.y):
                self.x = new_x

        new_x = self.x  # Reset new_x to updated x position
        if keys[pygame.K_w]:
            new_y -= current_speed
            if self.can_move(new_x, new_y):
                self.y = new_y
        if keys[pygame.K_s]:
            new_y += current_speed
            if self.can_move(new_x, new_y):
                self.y = new_y

        self.keep_in_bounds()

        # Handle inventory key presses
        if keys[pygame.K_1]:
            self.use_powerup(0)  # Use the powerup in the first slot
        if keys[pygame.K_2]:
            self.use_powerup(1)  # Use the powerup in the second slot
        if keys[pygame.K_3]:
            self.use_powerup(2)  # Use the powerup in the third slot

    def can_move(self, new_x, new_y):
        # Create a temporary rectangle for the new position
        temp_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)

        # Check for collision with UI area and screen boundaries
        ui_rect = pygame.Rect(0, 0, cfg.UI_WIDTH, cfg.SCREEN_HEIGHT)
        screen_rect = pygame.Rect(0, 0, cfg.screen_width, cfg.screen_height)

        return not temp_rect.colliderect(ui_rect) and screen_rect.contains(temp_rect)

    def add_to_inventory(self, powerup_info):
        if len(self.inventory) < 3:  # Maximum of 3 items in inventory
            self.inventory.append(powerup_info)
            sound_effect = pygame.mixer.Sound("audio/pickupPowerup.wav")
            sound_effect.set_volume(0.18)
            sound_effect.play()

    def use_powerup(self, slot_index):
        current_time = pygame.time.get_ticks()
        if 0 <= slot_index < len(self.inventory) and current_time - self.last_powerup_use_time > self.powerup_use_cooldown:
            self.activate_powerup(self.inventory.pop(slot_index))  # Remove the used powerup
            sound_effect = pygame.mixer.Sound("audio/usePowerup.wav")
            sound_effect.set_volume(0.18)
            sound_effect.play()
            self.last_powerup_use_time = current_time

    def activate_powerup(self, powerup_info):
        for powerup_type in powerup_info["types"]:
            if powerup_type == "invincibility":
                self.invincible = True
            elif powerup_type == "infinite_stamina":
                self.infinite_stamina = True
            elif powerup_type == "shoot_speed_boost":
                self.shot_delay = self.base_shot_delay * 0.5  # Example: 50% of original delay
            elif powerup_type == "move_speed_boost":
                self.sprint_speed = self.base_sprint_speed * 1.5
                self.speed = self.base_speed * 1.5
            elif powerup_type == "health_orb":
                self.hp = min(self.hp + 0.3 * self.max_hp, self.max_hp)  # Increase HP but not above max

            # Set timer for each power-up duration (e.g., 10 seconds)
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
            self.base_speed += self.base_speed * 0.1  # Increase speed by 10%
            self.base_sprint_speed += self.base_sprint_speed * 0.1  # Increase sprint speed as well
            self.speed = self.base_speed
            self.sprint_speed = self.base_sprint_speed

        elif upgrade_name == "Enhanced Fire Rate":
            self.base_shot_delay *= 0.9  # Decrease delay by 10%
            self.shot_delay = self.base_shot_delay

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
        current_time = pygame.time.get_ticks()
        if self.is_knocked_back:
            if current_time < self.knockback_end_time:
                # Move X and Y with bounds checking
                new_x = self.x + self.knockback_velocity_x
                new_y = self.y + self.knockback_velocity_y

                # Bounds checking for left and right boundaries
                if new_x < cfg.UI_WIDTH or new_x > cfg.screen_width - self.rect.width:
                    self.knockback_velocity_x *= -1  # Reverse horizontal direction

                # Bounds checking for top and bottom boundaries
                if new_y < 0 or new_y > cfg.screen_height - self.rect.height:
                    self.knockback_velocity_y *= -1  # Reverse vertical direction

                # Update position with new values
                self.x = new_x
                self.y = new_y

                self.rect.x, self.rect.y = round(self.x), round(self.y)
            else:
                # Reset knockback state
                self.is_knocked_back = False
        else:
        
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
                    
    def knockback(self, velocity_x, velocity_y, duration):
        self.is_knocked_back = True
        self.knockback_velocity_x = velocity_x
        self.knockback_velocity_y = velocity_y
        self.knockback_end_time = pygame.time.get_ticks() + duration


    def take_damage(self):
        current_time = pygame.time.get_ticks()
        if(self.invincible == False):
            self.hp = self.hp - 1 + self.damage_reduction  # Reduce HP by 1 - total damage reduction
            sound_effect = pygame.mixer.Sound("audio/playerDamage.wav")
            sound_effect.set_volume(0.18)
            sound_effect.play()


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
        self.fire_squares = []  # List to hold the fire squares

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

    def update_fire_effect(self):
        # Add new fire squares to simulate flames
        if random.random() < 0.5:  # Adjust probability to control density
            self.add_fire_square()

        # Update existing fire squares
        for square in self.fire_squares[:]:  # Iterate over a copy of the list
            square['y'] += random.uniform(-1, 1)  # Slight vertical jitter can add to the effect
            square['lifetime'] += 1
            if square['lifetime'] > 30:  # Shorter lifetime
                self.fire_squares.remove(square)

    def add_fire_square(self):
        colors = [(255, 150, 0), (255, 69, 0), (255, 215, 0)]  # Different shades for fire
        for _ in range(5):  # Add multiple squares at once for a denser effect
            color = random.choice(colors)
            offset_x = random.uniform(-20, 20)
            offset_y = random.uniform(-20, 20)
            square = {
                'x': self.x + offset_x + 20,
                'y': self.y + offset_y + 20,
                'color': color,
                'lifetime': 0
            }
            self.fire_squares.append(square)

    def draw(self, surface):
        if self.x > cfg.UI_WIDTH:  # Only draw if outside the UI area
            surface.blit(self.image, self.rect)
            if self.x > cfg.UI_WIDTH:  # Check based on your game's UI configuration
                surface.blit(self.image, self.rect)
            
            # Draw fire squares
            for square in self.fire_squares:
                s = pygame.Surface((5, 5), pygame.SRCALPHA)
                alpha = max(0, 255 - square['lifetime'] * 10)  # Increase fade-out speed
                s.fill((*square['color'], alpha))  # Set color with alpha
                surface.blit(s, (square['x'], square['y']))  # Draw square

class Boss:
    def __init__(self, x, y, boss_type, health):
        self.x, self.y = x, y
        self.boss_type = boss_type
        self.hp = health
        self.max_hp = health
        self.image = pygame.Surface((80, 80))
        self.image.fill((200, 0, 0))
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.speed = 2
        self.squares = []

        if self.boss_type == 'dasher':
            self.dash_speed = 20  # Speed of the dash
            self.dash_count = 0
            self.max_dashes = 3
            self.dash_duration = 400  # Duration of each dash
            self.dash_cooldown = 250  # Delay between individual dashes
            self.burst_cooldown = 1000  # Delay between dash bursts
            self.last_dash_time = 0
            self.next_dash_time = 0
            self.dashing = False
            self.dash_target = None

    def update(self, player):
        current_time = pygame.time.get_ticks()
        if self.boss_type == 'dasher':
            if not self.dashing and current_time >= self.next_dash_time:
                self.start_dash(player)

            if self.dashing:
                if current_time - self.last_dash_time > self.dash_duration:
                    self.end_dash()
                    if self.dash_count < self.max_dashes:
                        self.next_dash_time = current_time + self.dash_cooldown
                    else:
                        self.next_dash_time = current_time + self.burst_cooldown
                        self.dash_count = 0  # Reset dash count after burst cooldown

                else:
                    self.continue_dash()
        
        # Update squares
        for square in self.squares[:]:  # Iterate over a copy of the list
            square['angle'] += 5  # Update angle for spinning
            square['lifetime'] += 5  # Update lifetime for fading

            # Remove square if its lifetime exceeds a threshold (e.g., 100 frames)
            if square['lifetime'] > 1000:
                self.squares.remove(square)


    def draw_hp_bar(self, surface, max_health):
        bar_width = 160
        bar_height = 13
        bar_color = (255, 0, 0)  # red color for the health bar
        background_color = (50, 50, 50)  # dark gray for the background

        bar_x = self.x - 38
        bar_y = self.y - 30  # position the bar above the boss

        draw_bar(surface, self.hp, self.max_hp, bar_x, bar_y, bar_width, bar_height, bar_color, background_color)

    def dash_effect(self, surface):
        # Spawn squares with wider offsets
        for _ in range(10):  # Spawn 5 squares or adjust as needed
            square = {
                'x': self.x + random.uniform(-40, 40),  # Increase the range for a wider spread
                'y': self.y + random.uniform(-40, 40),  # Increase the range for a wider spread
                'angle': 0,
                'lifetime': 0
            }
            self.squares.append(square)

    def start_dash(self, player):
        self.dashing = True
        self.dash_target = (player.x, player.y)
        self.last_dash_time = pygame.time.get_ticks()
        self.dash_count += 1
        self.dash_effect(screen)

    def continue_dash(self):
        if self.dash_target:
            target_dx, target_dy = self.dash_target[0] - self.x, self.dash_target[1] - self.y
            distance = max((target_dx**2 + target_dy**2)**0.5, 1)
            self.x += (target_dx / distance) * self.dash_speed
            self.y += (target_dy / distance) * self.dash_speed
            self.rect.x, self.rect.y = round(self.x), round(self.y)
            self.dash_effect(screen)

    def end_dash(self):
        self.dashing = False

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        # Draw squares
        for square in self.squares:
            # Create a surface for the square with an alpha channel for transparency
            s = pygame.Surface((5, 5), pygame.SRCALPHA)
            # Calculate fading based on lifetime (e.g., start fading after 50 frames)
            alpha = max(0, min(255, 255 - (square['lifetime'])))  # Ensure alpha is within 0-255
            s.fill((255, 0, 0, alpha))  # Apply fading effect
            # Rotate the square surface
            s = pygame.transform.rotate(s, square['angle'])
            # Correct the position after rotation
            new_rect = s.get_rect(center=(square['x'], square['y']))
            # Draw the rotated and faded square
            surface.blit(s, new_rect.topleft)

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
        sound_effect = pygame.mixer.Sound("audio/shootBullet.wav")
        sound_effect.set_volume(0.13)
        sound_effect.play()

    def update(self):
        self.x += self.x_velocity
        self.y += self.y_velocity
        self.rect.x, self.rect.y = round(self.x), round(self.y)

        # Deactivate if it collides with the UI area
        if self.rect.colliderect(pygame.Rect(0, 0, cfg.UI_WIDTH, cfg.SCREEN_HEIGHT)):
            self.is_active = False

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
        self.x_velocity = random.uniform(-2.4, 2.4)
        self.y_velocity = random.uniform(-2.4, 2.4)
        self.fading = False
        self.alpha = 255  # Fully opaque initially

    def update(self):
        # Update position
        self.x += self.x_velocity
        self.y += self.y_velocity

        # Create a rectangle for collision detection
        temp_rect = pygame.Rect(self.x, self.y, self.radius * 2, self.radius * 2)

        # Check for collision with screen boundaries and UI
        if temp_rect.left <= cfg.UI_WIDTH or temp_rect.right >= cfg.screen_width:
            self.x_velocity *= -1  # Reverse horizontal direction
        if temp_rect.top <= 0 or temp_rect.bottom >= cfg.screen_height:
            self.y_velocity *= -1  # Reverse vertical direction

        # Update the position of the rect
        self.rect.x, self.rect.y = round(self.x), round(self.y)

        if self.fading:
            self.alpha -= 5  # Reduce alpha to create a fading effect
            self.alpha = max(self.alpha, 0)  # Ensure alpha doesn't go below 0
    
    def draw(self, surface):
        if self.alpha < 255:
            self.image.set_alpha(self.alpha)  # Set current alpha
        surface.blit(self.image, self.rect)

class Button:
    def __init__(self, text, x, y, width, height, action=None, action_args=[], bg_color=(255, 255, 255)):
        # Existing attributes
        self.text = text
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y
        self.width = width
        self.height = height
        self.base_width = width
        self.base_height = height
        self.action = action
        self.action_args = action_args
        self.bg_color = bg_color

        # Attributes for hover effect
        self.hovered = False
        self.scale_factor = 1.0
        self.target_scale = 1.05  # Target scale factor when hovered
        self.current_color = self.bg_color
        self.hover_color = (min(255, self.bg_color[0] + 30),  # Brighten the color for hover effect
                            min(255, self.bg_color[1] + 30),
                            min(255, self.bg_color[2] + 30))
        self.anim_speed = 0.00005 * self.width

        # Attributes for effects
        self.hover_alpha = 0  # Alpha for hover overlay
        self.hover_increment = 15  # Speed of fade-in for hover effect
        self.clicked = False  # Track if the button is currently being clicked

    def update(self, mouse_pos, mouse_pressed):
        # Hover detection
        mouse_x, mouse_y = mouse_pos

        # Check if the mouse is over the button
        self.hovered = self.x <= mouse_x <= self.x + self.width and self.y <= mouse_y <= self.y + self.height
        
        # Hover alpha animation
        if self.hovered:
            self.hover_alpha = min(self.hover_alpha + self.hover_increment, 50)  # Cap at desired max alpha
        else:
            self.hover_alpha = max(self.hover_alpha - self.hover_increment, 0)
        
        # Click effect handling
        if self.hovered and mouse_pressed[0]:  # Left mouse button is pressed
            self.clicked = True
        else:
            self.clicked = False
                
        # Hover effect to expand the button in all directions
        if self.hovered:
            self.width = self.base_width * self.target_scale
            self.height = self.base_height * self.target_scale
            self.x = self.base_x - (self.width - self.base_width) // 2
            self.y = self.base_y - (self.height - self.base_height) // 2
        else:
            self.width = self.base_width
            self.height = self.base_height
            self.x = self.base_x
            self.y = self.base_y
        
        # Ensure color values remain within valid range
        self.current_color = tuple(min(255, max(0, int(c))) for c in self.current_color)

    def draw(self, screen):
        # Draw the button background with border
        pygame.draw.rect(screen, self.current_color, (self.x, self.y, self.width, self.height))

        # Apply scale and adjust position to keep centered
        scaled_width = int(self.width * self.scale_factor)
        scaled_height = int(self.height * self.scale_factor)
        scaled_x = self.x - (scaled_width - self.width) // 2
        scaled_y = self.y - (scaled_height - self.height) // 2

        # Draw the button with the current color and scaled size
        pygame.draw.rect(screen, self.current_color, (scaled_x, scaled_y, scaled_width, scaled_height))
        # Set the colors
        button_color = (50, 50, 50)  # Dark gray background
        text_color = (255, 255, 255)  # White text
        border_color = (255, 255, 255)  # White border

        # Draw the button background with border
        pygame.draw.rect(screen, border_color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, button_color, (self.x + 2, self.y + 2, self.width - 4, self.height - 4))

        # Draw the text on the button
        font = pygame.font.SysFont("Arial", 20)
        text_surf = font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=(self.x + self.width / 2, self.y + self.height / 2))
        screen.blit(text_surf, text_rect)

        # Draw hover overlay
        if self.hover_alpha > 0:
            hover_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            hover_overlay.fill((255, 255, 255, self.hover_alpha))
            self.width = min(scaled_width, self.base_width * 1.05)
            self.height = min(scaled_height, self.base_height * 1.05)
            screen.blit(hover_overlay, (self.x, self.y))
        else:
            self.width = self.base_width
            self.height = self.base_height

    def is_clicked(self, mouse_pos):
        x, y = mouse_pos
        return (self.x <= x <= self.x + self.width) and (self.y <= y <= self.y + self.height)

    def activate(self):
        if self.action:
            sound_effect = pygame.mixer.Sound("audio/clickButton.wav")
            sound_effect.set_volume(0.25)
            sound_effect.play()
            return self.action(*self.action_args)  # Pass action_args to the function

class UpgradeTile:
    def __init__(self, upgrade_name, description, x, y, width, height):
        self.upgrade_name = upgrade_name
        self.description = description
        self.x = x
        self.y = y
        self.width = width + 15
        self.height = height
        self.button = Button("Choose", x + 17.5, y + height - 40, width - 20, 30, action=self.select_upgrade)
        button_list.append(self.button)

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
        global local_player, powerups
        local_player.apply_upgrade(self.upgrade_name)
        sound_effect = pygame.mixer.Sound("audio/clickButton.wav")
        sound_effect.set_volume(0.25)
        sound_effect.play()

        # Trigger fading for all powerups
        for powerup in powerups:
            powerup.fading = True

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.buttons = []

    def add_button(self, button):
        global button_list
        self.buttons.append(button)
        button_list.append(button)

    def draw(self):
        for button in self.buttons:
            button.draw(self.screen)

    def handle_event(self, event):
        global button_list, screen
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            for button in self.buttons:
                if button.is_clicked(mouse_pos) == True:
                    button.update(mouse_pos, pygame.mouse.get_pos())
                    button_list.clear()
                    button.draw(screen)
                    return button.activate()

    def reset_button_states(self):
        for button in self.buttons:
            button.hovered = False
            button.hover_alpha = 0

def draw_bar(surface, value, max_value, x, y, width, height, bar_color, background_color):
    # Draw the background of the bar (empty part)
    pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height))  # White border
    pygame.draw.rect(surface, background_color, (x + 2, y + 2, width - 4, height - 4))

    # Calculate the width of the bar (current value)
    current_width = (value / max_value) * width

    # Draw the current value
    pygame.draw.rect(surface, bar_color, (x + 2, y + 2, current_width - 4, height - 4))

def draw_player_stats(screen, player, start_x, start_y):

    stats_box_x = 6  # Adjust as needed
    stats_box_y = 95  # Adjust as needed
    stats_box_width = 225  # Adjust as needed
    stats_box_height = 152  # Adjust as needed
    box_color = (50, 50, 50)  # Dark gray
    border_color = (255, 255, 255)  # White

    # Draw the stats box background with border
    pygame.draw.rect(screen, border_color, (stats_box_x, stats_box_y, stats_box_width, stats_box_height))
    pygame.draw.rect(screen, box_color, (stats_box_x + 2, stats_box_y + 2, stats_box_width - 4, stats_box_height - 4))

    # Define the starting position
    start_x = 9  # adjust as needed for your screen layout
    start_y = 95
    line_height = 20  # space between lines
    font = pygame.font.SysFont("Arial", 16)

    # Calculate shots per second (Hz) and round to 2 decimal places for readability
    if player.shot_delay > 0:  # Prevent division by zero
        shots_per_second = round(1 / (player.shot_delay / 1000), 2)
    else:
        shots_per_second = 'Max'

    # Define stats to display
    stats = [
        f"Health: {player.hp:.2f}/{player.max_hp:.2f}",
        f"Health Regeneration: {player.hp_regeneration_rate:.2f}/s",  # Rounded to two decimal places
        f"Stamina: {player.stamina:.2f}/{player.max_stamina:.2f}",
        f"Stamina Regeneration: {player.stamina_recovery_rate:.2f}/s",  # Rounded to two decimal places
        f"Movement Speed: {player.speed:.2f} pixels/s",  # Rounded to two decimal places
        f"Fire Rate: {shots_per_second:.2f} shots/s",
        f"Damage Reduction: {player.damage_reduction:.2f}/hit",  # Rounded to two decimal places
    ]

    # Set the font for the stats
    font = pygame.font.SysFont("Arial", 16)
    
    # Draw each stat
    for i, stat in enumerate(stats):
        text_surface = font.render(stat, True, (255, 255, 255))  # White color text
        screen.blit(text_surface, (start_x, start_y + i * line_height))

def handle_player_input(player, upgrade_time):
    current_time = pygame.time.get_ticks()
    keys = pygame.key.get_pressed()
    player.handle_keys(keys)

    # Mouse button handling for shooting
    mouse_button_down = pygame.mouse.get_pressed()[0]
    if mouse_button_down and current_time - player.last_shot_time > player.shot_delay and current_time - upgrade_time > 5:
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
        tile_x = 6  # Adjust as needed
        tile_y = 255 + i * 110  # Adjust the vertical position based on the tile number
        tile_width = 301
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

def draw_wave_and_kill_count(screen, current_wave, enemies_killed):
    # Set the position and dimensions of the box
    box_x = 6
    box_y = 845  # Adjust as needed
    box_width = 200
    box_height = 50

    # Set the colors
    box_color = (50, 50, 50)  # Dark gray
    border_color = (255, 255, 255)  # White
    text_color = (255, 255, 255)  # White

    # Draw the box with a border
    pygame.draw.rect(screen, border_color, (box_x, box_y, 301, box_height))
    pygame.draw.rect(screen, box_color, (box_x + 2, box_y + 2, 301 - 4, box_height - 4))

    # Prepare the text
    font = pygame.font.SysFont("Arial", 20)
    wave_text = f"Wave: {current_wave}"
    kill_count_text = f"Enemies Killed: {enemies_killed}"

    # Render and position the wave text
    wave_surf = font.render(wave_text, True, text_color)
    wave_rect = wave_surf.get_rect()
    wave_rect.topleft = (box_x + 3, box_y + 5)  # Fixed left position
    screen.blit(wave_surf, wave_rect)

    # Render and position the kill count text
    kill_count_surf = font.render(kill_count_text, True, text_color)
    kill_count_rect = kill_count_surf.get_rect()
    kill_count_rect.topleft = (box_x + 3, box_y + 25)  # Fixed left position, below wave text
    screen.blit(kill_count_surf, kill_count_rect)

def draw_game(screen, player, enemies, projectiles, bosses):
    screen.fill((0, 0, 0))  # Clear screen with black background

    draw_background = False

    # Draw the UI area background
    if draw_background == False:
        ui_background = pygame.Rect(0, 0, cfg.UI_WIDTH, cfg.SCREEN_HEIGHT)
        pygame.draw.rect(screen, (128, 128, 128), ui_background)  # Grey background for UI

    # Draw UI elements within the UI area
    ui_offset_x = 20  # Horizontal offset for UI elements from the edge of the UI area
    ui_offset_y = 20  # Vertical offset for UI elements from the top of the UI area

    # Draw player and remote player (in multiplayer mode)
    player.draw(screen)

    # Draw enemies and projectiles
    for enemy in enemies:
        enemy.draw(screen)
        enemy.update_fire_effect()  # Update fire effect

    # Draw power-ups
    for powerup in powerups:
        powerup.draw(screen)

    for boss in bosses:
        boss.draw(screen)
        boss.draw_hp_bar(screen, boss.max_hp)

    # Draw projectiles
    for projectile in projectiles:
        if projectile.is_active:
            projectile.draw(screen)

    # Draw UI elements (HP bar, Stamina bar, etc.)
    # Health bar
    draw_bar(screen, player.hp, player.max_hp, 6, ui_offset_y, cfg.BAR_WIDTH, cfg.BAR_HEIGHT, cfg.RED, cfg.GRAY)
    # Stamina bar
    draw_bar(screen, player.stamina, player.max_stamina, 6, ui_offset_y + 40, cfg.BAR_WIDTH, cfg.BAR_HEIGHT, cfg.GREEN, cfg.GRAY)
    draw_wave_and_kill_count(screen, current_wave, enemies_killed)

    if in_intermission:
            draw_text(screen, f"Select an Upgrade to Begin Next Round", 36, 800, BAR_Y + BAR_HEIGHT + 10, WHITE)
            for tile_group in upgrade_tile_groups:
                for tile in tile_group:
                    tile.draw(screen)
                
    # Updates player stats
    draw_player_stats(screen, player, ui_offset_x, ui_offset_y + 80)  # Offset needs to be below the last bar

    # Draw the UI for inventory
    draw_inventory(screen, player)

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

def draw_inventory(screen, player):
    inventory_x = 239  # Adjust as needed
    inventory_y = 19  # Adjust as needed
    slot_width = 69
    slot_height = 69
    slot_margin = 10
    slot_color = (50, 50, 50)  # Dark gray
    border_color = (255, 255, 255)  # White

    for i in range(3):  # Draw three slots regardless of whether they are occupied
        # Draw the slot background with border
        pygame.draw.rect(screen, border_color, (inventory_x, inventory_y + i * (slot_height + slot_margin), slot_width, slot_height))
        pygame.draw.rect(screen, slot_color, (inventory_x + 2, inventory_y + 2 + i * (slot_height + slot_margin), slot_width - 4, slot_height - 4))

        # If the slot has a powerup, draw it
        if i < len(player.inventory):
            powerup_info = player.inventory[i]
            powerup_color = powerup_info["color"]  # Access the color from the dictionary
            pygame.draw.circle(screen, powerup_color, (inventory_x + slot_width // 2, inventory_y + slot_height // 2 + i * (slot_height + slot_margin)), 26.4)

def hover_effect():
    global button_list
    # Update and draw buttons with hover effect
    mouse_pos = pygame.mouse.get_pos()  # Get the current mouse position
    mouse_pressed = pygame.mouse.get_pressed()  # Get the state of the mouse buttons
    for button in button_list:  # Assuming you have a list of buttons
        button.update(mouse_pos, mouse_pressed)  # Update each button's state based on the mouse position
        if(button.hovered):
            button.draw(screen)  # Draw the button with its current appearance

def update_game_state(local_player, enemies, projectiles, powerups):
    global enemies_killed, bosses

    sound_effect = pygame.mixer.Sound("audio/hitEnemy.wav")
    sound_effect.set_volume(0.18)
    
    # Update local player
    local_player.update()

    # Update enemies
    for enemy in enemies:
        # The enemy should move towards the nearest player
        enemy.move_towards_player(local_player)

    for boss in bosses:
        boss.update(local_player)

        # Check for collisions with the player
        if float_based_collision(local_player, boss) and not local_player.is_knocked_back:
            # Calculate knockback direction based on relative position
            dx = local_player.x - boss.x
            dy = local_player.y - boss.y
            distance = max((dx**2 + dy**2)**0.5, 1)
            knockback_velocity_x = 15 * (dx / distance)  # Adjust magnitude as needed
            knockback_velocity_y = 15 * (dy / distance)  # Adjust magnitude as needed
            knockback_duration = 1500  # 1.5 seconds

            local_player.knockback(knockback_velocity_x, knockback_velocity_y, knockback_duration)
            local_player.take_damage()
        
        # Check for collisions with projectiles
        for projectile in projectiles:
            if projectile.is_active and float_based_collision(projectile, boss):
                # Handle collision with projectile
                boss.hp -= 1  # Example
                projectile.is_active = False
                sound_effect.play()

                if boss.hp <= 0:
                    bosses.remove(boss)
                    # Handle boss defeat, e.g., dropping items
                    break

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
                        sound_effect.play()
                        projectile.is_active = False
                        enemies_killed += 1
                        break
                    
    # Check for collisions between player and power-ups
    for powerup in powerups[:]:
        if float_based_collision(powerup, local_player):
            if len(local_player.inventory) < 3:  # Check if there's space in the inventory
                powerup_info = {
                    "types": powerup.types,
                    "color": powerup.color  # Store the combined color
                }
                local_player.add_to_inventory(powerup_info)
                powerups.remove(powerup)

    for powerup in powerups:
        powerup.update()

    powerups[:] = [powerup for powerup in powerups if powerup.alpha > 0]
        
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
    global waiting_to_choose, in_intermission, current_wave, enemies_per_wave, wave_increase_factor, upgrade_tile_groups, upgrade_selected, boss_spawned, bosses, button_list

    if len(enemies) == 0 and len(bosses) == 0 and not in_intermission:
        in_intermission = True
        upgrade_tile_groups.append(initialize_upgrade_tiles(current_wave))
        upgrade_selected = False  # Reset the flag at the start of intermission

    if in_intermission and upgrade_selected:
        in_intermission = False
        
        current_wave += 1
        enemies_per_wave += wave_increase_factor
        enemies.clear()
        bosses.clear()  # Clear any remaining bosses
        for upgradeButton in button_list:
            if upgradeButton.text == "Choose":
                button_list.remove(upgradeButton)

        if current_wave % 4 == 0:
            # It's a boss round
            boss_x = screen_width // 2
            boss_y = -80  # Spawn above the screen
            boss = Boss(boss_x, boss_y, "dasher", current_wave*2)  # Spawn a dasher boss
            bosses.append(boss)
        else:
            # Spawn regular enemies
            enemies.extend([spawn_enemy(player.x, player.y) for _ in range(enemies_per_wave)])

        upgrade_tile_groups.clear()  # Clear the upgrades after selection
        upgrade_selected = False  # Reset the flag after the intermission ends

def main_menu(screen):
    global is_multiplayer, back_to_main, main_menu_music_playing

    main_menu_music_playing = False

    # Create the main menu instance
    main_menu = Menu(screen)

    # Add buttons to the main menu
    main_menu.add_button(Button("Play", 100, 200, 175, 50, action=gameLoop))
    main_menu.add_button(Button("Credits", 100, 300, 175, 50, action=credits, action_args=(screen,)))
    main_menu.add_button(Button("Quit", 100, 400, 175, 50, action=quit_game))

    # Reset button states
    main_menu.reset_button_states()

    running = True
    while running:
        # Event handling
        # Play main menu music
        if not main_menu_music_playing:
            play_main_menu_music()
            main_menu_music_playing = True

        hover_effect()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                sys.exit()
            else:
                main_menu.handle_event(event)

        # Drawing the menu
        screen.fill(BLACK)  # Clear screen with black background
        draw_text(screen, "RogueBlocks", 52, 100, 100)
        main_menu.draw()
        pygame.display.update()

def credits(screen):
    # Create the main menu instance
    credit_screen = Menu(screen)

    # Add buttons to the main menu
    credit_screen.add_button(Button("Back", 1450, 800, 100, 50, action=back_to_main_menu))

    # Reset button states
    credit_screen.reset_button_states()

    running = True
    while running:
        hover_effect()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                sys.exit()
            else:
                credit_screen.handle_event(event)

        # Drawing the menu
        screen.fill(BLACK)  # Clear screen with black background
        draw_text(screen, "Programming, design, and sound effects by: Ian McMullen", 36, 100, BAR_Y + BAR_HEIGHT)
        draw_text(screen, f"""Music kindly provided by:""", 36, 100, BAR_Y + BAR_HEIGHT + 100)
        draw_text(screen, f""""MTA","In a Heartbeat", "Latin Industries", "Club Diver", "Harmful or Fatal" """, 36, 100, BAR_Y + BAR_HEIGHT + 136)
        draw_text(screen, f"""Kevin MacLeod (incompetech.com)""", 36, 100, BAR_Y + BAR_HEIGHT + 172)
        draw_text(screen, f"""Licensed under Creative Commons: By Attribution 3.0""", 36, 100, BAR_Y + BAR_HEIGHT + 208)
        draw_text(screen, f"""http://creativecommons.org/licenses/by/3.0/""", 36, 100, BAR_Y + BAR_HEIGHT + 240)
        credit_screen.draw()
        pygame.display.update()

def pause_menu(screen):
    pause_menu = Menu(screen)
    pause_menu.add_button(Button("Resume", screen_width // 2 - 100, 200, 200, 50, action=lambda: "resume"))
    pause_menu.add_button(Button("Quit", screen_width // 2 - 100, 300, 200, 50, action=back_to_main_menu))

    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(128)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    pause = True
    while pause:
        hover_effect()
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
    global enemies_per_wave, bosses
    enemies_per_wave = 5
    bosses = []
    
    game_over_menu = Menu(screen)
    game_over_menu.add_button(Button("Main Menu", screen_width // 2 - 125, 300, 250, 50, action=back_to_main_menu))  # Add the button to the menu

    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(128)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    while True:
        hover_effect()
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
    else:  # Left, adjust to spawn to the left of the UI but still on screen
        x = cfg.UI_WIDTH - 40  # Spawning just to the left of UI, 40 is the enemy width
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


    pygame.mixer.music.fadeout(fade_ms)

def play_main_menu_music():
    global current_song
    if current_song != "menu_song":
        if pygame.mixer.music.get_busy():  # Check if any music is currently playing
            pygame.mixer.music.fadeout(1000)  # Fade out the current music
        pygame.mixer.music.load("audio/soundtracks/Club Diver.mp3")
        current_song = "menu_song"
        pygame.mixer.music.play(-1, 0, 1000)
        pygame.mixer.music.set_volume(0.2)

def play_game_music():
    global current_track, current_song  # Use the global variable to keep track across function calls
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.fadeout(1000)  # Fade out the current music

        # Ensure a different track is chosen
        next_track = current_track
        while next_track == current_track:
            next_track = random.choice(soundtracks)
        
        current_track = next_track

        pygame.mixer.music.load(next_track)
        pygame.mixer.music.play(0, 0, 1000)
        pygame.mixer.music.set_volume(0.2)
        current_song = "game_song"

def gameLoop():
    global local_player, enemies_killed, current_wave, in_intermission, intermission_timer, projectiles, enemies_per_wave, projectiles, upgrade_tile_groups, upgrade_selected, powerups, bosses, button_list

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
    upgrade_time = 0
    last_health_regeneration_time = pygame.time.get_ticks()  # Initialize the last health regeneration time
    health_regeneration_interval = 1000  # 1 second interval for health regeneration

    # Player initialization
    local_player = Player()
    enemies = [spawn_enemy(local_player.x, local_player.y) for _ in range(enemies_per_wave)]
    group_to_remove = None
    
    # Fade out main menu music
    pygame.mixer.music.fadeout(1000)

    time.sleep(0.1)
    while running:
        current_time = pygame.time.get_ticks()

        #Begin playing soundtracks
        play_game_music()

        # Health regeneration logic
        if current_time - last_health_regeneration_time >= health_regeneration_interval:
            local_player.hp = min(local_player.hp + local_player.hp_regeneration_rate, local_player.max_hp)
            last_health_regeneration_time = current_time  # Reset the timer
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
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

                # Check for button clicks on upgrade tiles during intermission
                if in_intermission:
                    for tile_group in upgrade_tile_groups:
                        for tile in tile_group:
                            if tile.button.is_clicked((mouse_x, mouse_y)):
                                tile.select_upgrade()
                                upgrade_selected = True  # Set the flag to True after selecting an upgrade
                                upgrade_tile_groups.clear()  # Clear all upgrade tiles
                                button_list.clear()
                                upgrade_time = current_time
                                break
                        if upgrade_selected:
                            break
                        
        # Player input handling
        handle_player_input(local_player, upgrade_time)

        # Handle collisions between enemies
        handle_enemy_collisions(enemies)

        # Update game state
        update_game_state(local_player, enemies, projectiles, powerups)

        # Manage game waves
        manage_waves(enemies, local_player)
        
        hover_effect()

        # Drawing
        draw_game(screen, local_player, enemies, projectiles, bosses)

        # Check for game over
        if local_player.hp <= 0:
            action = game_over(screen, current_wave, enemies_killed)
            if action == "restart":
                reset_game()
                return "restart"
            elif action == "menu":
                reset_game()
                return "menu"

        clock.tick(fps)

def back_to_main_menu():
    importlib.reload(cfg)
    main_menu(screen)

def quit_game():
    pygame.quit()
    sys.exit()

def reset_game():
    global player, enemies, projectiles, enemies_killed, current_wave, initial_player_x, initial_player_y, number_of_enemies, powerups, upgrade_tile_groups, bosses, enemies_per_wave, wave_increase_factor, upgrade_selected, button_list
    player = Player()
    player.x, player.y = initial_player_x, initial_player_y
    enemies = [spawn_enemy(initial_player_x, initial_player_y) for _ in range(number_of_enemies)]
    projectiles = []
    enemies_killed = 0
    current_wave = 1
    initial_player_x = screen_width // 2
    initial_player_y = screen_height // 2
    number_of_enemies = 10
    powerups = []
    upgrade_tile_groups = []
    bosses = []
    enemies_per_wave = 5
    wave_increase_factor = 3
    upgrade_selected = False
    button_list.clear()

def main():
    global enemies, player, bosses
    #Initialize pygame
    pygame.init()
    #Set up game loop
    pygame.display.set_caption("Roguelike Shooter")
    enemies = [spawn_enemy(initial_player_x, initial_player_y) for _ in range(number_of_enemies)]
    main_menu(screen)
    pygame.quit()

if __name__ == "__main__":
    main()