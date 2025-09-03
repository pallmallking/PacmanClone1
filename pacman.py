# pacman_game.py

import pygame
import random
import sys
import numpy as np

# Constants
WIDTH, HEIGHT = 560, 620
TILE_SIZE = 20
FPS = 20  # Increased for smoother movement
MOVE_SPEED = 2  # Pixels per frame for smooth movement

# Colors
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
PINK = (255, 182, 193)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)

# Game constants
POWER_PELLET_DURATION = 100  # frames
GHOST_SCORE = 200
POWER_PELLET_SCORE = 50
DOT_SCORE = 10
FRUIT_SCORE = 100

class Fruit:
    """
    Represents a bonus fruit that appears occasionally for extra points.
    
    :ivar rect: The rectangular area defining the fruit's position and size.
    :type rect: pygame.Rect
    :ivar eaten: Indicates whether the fruit has been consumed.
    :type eaten: bool
    :ivar spawn_timer: Timer for fruit appearance.
    :type spawn_timer: int
    :ivar visible: Whether the fruit is currently visible.
    :type visible: bool
    :ivar fruit_type: Type of fruit (affects appearance and score).
    :type fruit_type: int
    """
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + TILE_SIZE//4, y + TILE_SIZE//4, TILE_SIZE//2, TILE_SIZE//2)
        self.eaten = False
        self.spawn_timer = 0
        self.visible = False
        self.fruit_type = 0  # 0=cherry, 1=strawberry, 2=orange
        
    def update(self):
        """Update fruit visibility and spawn timing"""
        if not self.eaten:
            self.spawn_timer += 1
            # Appear for limited time
            if 300 < self.spawn_timer < 500:  # Visible for ~10 seconds
                self.visible = True
            else:
                self.visible = False
                if self.spawn_timer > 1000:  # Reset after ~50 seconds
                    self.spawn_timer = 0
                    self.fruit_type = (self.fruit_type + 1) % 3

    def draw(self, screen):
        if not self.eaten and self.visible:
            # Draw different fruit types
            colors = [RED, PINK, ORANGE]  # Cherry, Strawberry, Orange
            pygame.draw.circle(screen, colors[self.fruit_type], self.rect.center, 6)
            # Add highlight
            pygame.draw.circle(screen, WHITE, (self.rect.center[0]-2, self.rect.center[1]-2), 2)

class SoundManager:
    """
    Handles sound effects for the game using procedurally generated sounds.
    """
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.sounds = {}
        self.generate_sounds()
        self.sound_enabled = True
    
    def generate_sounds(self):
        """Generate simple sound effects using sine waves"""
        try:
            # Dot collection sound (short beep)
            duration = 0.1
            sample_rate = 22050
            frequency = 800
            t = np.linspace(0, duration, int(sample_rate * duration))
            wave = np.sin(2 * np.pi * frequency * t) * 0.3
            wave = (wave * 32767).astype(np.int16)
            stereo_wave = np.column_stack((wave, wave))
            stereo_wave = np.ascontiguousarray(stereo_wave)
            self.sounds['dot'] = pygame.sndarray.make_sound(stereo_wave)
            
            # Power pellet sound (ascending tone)
            duration = 0.3
            frequencies = [400, 500, 600, 700]
            wave = np.array([])
            for freq in frequencies:
                t = np.linspace(0, duration/4, int(sample_rate * duration/4))
                tone = np.sin(2 * np.pi * freq * t) * 0.3
                wave = np.concatenate([wave, tone])
            wave = (wave * 32767).astype(np.int16)
            stereo_wave = np.column_stack((wave, wave))
            stereo_wave = np.ascontiguousarray(stereo_wave)
            self.sounds['power_pellet'] = pygame.sndarray.make_sound(stereo_wave)
            
            # Ghost eaten sound (descending tone)
            duration = 0.5
            frequency_start = 1000
            frequency_end = 200
            t = np.linspace(0, duration, int(sample_rate * duration))
            frequencies = np.linspace(frequency_start, frequency_end, len(t))
            wave = np.sin(2 * np.pi * frequencies * t) * 0.4
            wave = (wave * 32767).astype(np.int16)
            stereo_wave = np.column_stack((wave, wave))
            stereo_wave = np.ascontiguousarray(stereo_wave)
            self.sounds['ghost_eaten'] = pygame.sndarray.make_sound(stereo_wave)
            
            # Death sound (dramatic descending)
            duration = 1.0
            frequency_start = 400
            frequency_end = 100
            t = np.linspace(0, duration, int(sample_rate * duration))
            frequencies = np.linspace(frequency_start, frequency_end, len(t))
            wave = np.sin(2 * np.pi * frequencies * t) * 0.5
            # Add tremolo effect
            tremolo = 1 + 0.3 * np.sin(2 * np.pi * 5 * t)
            wave = wave * tremolo
            wave = (wave * 32767).astype(np.int16)
            stereo_wave = np.column_stack((wave, wave))
            stereo_wave = np.ascontiguousarray(stereo_wave)
            self.sounds['death'] = pygame.sndarray.make_sound(stereo_wave)
            
        except Exception as e:
            print(f"Could not generate sounds: {e}")
            self.sound_enabled = False
    
    def play(self, sound_name):
        """Play a sound effect"""
        if self.sound_enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass  # Ignore sound errors

