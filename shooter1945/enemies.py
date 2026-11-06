import math
import pygame
from settings import W, H
from bullets import Bullet, aim, fan, ring
from effects import draw_plane

TYPES = {
    #           hp   r   score  body color        wing color
    'small':  (2,  14, 100, (190, 70, 70),   (150, 50, 50)),
    'zigzag': (3,  15, 200, (220, 150, 50),  (180, 110, 30)),
    'swoop':  (3,  14, 200, (170, 90, 200),  (120, 60, 160)),
    'medium': (16, 26, 700, (110, 125, 110), (80, 95, 80)),
}


class Enemy:
    is_boss = False

    def __init__(self, kind, x, stage):
        hp, self.r, self.score, self.body, self.wing = TYPES[kind]
        self.kind = kind
        self.stage = stage
        self.hp = hp + (stage - 1) * (4 if kind == 'medium' else 1)
        self.x, self.y = x, -30.0
        self.x0 = x
        self.dir = 1 if x < W / 2 else -1
        self.t = 0
        self.flash = 0
        self.dead = False
        self.scale = self.r / 14.0

    def update(self, player, ebul):
        self.t += 1
        k = self.kind
        spd = 1 + 0.1 * (self.stage - 1)
        if k == 'small':
            self.y += 2.4 * spd
            if self.stage >= 2 and self.t == 50:
                self._aimed(player, ebul, 4)
        elif k == 'zigzag':
            self.y += 1.8 * spd
            self.x = self.x0 + math.sin(self.t * 0.06) * 60
            if self.t % 90 == 45:
                self._aimed(player, ebul, 4)
        elif k == 'swoop':
            self.y += 2.5
            self.x += self.dir * (3.0 - self.t * 0.03)
            if self.stage >= 3 and self.t == 60:
                self._aimed(player, ebul, 4.5)
        elif k == 'medium':
            if self.t < 300:
                self.y += 0.8 if self.y < 150 else 0.0
            else:
                self.y += 1.5
            if self.t > 60 and self.t % max(40, 75 - 8 * self.stage) == 0:
                fan(ebul, self.x, self.y + 10, player.x, player.y, 3.6 + 0.3 * self.stage,
                    [-18, 0, 18] if self.stage < 3 else [-30, -15, 0, 15, 30])
        if self.flash:
            self.flash -= 1
        if self.y > H + 40 or self.x < -50 or self.x > W + 50:
            self.dead = True

    def _aimed(self, player, ebul, speed):
        if 0 < self.y < H - 150:
            vx, vy = aim(self.x, self.y, player.x, player.y, speed)
            ebul.append(Bullet(self.x, self.y, vx, vy, 4))

    def collide(self, px, py, pr):
        return (self.x - px) ** 2 + (self.y - py) ** 2 < (self.r + pr) ** 2

    def hit(self, dmg):
        self.hp -= dmg
        self.flash = 3

    def draw(self, s):
        draw_plane(s, self.x, self.y, self.scale, self.body, self.wing, up=False, flash=self.flash > 0)


class Boss:
    is_boss = True
    kind = 'boss'
    score = 0

    def __init__(self, stage):
        self.stage = stage
        self.maxhp = 260 + 160 * (stage - 1)
        self.hp = self.maxhp
        self.x, self.y = W / 2, -90.0
        self.t = 0
        self.flash = 0
        self.dead = False
        self.score = 5000 * stage
        self.spin = 0.0

    @property
    def phase(self):
        r = self.hp / self.maxhp
        return 1 if r > 0.66 else 2 if r > 0.33 else 3

    def update(self, player, ebul):
        if self.flash:
            self.flash -= 1
        if self.y < 130:
            self.y += 1.5
            return
        self.t += 1
        ph = self.phase
        self.x = W / 2 + math.sin(self.t * (0.012 + 0.004 * ph)) * 150
        sp = 3.4 + 0.3 * self.stage
        if ph == 1:
            if self.t % 50 == 0:
                fan(ebul, self.x, self.y + 30, player.x, player.y, sp, [-15, 0, 15])
            if self.t % 120 == 60:
                fan(ebul, self.x, self.y + 30, self.x, self.y + 100, sp - 0.5, [-40, -20, 0, 20, 40])
        elif ph == 2:
            if self.t % 10 == 0:
                self.spin += 0.35
                for off in (0, math.pi):
                    a = self.spin + off
                    ebul.append(Bullet(self.x, self.y + 20, math.cos(a) * sp, math.sin(a) * sp, 4))
            if self.t % 100 == 0:
                ring(ebul, self.x, self.y + 20, sp - 0.4, 16, self.t * 0.1)
        else:
            if self.t % 7 == 0:
                self.spin += 0.3
                for off in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
                    a = self.spin + off
                    ebul.append(Bullet(self.x, self.y + 20, math.cos(a) * sp, math.sin(a) * sp, 4))
            if self.t % 45 == 0:
                fan(ebul, self.x, self.y + 30, player.x, player.y, sp + 1, [-24, -12, 0, 12, 24])

    def collide(self, px, py, pr):
        rect = pygame.Rect(self.x - 62, self.y - 34, 124, 68).inflate(pr * 2, pr * 2)
        return rect.collidepoint(px, py)

    def hit(self, dmg):
        self.hp -= dmg
        self.flash = 3

    def draw(self, s):
        draw_plane(s, self.x, self.y, 2.4, (95, 100, 120), (60, 70, 95), up=False, flash=self.flash > 0)
        # 엔진 포드
        for ox in (-34, 34):
            pygame.draw.circle(s, (200, 80, 60), (int(self.x + ox), int(self.y - 10)), 6)

    def draw_hud(self, s):
        w = 300
        x0 = (W - w) // 2
        pygame.draw.rect(s, (40, 40, 40), (x0 - 2, 52, w + 4, 12))
        pygame.draw.rect(s, (220, 50, 50), (x0, 54, int(w * max(0, self.hp) / self.maxhp), 8))
