import pygame
from pygame.locals import K_LEFT, K_RIGHT, K_UP, K_DOWN, K_a, K_d, K_w, K_s, K_SPACE, K_j, K_z, K_LSHIFT
from settings import W, H, MAX_POWER
from bullets import Bullet
from effects import draw_plane

# (x 오프셋, vx) 패턴 - 파워 레벨별
PATTERNS = {
    1: [(0, 0)],
    2: [(-8, 0), (8, 0)],
    3: [(0, 0), (-12, -1.5), (12, 1.5)],
    4: [(0, 0), (-10, -1.2), (10, 1.2), (-18, -2.6), (18, 2.6)],
}


class Player:
    hit_r = 4

    def __init__(self):
        self.lives, self.bombs, self.power = 3, 3, 1
        self.slow = False
        self.respawn()

    def respawn(self):
        self.x, self.y = W / 2, H - 90
        self.inv = 150
        self.cool = 0
        self.dead = False
        self.t = 0

    def update(self, keys, bullets, audio):
        self.t += 1
        dx = int(bool(keys[K_RIGHT] or keys[K_d])) - int(bool(keys[K_LEFT] or keys[K_a]))
        dy = int(bool(keys[K_DOWN] or keys[K_s])) - int(bool(keys[K_UP] or keys[K_w]))
        self.slow = bool(keys[K_LSHIFT])
        sp = 2.5 if self.slow else 5.0
        if dx and dy:
            sp *= 0.7071
        self.x = min(W - 20, max(20, self.x + dx * sp))
        self.y = min(H - 25, max(30, self.y + dy * sp))
        if self.inv > 0:
            self.inv -= 1
        if self.cool > 0:
            self.cool -= 1
        if (keys[K_SPACE] or keys[K_j] or keys[K_z]) and self.cool <= 0:
            self.cool = 8
            for ox, vx in PATTERNS[min(self.power, MAX_POWER)]:
                bullets.append(Bullet(self.x + ox, self.y - 20, vx, -12, 3, 1, 'p'))
            audio.play('shoot')

    def draw(self, surf):
        if self.dead:
            return
        if self.inv > 0 and (self.inv // 4) % 2 == 0:
            return
        draw_plane(surf, self.x, self.y, 1.0, (200, 215, 230), (70, 150, 90), up=True)
        w = 10 if self.t % 2 else 16  # 프로펠러
        pygame.draw.line(surf, (230, 230, 230), (self.x - w, self.y - 23), (self.x + w, self.y - 23), 2)
        if self.slow:
            pygame.draw.circle(surf, (255, 60, 60), (int(self.x), int(self.y)), self.hit_r)
            pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), self.hit_r, 1)
