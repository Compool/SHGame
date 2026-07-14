import pygame
import random
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

pygame.init()

SCREEN_W, SCREEN_H = 800, 600
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Shooting Game")
clock = pygame.time.Clock()

bg_img = pygame.image.load("background.png").convert()
player_img = pygame.image.load("p.png").convert_alpha()
missile_img = pygame.image.load("m.png").convert_alpha()
enemy_imgs = [pygame.image.load(f"e{i}.png").convert_alpha() for i in range(1, 7)]
bonus_imgs = [pygame.image.load("bonus1.png").convert_alpha(),
              pygame.image.load("bonus2.png").convert_alpha()]

font = pygame.font.SysFont("malgungothic", 36)
big_font = pygame.font.SysFont("malgungothic", 72)

PLAYER_SPEED = 5
MISSILE_SPEED = 10
ENEMY_BASE_SPEED = 2
ENEMY_SPAWN_INTERVAL = 60
BONUS_SPAWN_INTERVAL = 300


class Player:
    def __init__(self):
        self.img = player_img
        self.rect = self.img.get_rect(center=(SCREEN_W // 2, SCREEN_H - 80))
        self.hp = 3
        self.score = 0
        self.fire_cooldown = 0

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += PLAYER_SPEED

        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_W, SCREEN_H))

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def fire(self):
        if self.fire_cooldown <= 0:
            self.fire_cooldown = 10
            return Missile(self.rect.centerx, self.rect.top)
        return None

    def draw(self, surface):
        surface.blit(self.img, self.rect)


class Missile:
    def __init__(self, x, y):
        self.img = missile_img
        self.rect = self.img.get_rect(center=(x, y))

    def update(self):
        self.rect.y -= MISSILE_SPEED

    def is_off_screen(self):
        return self.rect.bottom < 0

    def draw(self, surface):
        surface.blit(self.img, self.rect)


class Enemy:
    def __init__(self, level):
        idx = random.randint(0, len(enemy_imgs) - 1)
        self.img = enemy_imgs[idx]
        self.rect = self.img.get_rect()
        self.rect.x = random.randint(0, SCREEN_W - self.rect.w)
        self.rect.y = random.randint(-100, -40)
        speed = ENEMY_BASE_SPEED + level * 0.3 + random.random()
        self.speed = min(speed, 7)
        self.hp = 1
        self.angle = random.choice([-1, 1])
        self.move_timer = 0
        self.score_value = (6 - idx) * 10 + 10

    def update(self):
        self.rect.y += self.speed
        self.move_timer += 1
        if self.move_timer % 30 == 0:
            self.angle *= -1
        self.rect.x += self.angle * (1 + random.random())

        if self.rect.left < 0:
            self.rect.left = 0
            self.angle = 1
        if self.rect.right > SCREEN_W:
            self.rect.right = SCREEN_W
            self.angle = -1

    def is_off_screen(self):
        return self.rect.top > SCREEN_H

    def draw(self, surface):
        surface.blit(self.img, self.rect)


class Bonus:
    def __init__(self):
        self.img = bonus_imgs[random.randint(0, len(bonus_imgs) - 1)]
        self.rect = self.img.get_rect()
        self.rect.x = random.randint(0, SCREEN_W - self.rect.w)
        self.rect.y = -self.rect.h
        self.speed = 2
        self.kind = random.randint(0, 1)

    def update(self):
        self.rect.y += self.speed

    def is_off_screen(self):
        return self.rect.top > SCREEN_H

    def apply(self, player):
        if self.kind == 0:
            player.score += 50
        else:
            player.hp = min(player.hp + 1, 5)

    def draw(self, surface):
        surface.blit(self.img, self.rect)


