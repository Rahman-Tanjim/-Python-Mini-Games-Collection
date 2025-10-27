  # polished_pong.py
import pygame
import sys
import random
import math

# -------- CONFIG --------
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60

PADDLE_WIDTH = 12
PADDLE_HEIGHT = 110
PADDLE_MARGIN = 30

BALL_SIZE = 16

# Base speeds
PADDLE_SPEED = 8
BALL_SPEED = 5.0

# Speed increase factors
BALL_SPEEDUP = 1.06
BALL_MAX_SPEED = 14.0
PADDLE_MAX_SPEED = 14

WIN_SCORE = 7
SERVE_DELAY_MS = 900  # milliseconds before serve after a score

# Colors
WHITE = (255, 255, 255)
BLACK = (12, 12, 12)
CYAN = (0, 200, 220)
MAGENTA = (255, 80, 180)
GRAY = (90, 90, 90)

# ------------------------

class Paddle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, speed=PADDLE_SPEED):
        super().__init__()
        self.image = pygame.Surface((PADDLE_WIDTH, PADDLE_HEIGHT))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed

    def move_up(self):
        self.rect.y -= self.speed
        if self.rect.top < 0:
            self.rect.top = 0

    def move_down(self):
        self.rect.y += self.speed
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def update_speed(self, new_speed):
        self.speed = max(1, min(PADDLE_MAX_SPEED, new_speed))

