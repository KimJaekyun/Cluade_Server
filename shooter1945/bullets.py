import math
import pygame
from settings import W, H


class Bullet:
    """플레이어 탄('p')과 적 탄('e') 공용."""

    def __init__(self, x, y, vx, vy, r=3, dmg=1, kind='e'):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.r, self.dmg, self.kind = r, dmg, kind
        self.dead = False

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if not (-40 < self.x < W + 40 and -40 < self.y < H + 40):
            self.dead = True

    def draw(self, s):
        if self.kind == 'p':
            pygame.draw.ellipse(s, (255, 240, 120), (self.x - 3, self.y - 9, 6, 16))
            pygame.draw.ellipse(s, (255, 255, 255), (self.x - 1, self.y - 6, 2, 9))
        else:
            pygame.draw.circle(s, (230, 40, 60), (int(self.x), int(self.y)), self.r)
            pygame.draw.circle(s, (255, 230, 230), (int(self.x), int(self.y)), max(1, self.r - 2))


def aim(x, y, tx, ty, speed):
    d = math.hypot(tx - x, ty - y) or 1.0
    return (tx - x) / d * speed, (ty - y) / d * speed


def fan(out, x, y, tx, ty, speed, angles_deg, r=4):
    """목표 방향 기준 부채꼴 발사."""
    base = math.atan2(ty - y, tx - x)
    for a in angles_deg:
        ang = base + math.radians(a)
        out.append(Bullet(x, y, math.cos(ang) * speed, math.sin(ang) * speed, r))


def ring(out, x, y, speed, count, offset=0.0, r=4):
    for i in range(count):
        ang = offset + i * 2 * math.pi / count
        out.append(Bullet(x, y, math.cos(ang) * speed, math.sin(ang) * speed, r))