# Maze (1 = wall, 0 = path, P = power pellet location)
MAZE = [
    "11111111111111111111111111111",
    "1000000000001110000000000001",
    "1011110111101110111101111101",
    "1P00010000000000000001000P1",
    "1011010111111111111010110101",
    "1000010100000000000101000001",
    "1111110111101110111101111111",
    "0000000100000000000001000000",
    "1111110101111111110101111111",
    "1000000001000000010000000001",
    "1011111101011001010111111101",
    "1000000000010110100000000001",
    "1011111111010110101111111101",
    "1000000001000000010000000001",
    "1111110101111111110101111111",
    "0000000100000000000001000000",
    "1111110111101110111101111111",
    "1000010100000000000101000001",
    "1011010111111111111010110101",
    "1P00010000000000000001000P1",
    "1011110111101110111101111101",
    "1000000000001110000000000001",
    "11111111111111111111111111111"
]

class Player:
    """
    Represents a player in a maze game. The Player object maintains its position,
    movement logic, collision detection with walls, and rendering on the screen.

    The starting position and movement of the player are initialized during object
    creation. The class allows resetting the player to its starting position,
    updating its position based on movement, and rendering the player on-screen.

    Attributes:
    ----------
    :ivar start_x: The starting x-coordinate of the player.
    :ivar start_y: The starting y-coordinate of the player.
    :ivar rect: The player's rectangular shape represented as a `pygame.Rect` object.
    :ivar dx: The distance the player moves horizontally per update.
    :ivar dy: The distance the player moves vertically per update.
    :ivar last_direction: The last direction the player was moving (for ghost AI).
    :ivar next_dx: The next horizontal direction queued by player input.
    :ivar next_dy: The next vertical direction queued by player input.
    """
    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.dx = MOVE_SPEED
        self.dy = 0
        self.last_direction = (1, 0)  # Track direction for ghost AI
        self.next_dx = MOVE_SPEED
        self.next_dy = 0

    def reset(self):
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.dx = MOVE_SPEED
        self.dy = 0
        self.last_direction = (1, 0)
        self.next_dx = MOVE_SPEED
        self.next_dy = 0

    def set_direction(self, dx, dy):
        """Queue a direction change"""
        self.next_dx = dx
        self.next_dy = dy

    def move(self, maze):
        # Try to change to queued direction if possible
        if self.next_dx != self.dx or self.next_dy != self.dy:
            test_rect = self.rect.move(self.next_dx, self.next_dy)
            if not self.collides_with_walls(test_rect, maze):
                self.dx = self.next_dx
                self.dy = self.next_dy
                # Update direction tracking
                if self.dx != 0 or self.dy != 0:
                    self.last_direction = (
                        1 if self.dx > 0 else -1 if self.dx < 0 else 0,
                        1 if self.dy > 0 else -1 if self.dy < 0 else 0
                    )
        
        # Move in current direction
        new_rect = self.rect.move(self.dx, self.dy)
        if not self.collides_with_walls(new_rect, maze):
            self.rect = new_rect
        else:
            # Stop if hitting a wall
            self.dx = 0
            self.dy = 0

    def collides_with_walls(self, rect, maze):
        for row_index, row in enumerate(maze):
            for col_index, cell in enumerate(row):
                if cell == "1":
                    wall_rect = pygame.Rect(col_index * TILE_SIZE, row_index * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if rect.colliderect(wall_rect):
                        return True
        return False

    def draw(self, screen):
        # Draw Pacman with mouth animation
        center = self.rect.center
        radius = TILE_SIZE // 2
        
        # Calculate mouth angle based on direction
        if self.dx > 0:  # Moving right
            start_angle = 0.2
            end_angle = -0.2
        elif self.dx < 0:  # Moving left
            start_angle = 3.34
            end_angle = 2.94
        elif self.dy > 0:  # Moving down
            start_angle = 1.77
            end_angle = 1.37
        elif self.dy < 0:  # Moving up
            start_angle = 4.91
            end_angle = 4.51
        else:  # Not moving
            start_angle = 0
            end_angle = 6.28
        
        # Draw the Pacman circle
        pygame.draw.circle(screen, YELLOW, center, radius)
        
        # Draw the mouth (black triangle)
        if self.dx != 0 or self.dy != 0:
            mouth_points = [center]
            import math
            for angle in [start_angle, end_angle]:
                x = center[0] + radius * math.cos(angle)
                y = center[1] + radius * math.sin(angle)
                mouth_points.append((x, y))
            if len(mouth_points) == 3:
                pygame.draw.polygon(screen, BLACK, mouth_points)

class Ghost:
    """
    Represents a Ghost character in the game.

    Manages the behavior and attributes of a ghost, such as its
    position, movement, and interactions with walls, the player,
    and the maze. Handles the ghost's color-dependent logic and
    its response within the game environment.

    :ivar start_x: Initial x-coordinate of the ghost.
    :type start_x: int
    :ivar start_y: Initial y-coordinate of the ghost.
    :type start_y: int
    :ivar rect: The rectangular area representing the ghost's position
        and size on the screen.
    :type rect: pygame.Rect
    :ivar direction: The current movement direction of the ghost as a
        tuple of x and y deltas.
    :type direction: tuple[int, int]
    :ivar color: The color of the ghost, affecting its behavior.
    :type color: tuple[int, int, int]
    :ivar vulnerable: Whether the ghost is vulnerable to being eaten.
    :type vulnerable: bool
    :ivar vulnerability_timer: Time remaining for vulnerability.
    :type vulnerability_timer: int
    :ivar respawn_timer: Time until ghost respawns after being eaten.
    :type respawn_timer: int
    :ivar eaten: Whether the ghost has been eaten.
    :type eaten: bool
    :ivar ai_type: The AI behavior pattern of the ghost.
    :type ai_type: str
    """
    def __init__(self, x, y, color=RED, ai_type="random"):
        self.start_x = x
        self.start_y = y
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.direction = random.choice([(MOVE_SPEED,0), (-MOVE_SPEED,0), (0,MOVE_SPEED), (0,-MOVE_SPEED)])
        self.color = color
        self.original_color = color
        self.vulnerable = False
        self.vulnerability_timer = 0
        self.respawn_timer = 0
        self.eaten = False
        self.ai_type = ai_type
        self.direction_change_timer = 0

    def reset(self):
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.direction = random.choice([(MOVE_SPEED,0), (-MOVE_SPEED,0), (0,MOVE_SPEED), (0,-MOVE_SPEED)])
        self.vulnerable = False
        self.vulnerability_timer = 0
        self.respawn_timer = 0
        self.eaten = False
        self.color = self.original_color
        self.direction_change_timer = 0

    def make_vulnerable(self):
        self.vulnerable = True
        self.vulnerability_timer = POWER_PELLET_DURATION
        self.color = BLUE

    def update_vulnerability(self):
        if self.vulnerability_timer > 0:
            self.vulnerability_timer -= 1
            # Flash when almost done
            if self.vulnerability_timer < 30 and self.vulnerability_timer % 10 < 5:
                self.color = WHITE
            else:
                self.color = BLUE
        else:
            self.vulnerable = False
            self.color = self.original_color

    def respawn(self):
        if self.respawn_timer > 0:
            self.respawn_timer -= 1
            if self.respawn_timer == 0:
                self.eaten = False
                self.rect.x = self.start_x
                self.rect.y = self.start_y
                self.vulnerable = False
                self.color = self.original_color

    def move(self, maze, player_pos=None, player_direction=None):
        if self.eaten:
            self.respawn()
            return
            
        self.update_vulnerability()
        self.direction_change_timer += 1
        
        # Different AI behaviors based on type and state
        if self.vulnerable:
            # Run away from player
            if player_pos and self.direction_change_timer % 10 == 0:
                px, py = player_pos
                gx, gy = self.rect.x, self.rect.y
                if abs(px - gx) > abs(py - gy):
                    self.direction = (-MOVE_SPEED if px > gx else MOVE_SPEED, 0)
                else:
                    self.direction = (0, -MOVE_SPEED if py > gy else MOVE_SPEED)
        else:
            # Normal AI behavior - change direction less frequently for smoother movement
            change_freq = 40  # Frames between direction changes
            if self.ai_type == "aggressive" and player_pos and self.direction_change_timer % 20 == 0:
                # Red ghost - aggressive chasing
                px, py = player_pos
                gx, gy = self.rect.x, self.rect.y
                if abs(px - gx) > abs(py - gy):
                    self.direction = (MOVE_SPEED if px > gx else -MOVE_SPEED, 0)
                else:
                    self.direction = (0, MOVE_SPEED if py > gy else -MOVE_SPEED)
            elif self.ai_type == "ambush" and player_pos and player_direction and self.direction_change_timer % 30 == 0:
                # Pink ghost - tries to ambush 4 tiles ahead of player
                px, py = player_pos
                dx, dy = player_direction
                target_x = px + (4 * TILE_SIZE * dx)
                target_y = py + (4 * TILE_SIZE * dy)
                gx, gy = self.rect.x, self.rect.y
                if abs(target_x - gx) > abs(target_y - gy):
                    self.direction = (MOVE_SPEED if target_x > gx else -MOVE_SPEED, 0)
                else:
                    self.direction = (0, MOVE_SPEED if target_y > gy else -MOVE_SPEED)
            elif self.ai_type == "patrol" and self.direction_change_timer % change_freq == 0:
                # Cyan ghost - patrols in patterns
                self.direction = random.choice([(MOVE_SPEED,0), (-MOVE_SPEED,0), (0,MOVE_SPEED), (0,-MOVE_SPEED)])
            elif self.ai_type == "random" and self.direction_change_timer % (change_freq//2) == 0:
                if random.randint(0, 10) > 7:
                    self.direction = random.choice([(MOVE_SPEED,0), (-MOVE_SPEED,0), (0,MOVE_SPEED), (0,-MOVE_SPEED)])

        new_rect = self.rect.move(*self.direction)
        if not self.collides_with_walls(new_rect, maze):
            self.rect = new_rect
        else:
            # Change direction when hitting a wall
            self.direction = random.choice([(MOVE_SPEED,0), (-MOVE_SPEED,0), (0,MOVE_SPEED), (0,-MOVE_SPEED)])

    def collides_with_walls(self, rect, maze):
        for row_index, row in enumerate(maze):
            for col_index, cell in enumerate(row):
                if cell == "1":
                    wall_rect = pygame.Rect(col_index * TILE_SIZE, row_index * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if rect.colliderect(wall_rect):
                        return True
        return False

    def draw(self, screen):
        if not self.eaten:
            pygame.draw.rect(screen, self.color, self.rect)
            # Add eyes
            eye_size = 3
            eye1_pos = (self.rect.x + 5, self.rect.y + 5)
            eye2_pos = (self.rect.x + 12, self.rect.y + 5)
            pygame.draw.circle(screen, WHITE, eye1_pos, eye_size)
            pygame.draw.circle(screen, WHITE, eye2_pos, eye_size)

class Dot:
    """
    Represents a collectible dot in a game.

    This class is designed to represent a dot that can be consumed by
    a player during gameplay. Each dot has a position on the game screen
    and can be drawn or marked as eaten when collected.

    :ivar rect: The rectangular area defining the dot's position and size.
    :type rect: pygame.Rect
    :ivar eaten: Indicates whether the dot has been consumed.
    :type eaten: bool
    """
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + TILE_SIZE//4, y + TILE_SIZE//4, TILE_SIZE//2, TILE_SIZE//2)
        self.eaten = False

    def draw(self, screen):
        if not self.eaten:
            pygame.draw.circle(screen, GREEN, self.rect.center, 4)

class PowerPellet:
    """
    Represents a power pellet that grants temporary power to eat ghosts.
    
    Power pellets are larger than regular dots and give the player
    the ability to eat ghosts for a limited time when consumed.
    
    :ivar rect: The rectangular area defining the power pellet's position and size.
    :type rect: pygame.Rect
    :ivar eaten: Indicates whether the power pellet has been consumed.
    :type eaten: bool
    :ivar flash_timer: Timer for flashing animation effect.
    :type flash_timer: int
    """
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + TILE_SIZE//6, y + TILE_SIZE//6, TILE_SIZE//1.5, TILE_SIZE//1.5)
        self.eaten = False
        self.flash_timer = 0

    def draw(self, screen):
        if not self.eaten:
            self.flash_timer += 1
            # Flash effect
            if self.flash_timer % 20 < 15:
                pygame.draw.circle(screen, YELLOW, self.rect.center, 8)
            else:
                pygame.draw.circle(screen, WHITE, self.rect.center, 8)

class Game:
    """
    Represents the main game logic for Pacman.

    Handles the initialization, gameplay logic, events, rendering,
    and overall functionality of the Pacman game. This class manages
    the player, ghosts, maze, dots, and game state such as the score,
    lives, and game over status.

    :ivar screen: The game window surface where elements are drawn.
    :type screen: pygame.Surface
    :ivar clock: Controls the frame rate of the game.
    :type clock: pygame.time.Clock
    :ivar maze: The layout of the game maze, defined as a 2D list.
    :type maze: list[list[str]]
    :ivar player: The player character in the game (Pacman).
    :type player: Player
    :ivar ghosts: A list of ghost characters in the game.
    :type ghosts: list[Ghost]
    :ivar dots: A collection of all dots present in the maze.
    :type dots: list[Dot]
    :ivar power_pellets: A collection of all power pellets in the maze.
    :type power_pellets: list[PowerPellet]
    :ivar score: The current game score.
    :type score: int
    :ivar font: The font used to render text on the screen.
    :type font: pygame.font.Font
    :ivar game_over: Indicates whether the game is over.
    :type game_over: bool
    :ivar lives: The number of lives remaining for the player.
    :type lives: int
    :ivar level: The current game level.
    :type level: int
    :ivar game_won: Indicates whether the player has won the current level.
    :type game_won: bool
    :ivar power_mode: Whether the player is in power mode.
    :type power_mode: bool
    :ivar ghost_combo: Multiplier for ghost eating scoring.
    :type ghost_combo: int
    :ivar bonus_fruit: The bonus fruit that occasionally appears.
    :type bonus_fruit: Fruit
    :ivar show_menu: Whether to show the start menu.
    :type show_menu: bool
    :ivar paused: Whether the game is paused.
    :type paused: bool
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pacman Clone - Enhanced Edition")
        self.clock = pygame.time.Clock()
        self.sound_manager = SoundManager()
        self.maze = MAZE
        self.player = Player(1 * TILE_SIZE, 1 * TILE_SIZE)
        self.ghosts = [
            Ghost(13 * TILE_SIZE, 11 * TILE_SIZE, RED, "aggressive"),     # Blinky - aggressive
            Ghost(14 * TILE_SIZE, 11 * TILE_SIZE, PINK, "ambush"),       # Pinky - ambush
            Ghost(13 * TILE_SIZE, 12 * TILE_SIZE, CYAN, "patrol"),       # Inky - patrol  
            Ghost(14 * TILE_SIZE, 12 * TILE_SIZE, ORANGE, "random")      # Clyde - random
        ]
        self.dots = self.create_dots()
        self.power_pellets = self.create_power_pellets()
        self.bonus_fruit = Fruit(14 * TILE_SIZE, 16 * TILE_SIZE)  # Center of maze
        self.score = 0
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 48)
        self.game_over = False
        self.lives = 3
        self.level = 1
        self.game_won = False
        self.power_mode = False
        self.ghost_combo = 1
        self.show_menu = True
        self.paused = False

    def reset_positions(self):
        self.player.reset()
        for ghost in self.ghosts:
            ghost.reset()

    def create_dots(self) -> list[Dot]:
        dots = []
        for row_index, row in enumerate(self.maze):
            for col_index, cell in enumerate(row):
                if cell == "0":
                    dots.append(Dot(col_index * TILE_SIZE, row_index * TILE_SIZE))
        return dots
    
    def create_power_pellets(self) -> list[PowerPellet]:
        power_pellets = []
        for row_index, row in enumerate(self.maze):
            for col_index, cell in enumerate(row):
                if cell == "P":
                    power_pellets.append(PowerPellet(col_index * TILE_SIZE, row_index * TILE_SIZE))
        return power_pellets

    def next_level(self):
        self.level += 1
        self.dots = self.create_dots()
        self.power_pellets = self.create_power_pellets()
        self.bonus_fruit = Fruit(14 * TILE_SIZE, 16 * TILE_SIZE)
        self.reset_positions()
        self.game_won = False
        # Increase difficulty slightly by increasing game speed
        global FPS
        FPS = min(30, 20 + self.level * 2)

    def draw_maze(self):
        for row_index, row in enumerate(self.maze):
            for col_index, cell in enumerate(row):
                if cell == "1":
                    pygame.draw.rect(
                        self.screen,
                        BLUE,
                        pygame.Rect(col_index * TILE_SIZE, row_index * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    )

    def handle_events(self):
        keys = pygame.key.get_pressed()
        
        # Menu controls
        if self.show_menu:
            if keys[pygame.K_SPACE]:
                self.show_menu = False
            return
        
        # Pause toggle
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and not self.game_over and not self.game_won:
                    self.paused = not self.paused
        
        # Game controls (only when not paused)
        if not self.paused:
            if keys[pygame.K_LEFT]:
                self.player.set_direction(-MOVE_SPEED, 0)
            elif keys[pygame.K_RIGHT]:
                self.player.set_direction(MOVE_SPEED, 0)
            elif keys[pygame.K_UP]:
                self.player.set_direction(0, -MOVE_SPEED)
            elif keys[pygame.K_DOWN]:
                self.player.set_direction(0, MOVE_SPEED)
            
        if (self.game_over or self.game_won) and keys[pygame.K_r]:
            self.__init__()

    def update_dots(self):
        for dot in self.dots:
            if not dot.eaten and self.player.rect.colliderect(dot.rect):
                dot.eaten = True
                self.score += DOT_SCORE
                self.sound_manager.play('dot')
        
        # Check win condition
        if all(dot.eaten for dot in self.dots):
            self.game_won = True
    
    def update_power_pellets(self):
        for pellet in self.power_pellets:
            if not pellet.eaten and self.player.rect.colliderect(pellet.rect):
                pellet.eaten = True
                self.score += POWER_PELLET_SCORE
                self.power_mode = True
                self.ghost_combo = 1
                self.sound_manager.play('power_pellet')
                # Make all ghosts vulnerable
                for ghost in self.ghosts:
                    ghost.make_vulnerable()
    
    def update_bonus_fruit(self):
        """Update bonus fruit and check for collection"""
        self.bonus_fruit.update()
        if (not self.bonus_fruit.eaten and self.bonus_fruit.visible and 
            self.player.rect.colliderect(self.bonus_fruit.rect)):
            self.bonus_fruit.eaten = True
            fruit_scores = [100, 300, 500]  # Cherry, Strawberry, Orange
            self.score += fruit_scores[self.bonus_fruit.fruit_type]
            self.sound_manager.play('power_pellet')  # Use power pellet sound for now

    def check_collisions(self):
        for ghost in self.ghosts:
            if self.player.rect.colliderect(ghost.rect) and not ghost.eaten:
                if ghost.vulnerable:
                    # Eat the ghost
                    ghost.eaten = True
                    ghost.respawn_timer = 60  # Respawn after 60 frames
                    self.score += GHOST_SCORE * self.ghost_combo
                    self.ghost_combo += 1
                    self.sound_manager.play('ghost_eaten')
                else:
                    # Ghost catches player
                    self.lives -= 1
                    self.sound_manager.play('death')
                    if self.lives <= 0:
                        self.game_over = True
                    else:
                        self.reset_positions()

    def draw_score(self):
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        
        self.screen.blit(score_text, (10, HEIGHT - 60))
        self.screen.blit(lives_text, (200, HEIGHT - 60))
        self.screen.blit(level_text, (350, HEIGHT - 60))
        
        # Power mode indicator
        if any(ghost.vulnerable for ghost in self.ghosts):
            power_text = self.small_font.render("POWER MODE!", True, YELLOW)
            self.screen.blit(power_text, (10, HEIGHT - 30))
        
        if self.game_over:
            over_text = self.font.render("GAME OVER - Press R to Restart", True, RED)
            self.screen.blit(over_text, (WIDTH//2 - 220, HEIGHT//2))
        elif self.game_won:
            if self.level >= 3:  # Win after 3 levels
                win_text = self.font.render("CONGRATULATIONS! YOU WON!", True, GREEN)
                restart_text = self.small_font.render("Press R to Play Again", True, WHITE)
                self.screen.blit(win_text, (WIDTH//2 - 200, HEIGHT//2 - 20))
                self.screen.blit(restart_text, (WIDTH//2 - 100, HEIGHT//2 + 20))
            else:
                next_text = self.font.render(f"Level {self.level} Complete!", True, GREEN)
                continue_text = self.small_font.render("Press R to Continue", True, WHITE)
                self.screen.blit(next_text, (WIDTH//2 - 150, HEIGHT//2 - 20))
                self.screen.blit(continue_text, (WIDTH//2 - 80, HEIGHT//2 + 20))

    def draw_menu(self):
        """Draw the start menu"""
        self.screen.fill(BLACK)
        
        # Title
        title_text = self.large_font.render("PACMAN CLONE", True, YELLOW)
        subtitle_text = self.font.render("Enhanced Edition", True, WHITE)
        self.screen.blit(title_text, (WIDTH//2 - 150, HEIGHT//3))
        self.screen.blit(subtitle_text, (WIDTH//2 - 80, HEIGHT//3 + 60))
        
        # Instructions
        instructions = [
            "Arrow Keys - Move Pacman",
            "P - Pause Game",
            "R - Restart (when game over)",
            "",
            "Collect dots and power pellets!",
            "Eat ghosts when they're blue!",
            "Complete levels to win!",
            "",
            "Press SPACE to Start"
        ]
        
        y_offset = HEIGHT//2
        for instruction in instructions:
            if instruction:  # Skip empty lines
                text = self.small_font.render(instruction, True, WHITE)
                x_pos = WIDTH//2 - text.get_width()//2
                self.screen.blit(text, (x_pos, y_offset))
            y_offset += 25
    
    def draw_pause_overlay(self):
        """Draw pause overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Pause text
        pause_text = self.large_font.render("PAUSED", True, YELLOW)
        resume_text = self.font.render("Press P to Resume", True, WHITE)
        
        self.screen.blit(pause_text, (WIDTH//2 - 80, HEIGHT//2 - 40))
        self.screen.blit(resume_text, (WIDTH//2 - 100, HEIGHT//2 + 20))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.handle_events()
            
            # Show menu
            if self.show_menu:
                self.draw_menu()
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            if not self.game_over and not self.paused:
                if self.game_won:
                    # Handle level progression
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_r]:
                        if self.level >= 3:
                            self.__init__()  # Restart game after winning
                        else:
                            self.next_level()  # Go to next level
                else:
                    # Normal gameplay
                    self.player.move(self.maze)
                    self.update_dots()
                    self.update_power_pellets()
                    self.update_bonus_fruit()
                    for ghost in self.ghosts:
                        ghost.move(self.maze, self.player.rect.center, self.player.last_direction)
                    self.check_collisions()

            # Rendering
            self.screen.fill(BLACK)
            self.draw_maze()
            
            # Draw dots and power pellets
            for dot in self.dots:
                dot.draw(self.screen)
            for pellet in self.power_pellets:
                pellet.draw(self.screen)
            
            # Draw bonus fruit
            self.bonus_fruit.draw(self.screen)
                
            # Draw game entities
            self.player.draw(self.screen)
            for ghost in self.ghosts:
                ghost.draw(self.screen)
                
            self.draw_score()
            
            # Draw pause overlay if paused
            if self.paused:
                self.draw_pause_overlay()
            
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == '__main__':
    Game().run()