class Ball(pygame.sprite.Sprite):
    def __init__(self, color):
        super().__init__()
        self.image = pygame.Surface((BALL_SIZE, BALL_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (BALL_SIZE // 2, BALL_SIZE // 2), BALL_SIZE // 2)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        self.speed = BALL_SPEED
        angle = random.uniform(-0.25 * math.pi, 0.25 * math.pi)
        self.vx = self.speed * math.copysign(math.cos(angle), random.choice([-1, 1]))
        self.vy = self.speed * math.sin(angle)

    def reset(self, direction=1, speed=None):
        """Reset to center. direction: +1 ball to right, -1 to left, 0 random"""
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed = speed if speed is not None else BALL_SPEED
        angle = random.uniform(-0.25 * math.pi, 0.25 * math.pi)
        if direction == 0:
            sign = random.choice([-1, 1])
        else:
            sign = 1 if direction > 0 else -1
        self.vx = sign * self.speed * math.cos(angle)
        self.vy = self.speed * math.sin(angle)

    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

        # Bounce off top/bottom
        if self.rect.top <= 0:
            self.rect.top = 0
            self.vy = -self.vy
        elif self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.vy = -self.vy

    def apply_speed(self, new_speed):
        """Scale vx, vy to match new_speed while preserving direction."""
        angle = math.atan2(self.vy, self.vx)
        self.vx = new_speed * math.cos(angle)
        self.vy = new_speed * math.sin(angle)
        self.speed = new_speed

# Helpers
def clamp(n, a, b):
    return max(a, min(b, n))

def paddle_hit_ball(ball, paddle):
    """
    Adjust ball velocity depending where on the paddle it hit.
    Returns True if handled (i.e., collision).
    """
    if not ball.rect.colliderect(paddle.rect):
        return False

    # Determine collision side: left paddle or right paddle
    # Move ball out slightly to avoid repeated collisions
    if ball.vx < 0:  # ball moving left => probably hit left paddle
        ball.rect.left = paddle.rect.right
    else:
        ball.rect.right = paddle.rect.left

    # Relative hit position: -1 (top) ... 0 (middle) ... +1 (bottom)
    rel_y = (ball.rect.centery - paddle.rect.centery) / (paddle.rect.height / 2)
    rel_y = clamp(rel_y, -1, 1)

    # Max bounce angle (radians)
    max_angle = 3 * math.pi / 8  # ~67.5 degrees
    angle = rel_y * max_angle

    # New speed increases slightly
    new_speed = clamp(ball.speed * BALL_SPEEDUP, 3.0, BALL_MAX_SPEED)

    # Horizontal direction flips
    dir_sign = -1 if ball.vx < 0 else 1
    # We want ball to go opposite direction relative to incoming (flip)
    dir_sign *= -1

    ball.vx = dir_sign * new_speed * math.cos(angle)
    ball.vy = new_speed * math.sin(angle)
    ball.speed = new_speed

    return True

# AI logic
class SimpleAI:
    def __init__(self, paddle, difficulty='normal'):
        self.paddle = paddle
        self.set_difficulty(difficulty)
        self.reaction_timer = 0

    def set_difficulty(self, difficulty):
        diff = difficulty.lower()
        if diff == 'easy':
            self.paddle.update_speed(6)
            self.react_ms = 200
            self.prediction_strength = 0.45
        elif diff == 'hard':
            self.paddle.update_speed(12)
            self.react_ms = 40
            self.prediction_strength = 0.98
        else:  # normal
            self.paddle.update_speed(8)
            self.react_ms = 110
            self.prediction_strength = 0.75

    def update(self, ball, dt_ms):
        # reaction: only move after a small delay to simulate imperfection
        self.reaction_timer += dt_ms
        if self.reaction_timer < self.react_ms:
            return
        self.reaction_timer = 0

        # Predict ball vertical position roughly
        predicted_y = ball.rect.centery + (ball.vy * (abs(ball.rect.centerx - self.paddle.rect.centerx) / max(1, abs(ball.vx))))
        target = ball.rect.centery * (1 - self.prediction_strength) + predicted_y * self.prediction_strength
        if target < self.paddle.rect.centery - 6:
            self.paddle.move_up()
        elif target > self.paddle.rect.centery + 6:
            self.paddle.move_down()

# UI / Game states
def draw_centered_text(screen, text, font, color, y):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
    screen.blit(surf, rect)

def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Polished Pong")
    clock = pygame.time.Clock()

    # Fonts
    title_font = pygame.font.Font(None, 72)
    menu_font = pygame.font.Font(None, 36)
    hud_font = pygame.font.Font(None, 28)
    big_font = pygame.font.Font(None, 56)

    # Load sounds if available
    bounce_sound = "pinpong.wav"
    score_sound = "pinpong.wav"
    try:
        bounce_sound = pygame.mixer.Sound("pinpong.wav")
        score_sound = pygame.mixer.Sound("pinpong.wav")
    except Exception:
        # No problem; sound optional
        bounce_sound = None
        score_sound = None

    # Game variables
    running = True
    in_menu = True

    # Menu selections
    selected_mode = 1  # 1: 1-player, 2: 2-player
    difficulty = 'Normal'
    win_score = WIN_SCORE

    while running:
        # ---------- MENU ----------
        while in_menu:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif ev.key == pygame.K_1:
                        selected_mode = 1
                    elif ev.key == pygame.K_2:
                        selected_mode = 2
                    elif ev.key == pygame.K_UP:
                        # toggle difficulty up
                        if difficulty == 'Easy':
                            difficulty = 'Normal'
                        elif difficulty == 'Normal':
                            difficulty = 'Hard'
                    elif ev.key == pygame.K_DOWN:
                        if difficulty == 'Hard':
                            difficulty = 'Normal'
                        elif difficulty == 'Normal':
                            difficulty = 'Easy'
                    elif ev.key == pygame.K_LEFT:
                        win_score = max(1, win_score - 1)
                    elif ev.key == pygame.K_RIGHT:
                        win_score = min(15, win_score + 1)
                    elif ev.key == pygame.K_SPACE:
                        in_menu = False
                    elif ev.key == pygame.K_RETURN:
                        in_menu = False

            screen.fill(BLACK)
            draw_centered_text(screen, "POLISHED PONG", title_font, WHITE, SCREEN_HEIGHT * 0.18)
            draw_centered_text(screen, "Press 1 for Single Player  •  2 for Two Player", menu_font, GRAY, SCREEN_HEIGHT * 0.34)
            draw_centered_text(screen, f"Mode: {'1-Player (AI)' if selected_mode == 1 else '2-Player'}", menu_font, CYAN, SCREEN_HEIGHT * 0.44)
            draw_centered_text(screen, f"Difficulty (UP/DOWN): {difficulty}", menu_font, MAGENTA, SCREEN_HEIGHT * 0.52)
            draw_centered_text(screen, f"Win Score (LEFT/RIGHT): {win_score}", menu_font, WHITE, SCREEN_HEIGHT * 0.60)
            draw_centered_text(screen, "P: Pause during game • R: Restart • ESC: Quit", hud_font, GRAY, SCREEN_HEIGHT * 0.72)
            draw_centered_text(screen, "Press SPACE or Enter to Start", menu_font, WHITE, SCREEN_HEIGHT * 0.85)

            # small legend on controls
            left_ctrl = menu_font.render("Player 1: W / S", True, CYAN)
            right_ctrl = menu_font.render("Player 2: Up / Down", True, MAGENTA)
            screen.blit(left_ctrl, (40, SCREEN_HEIGHT - 60))
            screen.blit(right_ctrl, (SCREEN_WIDTH - right_ctrl.get_width() - 40, SCREEN_HEIGHT - 60))

            pygame.display.flip()
            clock.tick(FPS)

        # ---------- SETUP GAME ----------
        # paddles
        paddle1 = Paddle(PADDLE_MARGIN, SCREEN_HEIGHT // 2, CYAN)
        paddle2 = Paddle(SCREEN_WIDTH - PADDLE_MARGIN, SCREEN_HEIGHT // 2, MAGENTA)

        # AI (if 1-player)
        ai = None
        if selected_mode == 1:
            ai = SimpleAI(paddle2, difficulty=difficulty)

        # ball & groups
        ball = Ball(WHITE)
        all_sprites = pygame.sprite.Group(paddle1, paddle2, ball)

        score1 = 0
        score2 = 0
        paused = False
        winner = None

        # Serve control
        next_serve_time = pygame.time.get_ticks() + SERVE_DELAY_MS
        pending_serve_dir = random.choice([-1, 1])  # who the ball goes to on serve

        # main game loop
        last_time = pygame.time.get_ticks()
        while True:
            dt_ms = clock.tick(FPS)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if ev.key == pygame.K_p:
                        paused = not paused
                    if ev.key == pygame.K_r:
                        # restart to menu
                        in_menu = True
                        break

            if in_menu:
                break  # exit to main menu loop to restart

            if paused:
                # Draw pause overlay
                screen.fill(BLACK)
                all_sprites.draw(screen)
                score1_text = big_font.render(str(score1), True, CYAN)
                score2_text = big_font.render(str(score2), True, MAGENTA)
                screen.blit(score1_text, (SCREEN_WIDTH // 4 - score1_text.get_width() // 2, 20))
                screen.blit(score2_text, (SCREEN_WIDTH * 3 // 4 - score2_text.get_width() // 2, 20))
                draw_centered_text(screen, "PAUSED - Press P to resume", menu_font, WHITE, SCREEN_HEIGHT // 2)
                pygame.display.flip()
                continue

            # Controls
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                paddle1.move_up()
            if keys[pygame.K_s]:
                paddle1.move_down()
            if selected_mode == 2:
                if keys[pygame.K_UP]:
                    paddle2.move_up()
                if keys[pygame.K_DOWN]:
                    paddle2.move_down()

            # AI update
            if ai and not paused:
                ai.update(ball, dt_ms)

            # Serve logic: only move ball after serve delay
            now = pygame.time.get_ticks()
            if now < next_serve_time:
                # show a "Get Ready" small overlay and don't move ball
                # center ball and show countdown
                ball.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                screen.fill(BLACK)
                # draw paddles and center line
                pygame.draw.line(screen, GRAY, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 2)
                all_sprites.draw(screen)
                # countdown
                remain = max(0, (next_serve_time - now) // 1000 + 1)
                draw_centered_text(screen, f"Serve in {remain}", menu_font, WHITE, SCREEN_HEIGHT * 0.45)
                score1_text = big_font.render(str(score1), True, CYAN)
                score2_text = big_font.render(str(score2), True, MAGENTA)
                screen.blit(score1_text, (SCREEN_WIDTH // 4 - score1_text.get_width() // 2, 20))
                screen.blit(score2_text, (SCREEN_WIDTH * 3 // 4 - score2_text.get_width() // 2, 20))
                pygame.display.flip()
                continue  # skip physics until serve time

            # If serve time passed and ball not moving (vx ~ 0), ensure ball is launched
            if abs(ball.vx) < 0.001 and abs(ball.vy) < 0.001:
                ball.reset(direction=pending_serve_dir)

            # Update sprites
            all_sprites.update()

            # Collisions: paddles
            if paddle_hit_ball(ball, paddle1) or paddle_hit_ball(ball, paddle2):
                if bounce_sound:
                    try:
                        bounce_sound.play()
                    except Exception:
                        pass

            # Score check
            scored = False
            if ball.rect.left <= 0:
                score2 += 1
                scored = True
                pending_serve_dir = -1  # send to left (loser side)
            elif ball.rect.right >= SCREEN_WIDTH:
                score1 += 1
                scored = True
                pending_serve_dir = 1

            if scored:
                if score_sound:
                    try:
                        score_sound.play()
                    except Exception:
                        pass
                # check win
                if score1 >= win_score:
                    winner = "PLAYER 1" if selected_mode == 2 or selected_mode == 1 else "PLAYER 1"
                elif score2 >= win_score:
                    winner = "PLAYER 2" if selected_mode == 2 else "COMPUTER"
                # reset ball & pause before serve
                ball.vx = 0
                ball.vy = 0
                ball.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                next_serve_time = pygame.time.get_ticks() + SERVE_DELAY_MS
                # small randomize direction next serve
                pending_serve_dir = random.choice([-1, 1])
                if winner:
                    # show game over screen
                    screen.fill(BLACK)
                    draw_centered_text(screen, f"{winner} WINS!", title_font, WHITE, SCREEN_HEIGHT * 0.35)
                    draw_centered_text(screen, f"Final Score: {score1} - {score2}", menu_font, GRAY, SCREEN_HEIGHT * 0.50)
                    draw_centered_text(screen, "Press R to return to menu or SPACE to play again", hud_font, WHITE, SCREEN_HEIGHT * 0.68)
                    pygame.display.flip()

                    # Wait for user decision
                    waiting = True
                    while waiting:
                        for ev in pygame.event.get():
                            if ev.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            if ev.type == pygame.KEYDOWN:
                                if ev.key == pygame.K_r:
                                    in_menu = True
                                    waiting = False
                                    break
                                if ev.key == pygame.K_SPACE:
                                    # reset everything for new match but keep mode/difficulty
                                    score1 = 0
                                    score2 = 0
                                    paddle1.rect.centery = SCREEN_HEIGHT // 2
                                    paddle2.rect.centery = SCREEN_HEIGHT // 2
                                    ball.reset(direction=random.choice([-1, 1]), speed=BALL_SPEED)
                                    winner = None
                                    next_serve_time = pygame.time.get_ticks() + SERVE_DELAY_MS
                                    waiting = False
                                    break
                                if ev.key == pygame.K_ESCAPE:
                                    pygame.quit()
                                    sys.exit()
                        clock.tick(FPS)
                    if in_menu:
                        break  # go back to menu
                    else:
                        continue  # continue playing new match

            # Draw
            screen.fill(BLACK)
            # center dashed line
            for y in range(0, SCREEN_HEIGHT, 22):
                pygame.draw.rect(screen, GRAY, (SCREEN_WIDTH // 2 - 1, y + 6, 2, 12))
            all_sprites.draw(screen)

            # Scores
            score1_text = big_font.render(str(score1), True, CYAN)
            score2_text = big_font.render(str(score2), True, MAGENTA)
            screen.blit(score1_text, (SCREEN_WIDTH // 4 - score1_text.get_width() // 2, 18))
            screen.blit(score2_text, (SCREEN_WIDTH * 3 // 4 - score2_text.get_width() // 2, 18))

            # Small HUD
            mode_text = "1P (AI)" if selected_mode == 1 else "2P"
            hud = hud_font.render(f"Mode: {mode_text} • Difficulty: {difficulty} • First to {win_score}", True, WHITE)
            screen.blit(hud, (20, SCREEN_HEIGHT - 34))

            pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
# polished_pong.py
import pygame
import sys
import random
import math

# -------- CONFIG --------
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60

PADDLE_WIDTH = 12
PADDLE_HEIGHT = 110
PADDLE_MARGIN = 30

BALL_SIZE = 16

# Base speeds
PADDLE_SPEED = 8
BALL_SPEED = 5.0

# Speed increase factors
BALL_SPEEDUP = 1.06
BALL_MAX_SPEED = 14.0
PADDLE_MAX_SPEED = 14

WIN_SCORE = 7
SERVE_DELAY_MS = 900  # milliseconds before serve after a score

# Colors
WHITE = (255, 255, 255)
BLACK = (12, 12, 12)
CYAN = (0, 200, 220)
MAGENTA = (255, 80, 180)
GRAY = (90, 90, 90)

# ------------------------

class Paddle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, speed=PADDLE_SPEED):
        super().__init__()
        self.image = pygame.Surface((PADDLE_WIDTH, PADDLE_HEIGHT))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed

    def move_up(self):
        self.rect.y -= self.speed
        if self.rect.top < 0:
            self.rect.top = 0

    def move_down(self):
        self.rect.y += self.speed
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def update_speed(self, new_speed):
        self.speed = max(1, min(PADDLE_MAX_SPEED, new_speed))

class Ball(pygame.sprite.Sprite):
    def __init__(self, color):
        super().__init__()
        self.image = pygame.Surface((BALL_SIZE, BALL_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (BALL_SIZE // 2, BALL_SIZE // 2), BALL_SIZE // 2)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        self.speed = BALL_SPEED
        angle = random.uniform(-0.25 * math.pi, 0.25 * math.pi)
        self.vx = self.speed * math.copysign(math.cos(angle), random.choice([-1, 1]))
        self.vy = self.speed * math.sin(angle)

    def reset(self, direction=1, speed=None):
        """Reset to center. direction: +1 ball to right, -1 to left, 0 random"""
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed = speed if speed is not None else BALL_SPEED
        angle = random.uniform(-0.25 * math.pi, 0.25 * math.pi)
        if direction == 0:
            sign = random.choice([-1, 1])
        else:
            sign = 1 if direction > 0 else -1
        self.vx = sign * self.speed * math.cos(angle)
        self.vy = self.speed * math.sin(angle)

    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

        # Bounce off top/bottom
        if self.rect.top <= 0:
            self.rect.top = 0
            self.vy = -self.vy
        elif self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.vy = -self.vy

    def apply_speed(self, new_speed):
        """Scale vx, vy to match new_speed while preserving direction."""
        angle = math.atan2(self.vy, self.vx)
        self.vx = new_speed * math.cos(angle)
        self.vy = new_speed * math.sin(angle)
        self.speed = new_speed

# Helpers
def clamp(n, a, b):
    return max(a, min(b, n))

def paddle_hit_ball(ball, paddle):
    """
    Adjust ball velocity depending where on the paddle it hit.
    Returns True if handled (i.e., collision).
    """
    if not ball.rect.colliderect(paddle.rect):
        return False

    # Determine collision side: left paddle or right paddle
    # Move ball out slightly to avoid repeated collisions
    if ball.vx < 0:  # ball moving left => probably hit left paddle
        ball.rect.left = paddle.rect.right
    else:
        ball.rect.right = paddle.rect.left

    # Relative hit position: -1 (top) ... 0 (middle) ... +1 (bottom)
    rel_y = (ball.rect.centery - paddle.rect.centery) / (paddle.rect.height / 2)
    rel_y = clamp(rel_y, -1, 1)

    # Max bounce angle (radians)
    max_angle = 3 * math.pi / 8  # ~67.5 degrees
    angle = rel_y * max_angle

    # New speed increases slightly
    new_speed = clamp(ball.speed * BALL_SPEEDUP, 3.0, BALL_MAX_SPEED)

    # Horizontal direction flips
    dir_sign = -1 if ball.vx < 0 else 1
    # We want ball to go opposite direction relative to incoming (flip)
    dir_sign *= -1

    ball.vx = dir_sign * new_speed * math.cos(angle)
    ball.vy = new_speed * math.sin(angle)
    ball.speed = new_speed

    return True

# AI logic
class SimpleAI:
    def __init__(self, paddle, difficulty='normal'):
        self.paddle = paddle
        self.set_difficulty(difficulty)
        self.reaction_timer = 0

    def set_difficulty(self, difficulty):
        diff = difficulty.lower()
        if diff == 'easy':
            self.paddle.update_speed(6)
            self.react_ms = 200
            self.prediction_strength = 0.45
        elif diff == 'hard':
            self.paddle.update_speed(12)
            self.react_ms = 40
            self.prediction_strength = 0.98
        else:  # normal
            self.paddle.update_speed(8)
            self.react_ms = 110
            self.prediction_strength = 0.75

    def update(self, ball, dt_ms):
        # reaction: only move after a small delay to simulate imperfection
        self.reaction_timer += dt_ms
        if self.reaction_timer < self.react_ms:
            return
        self.reaction_timer = 0

        # Predict ball vertical position roughly
        predicted_y = ball.rect.centery + (ball.vy * (abs(ball.rect.centerx - self.paddle.rect.centerx) / max(1, abs(ball.vx))))
        target = ball.rect.centery * (1 - self.prediction_strength) + predicted_y * self.prediction_strength
        if target < self.paddle.rect.centery - 6:
            self.paddle.move_up()
        elif target > self.paddle.rect.centery + 6:
            self.paddle.move_down()

# UI / Game states
def draw_centered_text(screen, text, font, color, y):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
    screen.blit(surf, rect)

def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Polished Pong")
    clock = pygame.time.Clock()

    # Fonts
    title_font = pygame.font.Font(None, 72)
    menu_font = pygame.font.Font(None, 36)
    hud_font = pygame.font.Font(None, 28)
    big_font = pygame.font.Font(None, 56)

    # Load sounds if available
    bounce_sound = "sounds/pinpong.wav"
    score_sound = "sounds/pinpong.wav"
    try:
        bounce_sound = pygame.mixer.Sound("pinpong.wav")
        score_sound = pygame.mixer.Sound("pinpong.wav")
    except Exception:
        # No problem; sound optional
        bounce_sound = None
        score_sound = None

    # Game variables
    running = True
    in_menu = True

    # Menu selections
    selected_mode = 1  # 1: 1-player, 2: 2-player
    difficulty = 'Normal'
    win_score = WIN_SCORE

    while running:
        # ---------- MENU ----------
        while in_menu:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif ev.key == pygame.K_1:
                        selected_mode = 1
                    elif ev.key == pygame.K_2:
                        selected_mode = 2
                    elif ev.key == pygame.K_UP:
                        # toggle difficulty up
                        if difficulty == 'Easy':
                            difficulty = 'Normal'
                        elif difficulty == 'Normal':
                            difficulty = 'Hard'
                    elif ev.key == pygame.K_DOWN:
                        if difficulty == 'Hard':
                            difficulty = 'Normal'
                        elif difficulty == 'Normal':
                            difficulty = 'Easy'
                    elif ev.key == pygame.K_LEFT:
                        win_score = max(1, win_score - 1)
                    elif ev.key == pygame.K_RIGHT:
                        win_score = min(15, win_score + 1)
                    elif ev.key == pygame.K_SPACE:
                        in_menu = False
                    elif ev.key == pygame.K_RETURN:
                        in_menu = False

            screen.fill(BLACK)
            draw_centered_text(screen, "POLISHED PONG", title_font, WHITE, SCREEN_HEIGHT * 0.18)
            draw_centered_text(screen, "Press 1 for Single Player  •  2 for Two Player", menu_font, GRAY, SCREEN_HEIGHT * 0.34)
            draw_centered_text(screen, f"Mode: {'1-Player (AI)' if selected_mode == 1 else '2-Player'}", menu_font, CYAN, SCREEN_HEIGHT * 0.44)
            draw_centered_text(screen, f"Difficulty (UP/DOWN): {difficulty}", menu_font, MAGENTA, SCREEN_HEIGHT * 0.52)
            draw_centered_text(screen, f"Win Score (LEFT/RIGHT): {win_score}", menu_font, WHITE, SCREEN_HEIGHT * 0.60)
            draw_centered_text(screen, "P: Pause during game • R: Restart • ESC: Quit", hud_font, GRAY, SCREEN_HEIGHT * 0.72)
            draw_centered_text(screen, "Press SPACE or Enter to Start", menu_font, WHITE, SCREEN_HEIGHT * 0.85)

            # small legend on controls
            left_ctrl = menu_font.render("Player 1: W / S", True, CYAN)
            right_ctrl = menu_font.render("Player 2: Up / Down", True, MAGENTA)
            screen.blit(left_ctrl, (40, SCREEN_HEIGHT - 60))
            screen.blit(right_ctrl, (SCREEN_WIDTH - right_ctrl.get_width() - 40, SCREEN_HEIGHT - 60))

            pygame.display.flip()
            clock.tick(FPS)

        # ---------- SETUP GAME ----------
        # paddles
        paddle1 = Paddle(PADDLE_MARGIN, SCREEN_HEIGHT // 2, CYAN)
        paddle2 = Paddle(SCREEN_WIDTH - PADDLE_MARGIN, SCREEN_HEIGHT // 2, MAGENTA)

        # AI (if 1-player)
        ai = None
        if selected_mode == 1:
            ai = SimpleAI(paddle2, difficulty=difficulty)

        # ball & groups
        ball = Ball(WHITE)
        all_sprites = pygame.sprite.Group(paddle1, paddle2, ball)

        score1 = 0
        score2 = 0
        paused = False
        winner = None

        # Serve control
        next_serve_time = pygame.time.get_ticks() + SERVE_DELAY_MS
        pending_serve_dir = random.choice([-1, 1])  # who the ball goes to on serve

        # main game loop
        last_time = pygame.time.get_ticks()
        while True:
            dt_ms = clock.tick(FPS)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if ev.key == pygame.K_p:
                        paused = not paused
                    if ev.key == pygame.K_r:
                        # restart to menu
                        in_menu = True
                        break

            if in_menu:
                break  # exit to main menu loop to restart

            if paused:
                # Draw pause overlay
                screen.fill(BLACK)
                all_sprites.draw(screen)
                score1_text = big_font.render(str(score1), True, CYAN)
                score2_text = big_font.render(str(score2), True, MAGENTA)
                screen.blit(score1_text, (SCREEN_WIDTH // 4 - score1_text.get_width() // 2, 20))
                screen.blit(score2_text, (SCREEN_WIDTH * 3 // 4 - score2_text.get_width() // 2, 20))
                draw_centered_text(screen, "PAUSED - Press P to resume", menu_font, WHITE, SCREEN_HEIGHT // 2)
                pygame.display.flip()
                continue

            # Controls
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                paddle1.move_up()
            if keys[pygame.K_s]:
                paddle1.move_down()
            if selected_mode == 2:
                if keys[pygame.K_UP]:
                    paddle2.move_up()
                if keys[pygame.K_DOWN]:
                    paddle2.move_down()

            # AI update
            if ai and not paused:
                ai.update(ball, dt_ms)

            # Serve logic: only move ball after serve delay
            now = pygame.time.get_ticks()
            if now < next_serve_time:
                # show a "Get Ready" small overlay and don't move ball
                # center ball and show countdown
                ball.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                screen.fill(BLACK)
                # draw paddles and center line
                pygame.draw.line(screen, GRAY, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 2)
                all_sprites.draw(screen)
                # countdown
                remain = max(0, (next_serve_time - now) // 1000 + 1)
                draw_centered_text(screen, f"Serve in {remain}", menu_font, WHITE, SCREEN_HEIGHT * 0.45)
                score1_text = big_font.render(str(score1), True, CYAN)
                score2_text = big_font.render(str(score2), True, MAGENTA)
                screen.blit(score1_text, (SCREEN_WIDTH // 4 - score1_text.get_width() // 2, 20))
                screen.blit(score2_text, (SCREEN_WIDTH * 3 // 4 - score2_text.get_width() // 2, 20))
                pygame.display.flip()
                continue  # skip physics until serve time

            # If serve time passed and ball not moving (vx ~ 0), ensure ball is launched
            if abs(ball.vx) < 0.001 and abs(ball.vy) < 0.001:
                ball.reset(direction=pending_serve_dir)

            # Update sprites
            all_sprites.update()

            # Collisions: paddles
            if paddle_hit_ball(ball, paddle1) or paddle_hit_ball(ball, paddle2):
                if bounce_sound:
                    try:
                        bounce_sound.play()
                    except Exception:
                        pass

            # Score check
            scored = False
            if ball.rect.left <= 0:
                score2 += 1
                scored = True
                pending_serve_dir = -1  # send to left (loser side)
            elif ball.rect.right >= SCREEN_WIDTH:
                score1 += 1
                scored = True
                pending_serve_dir = 1

            if scored:
                if score_sound:
                    try:
                        score_sound.play()
                    except Exception:
                        pass
                # check win
                if score1 >= win_score:
                    winner = "PLAYER 1" if selected_mode == 2 or selected_mode == 1 else "PLAYER 1"
                elif score2 >= win_score:
                    winner = "PLAYER 2" if selected_mode == 2 else "COMPUTER"
                # reset ball & pause before serve
                ball.vx = 0
                ball.vy = 0
                ball.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                next_serve_time = pygame.time.get_ticks() + SERVE_DELAY_MS
                # small randomize direction next serve
                pending_serve_dir = random.choice([-1, 1])
                if winner:
                    # show game over screen
                    screen.fill(BLACK)
                    draw_centered_text(screen, f"{winner} WINS!", title_font, WHITE, SCREEN_HEIGHT * 0.35)
                    draw_centered_text(screen, f"Final Score: {score1} - {score2}", menu_font, GRAY, SCREEN_HEIGHT * 0.50)
                    draw_centered_text(screen, "Press R to return to menu or SPACE to play again", hud_font, WHITE, SCREEN_HEIGHT * 0.68)
                    pygame.display.flip()

                    # Wait for user decision
                    waiting = True
                    while waiting:
                        for ev in pygame.event.get():
                            if ev.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            if ev.type == pygame.KEYDOWN:
                                if ev.key == pygame.K_r:
                                    in_menu = True
                                    waiting = False
                                    break
                                if ev.key == pygame.K_SPACE:
                                    # reset everything for new match but keep mode/difficulty
                                    score1 = 0
                                    score2 = 0
                                    paddle1.rect.centery = SCREEN_HEIGHT // 2
                                    paddle2.rect.centery = SCREEN_HEIGHT // 2
                                    ball.reset(direction=random.choice([-1, 1]), speed=BALL_SPEED)
                                    winner = None
                                    next_serve_time = pygame.time.get_ticks() + SERVE_DELAY_MS
                                    waiting = False
                                    break
                                if ev.key == pygame.K_ESCAPE:
                                    pygame.quit()
                                    sys.exit()
                        clock.tick(FPS)
                    if in_menu:
                        break  # go back to menu
                    else:
                        continue  # continue playing new match

            # Draw
            screen.fill(BLACK)
            # center dashed line
            for y in range(0, SCREEN_HEIGHT, 22):
                pygame.draw.rect(screen, GRAY, (SCREEN_WIDTH // 2 - 1, y + 6, 2, 12))
            all_sprites.draw(screen)

            # Scores
            score1_text = big_font.render(str(score1), True, CYAN)
            score2_text = big_font.render(str(score2), True, MAGENTA)
            screen.blit(score1_text, (SCREEN_WIDTH // 4 - score1_text.get_width() // 2, 18))
            screen.blit(score2_text, (SCREEN_WIDTH * 3 // 4 - score2_text.get_width() // 2, 18))

            # Small HUD
            mode_text = "1P (AI)" if selected_mode == 1 else "2P"
            hud = hud_font.render(f"Mode: {mode_text} • Difficulty: {difficulty} • First to {win_score}", True, WHITE)
            screen.blit(hud, (20, SCREEN_HEIGHT - 34))

            pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
# Write your code here :-)
