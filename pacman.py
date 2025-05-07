# pacman_game.py

import pygame
import random
import sys

# Constants
WIDTH, HEIGHT = 560, 620
TILE_SIZE = 20
FPS = 10

# Colors
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)

# Maze (1 = wall, 0 = path)
MAZE = [
    "11111111111111111111",
    "10000000001100000001",
    "10111111101101111101",
    "10100000100001000001",
    "10101111111101111001",
    "10100010000001000001",
    "10111110111101011101",
    "10000000100000000001",
    "11111111111111111111"
]

class Player:
    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.dx = TILE_SIZE
        self.dy = 0

    def reset(self):
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.dx = TILE_SIZE
        self.dy = 0

    def move(self, maze):
        new_rect = self.rect.move(self.dx, self.dy)
        if not self.collides_with_walls(new_rect, maze):
            self.rect = new_rect

    def collides_with_walls(self, rect, maze):
        for row_index, row in enumerate(maze):
            for col_index, cell in enumerate(row):
                if cell == "1":
                    wall_rect = pygame.Rect(col_index * TILE_SIZE, row_index * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if rect.colliderect(wall_rect):
                        return True
        return False

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, self.rect.center, TILE_SIZE // 2)

class Ghost:
    def __init__(self, x, y, color=RED):
        self.start_x = x
        self.start_y = y
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.direction = random.choice([(TILE_SIZE,0), (-TILE_SIZE,0), (0,TILE_SIZE), (0,-TILE_SIZE)])
        self.color = color

    def reset(self):
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.direction = random.choice([(TILE_SIZE,0), (-TILE_SIZE,0), (0,TILE_SIZE), (0,-TILE_SIZE)])

    def move(self, maze, player_pos=None):
        if self.color == RED:
            if random.randint(0, 10) > 8:
                self.direction = random.choice([(TILE_SIZE,0), (-TILE_SIZE,0), (0,TILE_SIZE), (0,-TILE_SIZE)])
        elif self.color == ORANGE and player_pos:
            px, py = player_pos
            gx, gy = self.rect.x, self.rect.y
            if abs(px - gx) > abs(py - gy):
                self.direction = (TILE_SIZE if px > gx else -TILE_SIZE, 0)
            else:
                self.direction = (0, TILE_SIZE if py > gy else -TILE_SIZE)

        new_rect = self.rect.move(*self.direction)
        if not self.collides_with_walls(new_rect, maze):
            self.rect = new_rect

    def collides_with_walls(self, rect, maze):
        for row_index, row in enumerate(maze):
            for col_index, cell in enumerate(row):
                if cell == "1":
                    wall_rect = pygame.Rect(col_index * TILE_SIZE, row_index * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if rect.colliderect(wall_rect):
                        return True
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class Dot:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + TILE_SIZE//4, y + TILE_SIZE//4, TILE_SIZE//2, TILE_SIZE//2)
        self.eaten = False

    def draw(self, screen):
        if not self.eaten:
            pygame.draw.circle(screen, GREEN, self.rect.center, 4)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pacman")
        self.clock = pygame.time.Clock()
        self.maze = MAZE
        self.player = Player(1 * TILE_SIZE, 1 * TILE_SIZE)
        self.ghosts = [Ghost(10 * TILE_SIZE, 1 * TILE_SIZE, RED), Ghost(10 * TILE_SIZE, 5 * TILE_SIZE, ORANGE)]
        self.dots = self.create_dots()
        self.score = 0
        self.font = pygame.font.SysFont(None, 36)
        self.game_over = False
        self.lives = 3

    def reset_positions(self):
        self.player.reset()
        for ghost in self.ghosts:
            ghost.reset()

    def create_dots(self):
        dots = []
        for row_index, row in enumerate(self.maze):
            for col_index, cell in enumerate(row):
                if cell == "0":
                    dots.append(Dot(col_index * TILE_SIZE, row_index * TILE_SIZE))
        return dots

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
        if keys[pygame.K_LEFT]:
            self.player.dx, self.player.dy = -TILE_SIZE, 0
        elif keys[pygame.K_RIGHT]:
            self.player.dx, self.player.dy = TILE_SIZE, 0
        elif keys[pygame.K_UP]:
            self.player.dx, self.player.dy = 0, -TILE_SIZE
        elif keys[pygame.K_DOWN]:
            self.player.dx, self.player.dy = 0, TILE_SIZE
        if self.game_over and keys[pygame.K_r]:
            self.__init__()

    def update_dots(self):
        for dot in self.dots:
            if not dot.eaten and self.player.rect.colliderect(dot.rect):
                dot.eaten = True
                self.score += 10

    def check_collisions(self):
        for ghost in self.ghosts:
            if self.player.rect.colliderect(ghost.rect):
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                else:
                    self.reset_positions()

    def draw_score(self):
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        self.screen.blit(score_text, (10, HEIGHT - 40))
        self.screen.blit(lives_text, (200, HEIGHT - 40))
        if self.game_over:
            over_text = self.font.render("Game Over - Press R to Restart", True, RED)
            self.screen.blit(over_text, (WIDTH//2 - 200, HEIGHT//2))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.handle_events()

            if not self.game_over:
                self.player.move(self.maze)
                self.update_dots()
                for ghost in self.ghosts:
                    ghost.move(self.maze, self.player.rect.center)
                self.check_collisions()

            self.screen.fill(BLACK)
            self.draw_maze()
            for dot in self.dots:
                dot.draw(self.screen)
            self.player.draw(self.screen)
            for ghost in self.ghosts:
                ghost.draw(self.screen)
            self.draw_score()
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == '__main__':
    Game().run()
