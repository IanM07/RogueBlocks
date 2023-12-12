import pygame
import sys
import json
import socket
import threading
import random
from networking import setup_server, setup_client, send_host_state_to_remote, send_remote_state_to_host, receive_game_state, log_message
from cfg import (screen_width, screen_height, BAR_WIDTH, BAR_HEIGHT, BAR_X, BAR_Y,
                    WHITE, BLACK, RED, GREEN, BLUE, DARK_BLUE, GRAY, initial_player_x, initial_player_y,
                    number_of_enemies, is_multiplayer, network_socket, is_host, screen, projectiles, enemies_per_wave, wave_increase_factor)

class Player:
    def __init__(self):
        self.image = pygame.Surface((50,50))
        self.image.fill((129, 0, 204))
        self.rect = self.image.get_rect()
        self.speed = 3  # Normal speed
        self.sprint_speed = 6  # Sprinting speed
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
            
    def update(self):
        # Sprinting depletes stamina
        if self.is_sprinting:
            self.stamina -= self.stamina_use_rate
            self.stamina = max(self.stamina, 0)

        # Regenerate stamina only when not sprinting and shift key is released
        keys = pygame.key.get_pressed()
        if not self.is_sprinting and not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
            self.stamina += self.stamina_recovery_rate
            self.stamina = min(self.stamina, self.max_stamina)

    def take_damage(self):
        current_time = pygame.time.get_ticks()
        self.hp -= 1  # Reduce HP by 1

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
        self.speed = 1
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

class Button:
    def __init__(self, text, x, y, width, height, action=None, action_args=[]):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.action = action
        self.action_args = action_args

    def draw(self, screen):
        # Draw the button rectangle
        pygame.draw.rect(screen, (0, 0, 0), (self.x, self.y, self.width, self.height))
        # Draw the text on the button
        font = pygame.font.SysFont(None, 30)
        text_surf = font.render(self.text, True, (255, 255, 255))
        screen.blit(text_surf, (self.x + 10, self.y + 10))

    def is_clicked(self, mouse_pos):
        x, y = mouse_pos
        return (self.x <= x <= self.x + self.width) and (self.y <= y <= self.y + self.height)

    def activate(self):
        if self.action:
            return self.action(*self.action_args)

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

def update_game_state(local_player, remote_player, enemies, projectiles):
    # Update local player
    local_player.update()

    # Update remote player if it exists
    if remote_player:
        remote_player.update()

    # Update enemies
    for enemy in enemies:
        nearest_player = find_nearest_player(enemy, [local_player, remote_player])
        if nearest_player:
            enemy.move_towards_player(nearest_player)

    # Update projectiles
    for projectile in projectiles[:]:  # Iterate over a copy of the list
        projectile.update()

        # Check if the projectile is out of bounds
        if projectile_out_of_bounds(projectile):
            projectiles.remove(projectile)
            continue

        # Check for collisions with enemies
        for enemy in enemies[:]:
            if float_based_collision(projectile, enemy):
                enemies.remove(enemy)
                projectiles.remove(projectile)
                break

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

def draw_game(screen, player, enemies, projectiles, is_multiplayer, remote_player):
    screen.fill((0, 0, 0))  # Clear screen with black background

    # Draw player and remote player (in multiplayer mode)
    player.draw(screen)
    if is_multiplayer and remote_player:
        remote_player.draw(screen)

    # Draw enemies and projectiles
    for enemy in enemies:
        enemy.draw(screen)
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

    pygame.display.flip()  # Update the full display Surface to the screen

def update_remote_player(remote_player, player_data):
    # Update the remote player's position
    remote_player.x = player_data['x']
    remote_player.y = player_data['y']

    # Update other properties as needed
    remote_player.hp = player_data.get('hp', remote_player.hp)

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

