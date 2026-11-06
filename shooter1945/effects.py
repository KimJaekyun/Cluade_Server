import math
import random
import pygame
from settings import W, H

_fonts = {}


def get_font(size, bold=True):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont(
            'malgungothic,applegothic,nanumgothic,arial', size, bold=bold)
    return _fonts[key]


def draw_text(surf, text, size, color, pos, center=True, shadow=True):
    f = get_font(size)
    img = f.render(text, True, color)
    r = img.get_rect()
    if center:
        r.center = pos
    else:
        r.topleft = pos
    if shadow:
        surf.blit(f.render(text, True, (0, 0, 0)), r.move(2, 2))
    surf.blit(img, r)


_BODY = [(0, -22), (4, -10), (5, 10), (0, 20), (-5, 10), (-4, -10)]
_WING = [(0, -4), (24, 8), (24, 14), (0, 8), (-24, 14), (-24, 8)]
_TAIL = [(0, 12), (10, 22), (10, 24), (0, 20), (-10, 24), (-10, 22)]


def draw_plane(surf, x, y, s, body, wing, up=True, flash=False):
    k = 1 if up else -1

    def tr(pts):
        return [(x + px * s, y + py * s * k) for px, py in pts]

    wc = (255, 255, 255) if flash else wing
    bc = (255, 255, 255) if flash else body
    pygame.draw.polygon(surf, wc, tr(_WING))
    pygame.draw.polygon(surf, (20, 20, 30), tr(_WING), 1)
    pygame.draw.polygon(surf, wc, tr(_TAIL))
    pygame.draw.polygon(surf, bc, tr(_BODY))
    pygame.draw.polygon(surf, (20, 20, 30), tr(_BODY), 1)
    pygame.draw.circle(surf, (90, 170, 230), (int(x), int(y - 6 * s * k)), max(2, int(3 * s)))


THEMES = [
    dict(sea=(32, 96, 168), wave=(60, 130, 200), land=(70, 150, 70), sand=(220, 200, 140)),
    dict(sea=(22, 110, 120), wave=(50, 150, 150), land=(120, 140, 60), sand=(230, 210, 150)),
    dict(sea=(40, 30, 70), wave=(80, 60, 120), land=(60, 40, 60), sand=(150, 90, 90)),
]


class Background:
    def __init__(self):
        rng = random.Random(7)
        self.theme = 0
        self.scroll = 0.0
        self.islands = [[rng.randint(0, W), rng.randint(-H, H), rng.randint(30, 70), rng.randint(20, 40)]
                        for _ in range(6)]
        self.clouds = []
        for _ in range(8):
            w, h = rng.randint(60, 130), rng.randint(26, 46)
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            for _ in range(4):
                cw, ch = rng.randint(w // 3, w // 2 + 10), rng.randint(h // 2, h - 2)
                pygame.draw.ellipse(surf, (255, 255, 255, 70),
                                    (rng.randint(0, w - cw), rng.randint(0, h - ch), cw, ch))
            self.clouds.append([rng.randint(0, W), rng.randint(0, H), surf, rng.uniform(2.0, 3.2)])

    def update(self, speed=1.0):
        self.scroll = (self.scroll + 1.5 * speed) % 40
        for isl in self.islands:
            isl[1] += 1.5 * speed
            if isl[1] > H + 80:
                isl[0], isl[1] = random.randint(0, W), -80
        for c in self.clouds:
            c[1] += c[3] * speed
            if c[1] > H + 50:
                c[0], c[1] = random.randint(-20, W), -50

    def draw(self, surf):
        th = THEMES[self.theme % len(THEMES)]
        surf.fill(th['sea'])
        for row, y in enumerate(range(-40, H + 40, 40)):
            yy = y + self.scroll
            for x in range((row % 2) * 30, W, 90):
                pygame.draw.line(surf, th['wave'], (x, yy), (x + 18, yy), 2)
        for x, y, w, h in self.islands:
            pygame.draw.ellipse(surf, th['sand'], (x - w // 2 - 6, y - h // 2 - 6, w + 12, h + 12))
            pygame.draw.ellipse(surf, th['land'], (x - w // 2, y - h // 2, w, h))
        for x, y, img, _ in self.clouds:
            surf.blit(img, (x, y))


class Effects:
    def __init__(self):
        self.parts, self.pops, self.rings = [], [], []

    def explode(self, x, y, size=1.0):
        for _ in range(int(14 * size) + 6):
            a = random.uniform(0, math.tau)
            sp = random.uniform(1, 5) * size ** 0.5
            life = random.randint(18, 38)
            col = random.choice([(255, 220, 80), (255, 150, 40), (255, 90, 30), (255, 255, 255)])
            self.parts.append([x, y, math.cos(a) * sp, math.sin(a) * sp, life, life, col,
                               random.uniform(2, 5) * size ** 0.5])
        self.rings.append([x, y, 4.0, 18 * size + 14])

    def popup(self, x, y, text, color=(255, 255, 255)):
        self.pops.append([x, y, 45, text, color])

    def update(self):
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.95
            p[3] *= 0.95
            p[4] -= 1
        self.parts = [p for p in self.parts if p[4] > 0]
        for r in self.rings:
            r[2] += 3
        self.rings = [r for r in self.rings if r[2] < r[3]]
        for p in self.pops:
            p[1] -= 0.8
            p[2] -= 1
        self.pops = [p for p in self.pops if p[2] > 0]

    def draw(self, surf):
        for x, y, r, mr in self.rings:
            pygame.draw.circle(surf, (255, 230, 150), (int(x), int(y)), int(r), 2)
        for x, y, _, _, life, ml, col, size in self.parts:
            sz = max(1, int(size * life / ml))
            pygame.draw.circle(surf, col, (int(x), int(y)), sz)
        for x, y, _, text, color in self.pops:
            draw_text(surf, text, 18, color, (x, y))
