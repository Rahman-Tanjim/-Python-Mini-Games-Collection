# Write your code here :-)
# ここにコードを書いてね :-)
# invader1.py
# AI2 Programming II (by: Mitsuo Yamamoto)
# Modified for unlimited play + auto-fire + fullscreen

import sys
import pygame
from pygame.locals import *

# color definition
WHITE = (225, 225, 255)
BLACK = (0, 1, 0)
RED = (255, 0, 1)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 80, 0)


# player class
class Player(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (screen_width // 2, screen_height - 50)
        self.speed = 5
        self.screen_width = screen_width

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < self.screen_width:
            self.rect.x += self.speed


# alien class
class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.speed = 2

    def update(self):
        self.rect.x += self.speed
        if self.rect.right >= 1200 or self.rect.left <= 0:  # adjust for large screen
            self.speed = -self.speed
            self.rect.y += 60


# bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((2, 10))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y)
        self.speed = -30

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()


def create_aliens(all_sprites, aliens, screen_width):
    """Spawn a new wave of aliens"""
    cols = 12
    rows = 3
    start_x = 50
    start_y = 70
    spacing_x = 60
    spacing_y = 60

    for i in range(cols):
        for j in range(rows):
            x = start_x + i * spacing_x
            y = start_y + j * spacing_y
            alien = Alien(x, y)
            all_sprites.add(alien)
            aliens.add(alien)


def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # fullscreen
    screen_width, screen_height = screen.get_size()
    pygame.display.set_caption("Space Invaders - Auto Fire")

    font = pygame.font.SysFont(None, 55)

    all_sprites = pygame.sprite.Group()
    aliens = pygame.sprite.Group()
    bullets = pygame.sprite.Group()

    player = Player(screen_width, screen_height)
    all_sprites.add(player)

    create_aliens(all_sprites, aliens, screen_width)

    score = 0
    running = True
    game_over = False
    game_started = True  # auto start
    clock = pygame.time.Clock()

    # Auto fire timer
    AUTO_FIRE_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(AUTO_FIRE_EVENT, 300)  # fire every 300ms

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # press ESC to quit
                    running = False
                if event.key == pygame.K_r and game_over:
                    main()
                    return
            elif event.type == AUTO_FIRE_EVENT and not game_over:
                bullet = Bullet(player.rect.centerx, player.rect.top)
                all_sprites.add(bullet)
                bullets.add(bullet)

        if not game_over and game_started:
            all_sprites.update()

            # bullet-alien collisions
            hits = pygame.sprite.groupcollide(bullets, aliens, True, True)
            if hits:
                score += 10 * len(hits)

            # respawn wave
            if not aliens:
                create_aliens(all_sprites, aliens, screen_width)

            # game over check
            for alien in aliens:
                if alien.rect.bottom >= player.rect.top:
                    game_over = True

        # drawing
        screen.fill(DARK_GREEN)
        all_sprites.draw(screen)

        # Score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # Game over
        if game_over:
            game_over_text = font.render("GAME OVER", True, WHITE)
            screen.blit(game_over_text, (screen_width // 2 - 150, screen_height // 2 - 50))
            restart_text = font.render("Press 'R' to Restart", True, WHITE)
            screen.blit(restart_text, (screen_width // 2 - 200, screen_height // 2))

            all_sprites.empty()
            aliens.empty()
            bullets.empty()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