def update_game_state(local_player, remote_player, enemies, projectiles):
    global enemies_killed

    # Update local player
    local_player.update()

    # Update remote player if it exists
    if remote_player:
        remote_player.update()

    # Update enemies
    for enemy in enemies:
        # The enemy should move towards the nearest player
        nearest_player = find_nearest_player(enemy, [local_player, remote_player])
        enemy.move_towards_player(nearest_player)

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
                        enemies.remove(enemy)
                        projectile.is_active = False
                        enemies_killed += 1
                        break

    # Check for collisions between enemies and players
    for enemy in enemies[:]:
        if float_based_collision(enemy, local_player):
            local_player.take_damage()
            enemies.remove(enemy)
        elif remote_player and float_based_collision(enemy, remote_player):
            remote_player.take_damage()  # Assuming remote_player has a similar take_damage method
            enemies.remove(enemy)

def projectile_out_of_bounds(projectile):
    return (projectile.x < 0 or projectile.x > screen_width or
            projectile.y < 0 or projectile.y > screen_height)

def manage_waves(enemies, player):
    global in_intermission, intermission_timer, current_wave, enemies_per_wave, wave_increase_factor
    
    current_time = pygame.time.get_ticks()
    time_between_waves = 5000  # 5 seconds
    
    # Check if all enemies are defeated and wave is completed
    if len(enemies) == 0 and not in_intermission:
        in_intermission = True
        intermission_timer = current_time + time_between_waves

    # Spawn new wave of enemies after intermission
    if in_intermission and current_time >= intermission_timer:
        in_intermission = False
        current_wave += 1
        enemies_per_wave += wave_increase_factor
        enemies.clear()
        enemies.extend([spawn_enemy(player.x, player.y) for _ in range(enemies_per_wave)])

def main_menu(screen):
    global is_multiplayer

    # Create the main menu instance
    main_menu = Menu(screen)

    # Add buttons to the main menu
    main_menu.add_button(Button("Single Player", 100, 200, 200, 50, action=gameLoop))
    main_menu.add_button(Button("Multiplayer", 100, 300, 200, 50, action=multiplayer_menu, action_args=[screen]))
    main_menu.add_button(Button("Instructions", 100, 400, 150, 50, action=instructions))
    main_menu.add_button(Button("Quit", 100, 500, 100, 50, action=quit_game))

    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                main_menu.handle_event(event)

        # Drawing the menu
        screen.fill((255, 255, 255))  # Clear screen with white background
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

def multiplayer_menu(screen):
    multiplayer_menu = Menu(screen)
    multiplayer_menu.add_button(Button("Join Game", 100, 300, 200, 50, action=join_game))
    multiplayer_menu.add_button(Button("Host Game", 100, 200, 200, 50, action=host_game))
    multiplayer_menu.add_button(Button("Back", 100, 400, 100, 50, action=back_to_main_menu))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            else:
                multiplayer_menu.handle_event(event)

        screen.fill((0, 0, 0))  # Fill screen with background color
        multiplayer_menu.draw()
        pygame.display.update()

def host_game():
    global network_socket, is_host, waiting_for_connection, is_multiplayer
    # Initialize variables
    waiting_for_connection = True
    is_multiplayer = True
    is_host = False

    predefined_port = 54365  # Example port number
    host_ip = socket.gethostbyname(socket.gethostname())
    print(f"Hosting game on {host_ip}:{predefined_port}")

    def server_thread():
        global network_socket, is_host, waiting_for_connection
        try:
            # Set up the server and wait for a client connection
            network_socket = setup_server('', predefined_port)
            print(f"Client connected. Starting game...")

            # Once connected, set flags and exit lobby
            is_host = True
            waiting_for_connection = False
        except Exception as e:
            print(f"Failed to host game: {e}")
            # Optionally, add logic to handle server setup failure
    
    # Start the server thread
    threading.Thread(target=server_thread, daemon=True).start()

    # Lobby screen
    while waiting_for_connection:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill(BLACK)
        draw_text(screen, 'Waiting for other players to join...', 55, 20, 20, WHITE)
        pygame.display.update()

    # After exiting the lobby loop, start the game loop
    if is_host:
        gameLoop()