class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.max_radius = 25
        self.timer = 0

    def update(self):
        self.timer += 1
        self.radius = min(self.radius + 3, self.max_radius)

    def is_done(self):
        return self.timer >= 10

    def draw(self, surface):
        alpha = max(0, 255 - self.timer * 30)
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 150, 0, alpha), (self.radius, self.radius), self.radius)
        pygame.draw.circle(s, (255, 255, 0, alpha), (self.radius, self.radius), self.radius // 2)
        surface.blit(s, (self.x - self.radius, self.y - self.radius))


def draw_hp(surface, hp):
    for i in range(hp):
        pygame.draw.rect(surface, (255, 50, 50), (10 + i * 35, 10, 30, 20))
        pygame.draw.rect(surface, (200, 200, 200), (10 + i * 35, 10, 30, 20), 2)


def draw_score(surface, score):
    text = font.render(f"Score: {score}", True, (255, 255, 255))
    surface.blit(text, (SCREEN_W - text.get_width() - 10, 10))


def game_loop():
    player = Player()
    missiles = []
    enemies = []
    bonuses = []
    explosions = []
    bg_y = 0
    frame = 0
    level = 1

    while True:
        frame += 1
        if frame % 3600 == 0:
            level += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        keys = pygame.key.get_pressed()
        player.update(keys)

        if keys[pygame.K_SPACE]:
            m = player.fire()
            if m:
                missiles.append(m)

        if frame % max(20, ENEMY_SPAWN_INTERVAL - level * 5) == 0:
            enemies.append(Enemy(level))

        if frame % BONUS_SPAWN_INTERVAL == 0:
            bonuses.append(Bonus())

        for m in missiles:
            m.update()
        missiles = [m for m in missiles if not m.is_off_screen()]

        for e in enemies:
            e.update()
        enemies = [e for e in enemies if not e.is_off_screen()]

        for b in bonuses:
            b.update()
        bonuses = [b for b in bonuses if not b.is_off_screen()]

        for exp in explosions:
            exp.update()
        explosions = [e for e in explosions if not e.is_done()]

        for m in missiles[:]:
            for e in enemies[:]:
                if m.rect.colliderect(e.rect):
                    missiles.remove(m)
                    enemies.remove(e)
                    explosions.append(Explosion(e.rect.centerx, e.rect.centery))
                    player.score += e.score_value
                    break

        for e in enemies[:]:
            if player.rect.colliderect(e.rect):
                enemies.remove(e)
                explosions.append(Explosion(e.rect.centerx, e.rect.centery))
                player.hp -= 1
                if player.hp <= 0:
                    return player.score

        for b in bonuses[:]:
            if player.rect.colliderect(b.rect):
                bonuses.remove(b)
                b.apply(player)

        bg_y = (bg_y + 1) % SCREEN_H
        screen.blit(bg_img, (0, -bg_y))
        screen.blit(bg_img, (0, -bg_y + SCREEN_H))

        for m in missiles:
            m.draw(screen)
        for e in enemies:
            e.draw(screen)
        for b in bonuses:
            b.draw(screen)
        for exp in explosions:
            exp.draw(screen)
        player.draw(screen)

        draw_hp(screen, player.hp)
        draw_score(screen, player.score)

        lv_text = font.render(f"Level {level}", True, (200, 200, 200))
        screen.blit(lv_text, (SCREEN_W // 2 - lv_text.get_width() // 2, 10))

        pygame.display.flip()
        clock.tick(60)


def game_over_screen(score):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return True
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return False

        screen.blit(bg_img, (0, 0))
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        go_text = big_font.render("GAME OVER", True, (255, 50, 50))
        screen.blit(go_text, (SCREEN_W // 2 - go_text.get_width() // 2, 180))

        sc_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(sc_text, (SCREEN_W // 2 - sc_text.get_width() // 2, 300))

        re_text = font.render("Press ENTER to restart", True, (200, 200, 200))
        screen.blit(re_text, (SCREEN_W // 2 - re_text.get_width() // 2, 400))

        q_text = font.render("Press ESC to quit", True, (200, 200, 200))
        screen.blit(q_text, (SCREEN_W // 2 - q_text.get_width() // 2, 450))

        pygame.display.flip()
        clock.tick(30)


def main():
    while True:
        score = game_loop()
        if not game_over_screen(score):
            break
    pygame.quit()


if __name__ == "__main__":
    main()
