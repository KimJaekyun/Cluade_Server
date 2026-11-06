import os
import random
import sys

import pygame
from pygame.locals import (QUIT, KEYDOWN, K_ESCAPE, K_RETURN, K_p, K_b, K_x, K_LCTRL)

from settings import W, H, FPS, MAX_POWER, MAX_BOMBS, MAX_LIVES
from audio import Audio
from effects import Background, Effects, draw_text, draw_plane
from player import Player
from enemies import Enemy, Boss
from items import Item
from stages import STAGES

HS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'highscore.txt')


def load_hi():
    try:
        with open(HS_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return 0


def save_hi(v):
    try:
        with open(HS_FILE, 'w') as f:
            f.write(str(v))
    except Exception:
        pass


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption('1945 SKY STRIKER')
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        self.bg = Background()
        self.fx = Effects()
        self.hi = load_hi()
        self.state = 'title'
        self.paused = False
        self.shake = 0
        self.tick = 0
        self.score = 0

    # ---------- 게임 시작/스테이지 ----------
    def new_game(self):
        self.player = Player()
        self.score = 0
        self.stage_idx = 0
        self.over_timer = 0
        self.state = 'play'
        self.start_stage()

    def start_stage(self):
        self.stage = STAGES[self.stage_idx]
        self.bg.theme = self.stage_idx
        self.t = 0
        self.wave_i = 0
        self.enemies, self.pbul, self.ebul, self.items = [], [], [], []
        self.boss = None
        self.boss_spawned = False
        self.clear_timer = 0
        self.banner = 150
        self.warn = 0
        self.bomb_t = 0
        self.player.respawn()

    # ---------- 이벤트 ----------
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == QUIT:
                self.quit()
            if e.type != KEYDOWN:
                continue
            if self.state == 'title':
                if e.key == K_RETURN:
                    self.new_game()
                elif e.key == K_ESCAPE:
                    self.quit()
            elif self.state == 'play':
                if e.key == K_ESCAPE:
                    self.state = 'title'
                elif e.key == K_p:
                    self.paused = not self.paused
                elif e.key in (K_b, K_x, K_LCTRL) and not self.paused:
                    self.use_bomb()
            elif self.state in ('gameover', 'victory'):
                if e.key == K_RETURN:
                    self.state = 'title'

    def quit(self):
        pygame.quit()
        sys.exit()

    # ---------- 전투 로직 ----------
    def damage(self, e, dmg):
        if e.dead:
            return
        e.hit(dmg)
        if e.hp <= 0:
            self.kill(e)

    def kill(self, e):
        e.dead = True
        self.score += e.score
        if e.is_boss:
            self.on_boss_dead(e)
            return
        big = e.kind == 'medium'
        self.fx.explode(e.x, e.y, 2.0 if big else 1.0)
        self.fx.popup(e.x, e.y - 10, str(e.score), (255, 240, 140))
        self.audio.play('boom')
        if big:
            self.shake = max(self.shake, 8)
        self.drop(e)

    def drop(self, e):
        chance = {'small': 0.10, 'zigzag': 0.15, 'swoop': 0.15, 'medium': 0.9}[e.kind]
        if random.random() > chance:
            return
        kind = random.choices('PBLS', weights=[40, 14, 4, 42])[0]
        if e.kind == 'medium':
            kind = random.choices('PBLS', weights=[60, 20, 5, 15])[0]
        self.items.append(Item(kind, e.x, e.y))

    def on_boss_dead(self, b):
        self.audio.play('bigboom')
        self.shake = 40
        for _ in range(14):
            self.fx.explode(b.x + random.randint(-60, 60), b.y + random.randint(-35, 35),
                            random.uniform(1.0, 2.5))
        self.fx.popup(b.x, b.y, '+%d' % b.score, (255, 240, 140))
        self.ebul.clear()
        for e in self.enemies:
            if not e.dead:
                e.dead = True
                self.fx.explode(e.x, e.y, 1.0)
        self.boss = None
        self.clear_timer = 240
        self.player.inv = max(self.player.inv, 300)

    def use_bomb(self):
        p = self.player
        if p.dead or p.bombs <= 0 or self.bomb_t > 0 or self.clear_timer > 0:
            return
        p.bombs -= 1
        self.bomb_t = 60
        p.inv = max(p.inv, 120)
        self.ebul.clear()
        self.audio.play('bomb')
        self.shake = max(self.shake, 20)
        for e in list(self.enemies):
            self.damage(e, 25)
        if self.boss is not None:
            self.damage(self.boss, 40)

    def hurt_player(self):
        p = self.player
        p.lives -= 1
        p.power = max(1, p.power - 1)
        p.bombs = max(p.bombs, 2)
        self.fx.explode(p.x, p.y, 1.6)
        self.audio.play('hurt')
        self.shake = max(self.shake, 15)
        self.ebul.clear()
        if p.lives <= 0:
            p.dead = True
            self.over_timer = 100
        else:
            p.respawn()

    def apply_item(self, it):
        p = self.player
        self.audio.play('item')
        if it.kind == 'P':
            if p.power < MAX_POWER:
                p.power += 1
                self.fx.popup(p.x, p.y - 30, 'POWER UP!', (255, 120, 90))
            else:
                self.score += 1000
                self.fx.popup(p.x, p.y - 30, '+1000', (255, 240, 140))
        elif it.kind == 'B':
            if p.bombs < MAX_BOMBS:
                p.bombs += 1
                self.fx.popup(p.x, p.y - 30, 'BOMB +1', (120, 170, 255))
            else:
                self.score += 1000
        elif it.kind == 'L':
            if p.lives < MAX_LIVES:
                p.lives += 1
                self.fx.popup(p.x, p.y - 30, '1UP!', (120, 230, 140))
            else:
                self.score += 2000
        else:
            self.score += 500
            self.fx.popup(p.x, p.y - 30, '+500', (255, 240, 140))

    # ---------- 업데이트 ----------
    def update_play(self):
        p = self.player
        keys = pygame.key.get_pressed()
        self.t += 1
        self.bg.update()
        if self.banner > 0:
            self.banner -= 1
        if self.warn > 0:
            self.warn -= 1
        if self.bomb_t > 0:
            self.bomb_t -= 1

        # 스폰
        if self.clear_timer == 0:
            waves = self.stage['waves']
            while self.wave_i < len(waves) and waves[self.wave_i][0] * FPS <= self.t:
                _, kind, x = waves[self.wave_i]
                self.enemies.append(Enemy(kind, x, self.stage_idx + 1))
                self.wave_i += 1
            if not self.boss_spawned and self.t >= self.stage['boss_time'] * FPS:
                self.boss_spawned = True
                self.boss = Boss(self.stage_idx + 1)
                self.warn = 150
                self.audio.play('warn')

        if not p.dead:
            p.update(keys, self.pbul, self.audio)

        for b in self.pbul:
            b.update()
        for b in self.ebul:
            b.update()
        for e in self.enemies:
            e.update(p, self.ebul)
        if self.boss is not None:
            self.boss.update(p, self.ebul)
        for it in self.items:
            it.update(p)

        # 플레이어 탄 vs 적
        targets = self.enemies + ([self.boss] if self.boss is not None else [])
        for b in self.pbul:
            if b.dead:
                continue
            for e in targets:
                if not e.dead and e.collide(b.x, b.y, b.r):
                    b.dead = True
                    self.audio.play('hit')
                    self.damage(e, b.dmg)
                    break

        # 적/적탄 vs 플레이어
        if not p.dead and p.inv <= 0:
            hit = False
            for b in self.ebul:
                if (b.x - p.x) ** 2 + (b.y - p.y) ** 2 < (b.r + p.hit_r) ** 2:
                    hit = True
                    break
            if not hit:
                for e in targets:
                    if not e.dead and e.collide(p.x, p.y, p.hit_r + 2):
                        hit = True
                        break
            if hit:
                self.hurt_player()

        # 아이템 습득
        if not p.dead:
            for it in self.items:
                if (it.x - p.x) ** 2 + (it.y - p.y) ** 2 < (it.r + 18) ** 2:
                    it.dead = True
                    self.apply_item(it)

        # 정리
        self.pbul = [b for b in self.pbul if not b.dead]
        self.ebul = [b for b in self.ebul if not b.dead]
        self.enemies = [e for e in self.enemies if not e.dead]
        self.items = [i for i in self.items if not i.dead]
        self.fx.update()
        if self.shake > 0:
            self.shake -= 1

        # 스테이지 클리어 진행
        if self.clear_timer > 0:
            self.clear_timer -= 1
            if self.clear_timer == 0:
                if self.stage_idx + 1 < len(STAGES):
                    self.stage_idx += 1
                    self.start_stage()
                else:
                    self.finish('victory')

        if p.dead:
            self.over_timer -= 1
            if self.over_timer <= 0:
                self.finish('gameover')

    def finish(self, state):
        if self.score > self.hi:
            self.hi = self.score
            save_hi(self.hi)
        self.state = state

    # ---------- 그리기 ----------
    def draw_play(self, s):
        self.bg.draw(s)
        for it in self.items:
            it.draw(s)
        for e in self.enemies:
            e.draw(s)
        if self.boss is not None:
            self.boss.draw(s)
        for b in self.pbul:
            b.draw(s)
        self.player.draw(s)
        for b in self.ebul:
            b.draw(s)
        self.fx.draw(s)
        if self.bomb_t > 0:
            r = (60 - self.bomb_t) * 14
            pygame.draw.circle(s, (255, 255, 200), (int(self.player.x), int(self.player.y)), r, 8)
            pygame.draw.circle(s, (255, 180, 80), (int(self.player.x), int(self.player.y)), max(1, r - 30), 4)
        self.draw_hud(s)

    def draw_hud(self, s):
        p = self.player
        draw_text(s, 'SCORE %07d' % self.score, 20, (255, 255, 255), (10, 8), center=False)
        draw_text(s, 'HI %07d' % max(self.hi, self.score), 20, (255, 230, 120), (W - 10, 20), center=True)
        # 목숨
        for i in range(p.lives):
            draw_plane(s, 22 + i * 28, H - 22, 0.5, (200, 215, 230), (70, 150, 90))
        # 폭탄
        draw_text(s, 'BOMB x%d' % p.bombs, 18, (140, 190, 255), (W - 10, H - 40), center=False)
        # 파워
        draw_text(s, 'POWER', 14, (255, 255, 255), (W - 130, H - 18), center=True)
        for i in range(MAX_POWER):
            col = (255, 110, 70) if i < p.power else (70, 70, 70)
            pygame.draw.rect(s, col, (W - 95 + i * 18, H - 26, 14, 14))
        if self.boss is not None and self.boss.y >= 130:
            self.boss.draw_hud(s)
            draw_text(s, 'BOSS', 14, (255, 120, 120), (W // 2, 42))
        if self.banner > 0:
            a = min(1.0, self.banner / 40)
            draw_text(s, self.stage['name'], 28, (255, 255, 255), (W // 2, H // 3))
        if self.warn > 0 and (self.warn // 12) % 2 == 0:
            draw_text(s, 'WARNING!!', 44, (255, 60, 60), (W // 2, H // 3))
        if self.clear_timer > 0:
            draw_text(s, 'STAGE CLEAR!', 40, (255, 240, 120), (W // 2, H // 3))
        if self.paused:
            draw_text(s, 'PAUSED', 48, (255, 255, 255), (W // 2, H // 2))

    def draw_title(self, s):
        self.bg.draw(s)
        draw_text(s, '1945', 96, (255, 220, 70), (W // 2, 190))
        draw_text(s, 'SKY STRIKER', 38, (255, 255, 255), (W // 2, 265))
        draw_plane(s, W // 2, 380 + (self.tick // 6 % 2) * 3, 2.2, (200, 215, 230), (70, 150, 90))
        if (self.tick // 30) % 2 == 0:
            draw_text(s, 'PRESS ENTER', 28, (255, 255, 255), (W // 2, 500))
        draw_text(s, '이동: 방향키/WASD   (Shift: 정밀 이동)', 16, (230, 240, 255), (W // 2, 560))
        draw_text(s, '발사: Space/J/Z   폭탄: B/X   일시정지: P', 16, (230, 240, 255), (W // 2, 586))
        draw_text(s, 'HI SCORE %07d' % self.hi, 20, (255, 230, 120), (W // 2, 640))

    def draw_end(self, s, title, color):
        self.bg.draw(s)
        draw_text(s, title, 52, color, (W // 2, 250))
        draw_text(s, 'SCORE %07d' % self.score, 28, (255, 255, 255), (W // 2, 340))
        draw_text(s, 'HI SCORE %07d' % self.hi, 22, (255, 230, 120), (W // 2, 385))
        if (self.tick // 30) % 2 == 0:
            draw_text(s, 'PRESS ENTER', 26, (255, 255, 255), (W // 2, 480))

    # ---------- 메인 루프 ----------
    def run(self):
        while True:
            self.tick += 1
            self.handle_events()
            c = self.canvas
            if self.state == 'title':
                self.bg.update(0.6)
                self.draw_title(c)
            elif self.state == 'play':
                if not self.paused:
                    self.update_play()
                if self.state == 'play':
                    self.draw_play(c)
            elif self.state == 'gameover':
                self.bg.update(0.4)
                self.draw_end(c, 'GAME OVER', (255, 80, 80))
            elif self.state == 'victory':
                self.bg.update(0.4)
                self.draw_end(c, 'MISSION COMPLETE!', (255, 230, 90))
            ox = oy = 0
            if self.shake > 0 and self.state == 'play':
                ox, oy = random.randint(-4, 4), random.randint(-4, 4)
            self.screen.fill((0, 0, 0))
            self.screen.blit(c, (ox, oy))
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == '__main__':
    Game().run()
