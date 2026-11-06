import math
import pygame
from effects import draw_text

KINDS = {
    'P': ((230, 70, 50), 'P'),
    'B': ((60, 120, 230), 'B'),
    'L': ((60, 190, 90), 'UP'),
    'S': ((240, 200, 40), '$'),
}


class Item:
    r = 12

    def __init__(self, kind, x, y):
        self.kind, self.x, self.y = kind, x, y
        self.dead = False

    def update(self, player):
        self.y += 1.6
        if not player.dead:
            d = math.hypot(player.x - self.x, player.y - self.y) or 1.0
            if d < 90:  # 자석
                self.x += (player.x - self.x) / d * 4
                self.y += (player.y - self.y) / d * 4
        if self.y > 760:
            self.dead = True

    def draw(self, s):
        col, label = KINDS[self.kind]
        c = (int(self.x), int(self.y))
        pygame.draw.circle(s, col, c, self.r)
        pygame.draw.circle(s, (255, 255, 255), c, self.r, 2)
        draw_text(s, label, 13 if len(label) > 1 else 16, (255, 255, 255), c, shadow=False)
