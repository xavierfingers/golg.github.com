import pygame
import random
import os

# --- Game Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# --- Initialize Pygame ---
pygame.init()
pygame.mixer.init() # For sound

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()

# --- Asset Loading (Placeholders for now) ---
# You would typically load images here:
# player_img = pygame.image.load(os.path.join("assets", "player.png")).convert()
# enemy_img = pygame.image.load(os.path.join("assets", "enemy.png")).convert()
# bullet_img = pygame.image.load(os.path.join("assets", "bullet.png")).convert()

# --- Fonts ---
font_name = pygame.font.match_font('arial')

def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)

# --- Player Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Placeholder: A simple rectangle for the player
        self.image = pygame.Surface((50, 40))
        self.image.fill(BLUE)
        # If using an image:
        # self.image = player_img
        # self.image = pygame.transform.scale(self.image, (50, 40))
        # self.image.set_colorkey(BLACK) # Assuming black background for transparency

        self.rect = self.image.get_rect()
        self.radius = 20 # For circular collision detection
        # pygame.draw.circle(self.image, RED, self.rect.center, self.radius) # Uncomment to visualize radius

        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speedx = 0
        self.shield = 100
        self.shoot_delay = 250 # milliseconds
        self.last_shot = pygame.time.get_ticks()
        self.lives = 3
        self.hidden = False
        self.hide_timer = pygame.time.get_ticks()

    def update(self):
        # Unhide if hidden for too long
        if self.hidden and pygame.time.get_ticks() - self.hide_timer > 1000:
            self.hidden = False
            self.rect.centerx = SCREEN_WIDTH // 2
            self.rect.bottom = SCREEN_HEIGHT - 10

        self.speedx = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT]:
            self.speedx = -5
        if keystate[pygame.K_RIGHT]:
            self.speedx = 5
        self.rect.x += self.speedx

        # Keep player on screen
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay and not self.hidden:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)
            # shoot_sound.play() # Uncomment if you have a sound

    def hide(self):
        self.hidden = True
        self.hide_timer = pygame.time.get_ticks()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT + 200) # Move off-screen

# --- Enemy Class ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Placeholder: A simple rectangle for the enemy
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        # If using an image:
        # self.image = enemy_img
        # self.image = pygame.transform.scale(self.image, (30, 30))
        # self.image.set_colorkey(BLACK)

        self.rect = self.image.get_rect()
        self.radius = 15
        # pygame.draw.circle(self.image, BLUE, self.rect.center, self.radius)

        self.rect.x = random.randrange(SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedy = random.randrange(1, 8)
        self.speedx = random.randrange(-3, 3)

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy

        # If enemy goes off screen, reset its position
        if self.rect.top > SCREEN_HEIGHT + 10 or self.rect.left < -25 or self.rect.right > SCREEN_WIDTH + 20:
            self.rect.x = random.randrange(SCREEN_WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 8)
            self.speedx = random.randrange(-3, 3)

# --- Bullet Class ---
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Placeholder: A simple rectangle for the bullet
        self.image = pygame.Surface((5, 15))
        self.image.fill(YELLOW)
        # If using an image:
        # self.image = bullet_img
        # self.image = pygame.transform.scale(self.image, (5, 15))
        # self.image.set_colorkey(BLACK)

        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        # Kill if it moves off the top of the screen
        if self.rect.bottom < 0:
            self.kill()

# --- Game Over Screen ---
def show_go_screen():
    screen.fill(BLACK)
    draw_text(screen, "SPACE SHOOTER!", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
    draw_text(screen, "Arrow keys move, Space to fire", 22, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    draw_text(screen, "Press a key to begin", 18, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4)
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYUP:
                waiting = False

# --- Game Loop ---
game_over = True
running = True
while running:
    if game_over:
        show_go_screen()
        game_over = False
        all_sprites = pygame.sprite.Group()
        enemies = pygame.sprite.Group()
        bullets = pygame.sprite.Group()

        player = Player()
        all_sprites.add(player)
        for i in range(8): # Spawn initial enemies
            m = Enemy()
            all_sprites.add(m)
            enemies.add(m)

        score = 0

    # Keep loop running at the right speed
    clock.tick(FPS)

    # --- Process Input (Events) ---
    for event in pygame.event.get():
        # Check for closing window
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()

    # --- Update ---
    all_sprites.update()

    # Check for bullet-enemy collisions
    hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
    for hit in hits:
        score += 10
        m = Enemy() # Spawn a new enemy
        all_sprites.add(m)
        enemies.add(m)

    # Check for enemy-player collisions
    hits = pygame.sprite.spritecollide(player, enemies, True, pygame.sprite.collide_circle)
    for hit in hits:
        player.shield -= hit.radius * 2 # Reduce shield based on enemy size
        m = Enemy() # Spawn a new enemy
        all_sprites.add(m)
        enemies.add(m)
        if player.shield <= 0:
            player.lives -= 1
            player.shield = 100 # Reset shield for next life
            player.hide()

    # If player runs out of lives
    if player.lives == 0 and not player.hidden:
        game_over = True

    # --- Draw / Render ---
    screen.fill(BLACK) # Background
    all_sprites.draw(screen)
    draw_text(screen, f"Score: {score}", 18, SCREEN_WIDTH // 2, 10)
    draw_text(screen, f"Shield: {player.shield}", 18, 60, 10)
    draw_text(screen, f"Lives: {player.lives}", 18, SCREEN_WIDTH - 60, 10)

    # --- After drawing everything, flip the display ---
    pygame.display.flip()

pygame.quit()