def join_game():
    global network_socket, is_host, is_multiplayer
    is_multiplayer = True
    # Implement the logic to join a game
    # This could include asking the player to enter the host's IP address and port
    host_ip = input("Enter host IP address: ")  # Use a proper input method
    port = 54365
    network_socket = setup_client(host_ip, int(port))
    is_host = False
    gameLoop()

def find_nearest_player(enemy, players):
    nearest_player = None
    min_distance = float('inf')
    for player in players:
        if player:  # Ensure player is not None
            distance = ((player.x - enemy.x)**2 + (player.y - enemy.y)**2)**0.5
            if distance < min_distance:
                min_distance = distance
                nearest_player = player
    return nearest_player

def handle_multiplayer_interactions(network_socket, local_player, remote_player, projectiles, enemies):
    if is_multiplayer:
        if is_host:
            try:
                # Host-specific logic: sending full game state and processing joiner's state
                send_host_state_to_remote(network_socket, local_player, enemies, projectiles)
                joiner_state = receive_game_state(network_socket)
                log_message("Sending game state to remote player")
            except Exception as e:
                log_message(f"Error in host multiplayer interactions: {e}")

            if joiner_state:
                update_remote_player(remote_player, joiner_state['player'])
                update_projectiles(projectiles, joiner_state['projectiles'])

        else:
            try:
                # Joiner-specific logic: sending player state and receiving full game state
                send_remote_state_to_host(network_socket, local_player, projectiles)
                host_state = receive_game_state(network_socket)
                log_message("Sending player state to host")
            except Exception as e:
                log_message(f"Error in remote multiplayer interactions: {e}")

            if host_state:
                update_remote_player(remote_player, host_state['player'])
                update_projectiles(projectiles, host_state['projectiles'])
                update_enemies(enemies, host_state['enemies'])

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

def send_shoot_signal(sock, player):
    try:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        shoot_signal = {
            'action': 'shoot',
            'player_x': player.x,
            'player_y': player.y,
            'mouse_x': mouse_x,
            'mouse_y': mouse_y
        }
        serialized_data = json.dumps(shoot_signal).encode('utf-8')
        sock.sendall(serialized_data)
    except Exception as e:
        print(f"Error sending shoot signal: {e}")

def create_projectile_based_on_joiner_signal(signal):
    # Calculate direction vector towards the target (mouse position)
    direction_x = signal['mouse_x'] - signal['player_x']
    direction_y = signal['mouse_y'] - signal['player_y']

    # Normalize the direction vector (to maintain constant projectile speed)
    magnitude = (direction_x**2 + direction_y**2)**0.5
    if magnitude != 0:
        direction_x /= magnitude
        direction_y /= magnitude

    # Set the speed of the projectile
    speed = 30  # Adjust as needed
    x_velocity = direction_x * speed
    y_velocity = direction_y * speed

    # Create and return the new projectile
    return Projectile(round(signal['player_x'] + 25), round(signal['player_y'] + 25), x_velocity, y_velocity)

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
    global network_socket, local_player, remote_player, enemies_killed, current_wave, in_intermission, intermission_timer, projectiles, enemies_per_wave, projectiles

    # Initialization
    running = True
    enemies_killed = 0
    current_wave = 1
    last_shot_time = 0
    shot_delay = 500 # milliseconds
    in_intermission = False
    intermission_timer = 0
    mouse_button_down = False
    clock = pygame.time.Clock()
    fps = 60
    
    # Player initialization
    local_player = Player()
    remote_player = Player() if is_multiplayer else None
    enemies = [spawn_enemy(local_player.x, local_player.y) for _ in range(enemies_per_wave)]

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

        # Player input handling
        handle_player_input(local_player)

        # Handle collisions between enemies
        handle_enemy_collisions(enemies)

        # Update game state
        update_game_state(local_player, remote_player, enemies, projectiles)

        # Handle multiplayer interactions
        handle_multiplayer_interactions(network_socket, local_player, remote_player, projectiles, enemies)

        # Manage game waves
        manage_waves(enemies, local_player)

        # Drawing
        draw_game(screen, local_player, enemies, projectiles, is_multiplayer, remote_player)

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
