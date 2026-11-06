"""외부 파일 없이 합성한 간단한 효과음. mixer 초기화 실패 시 무음."""
import array
import random
import pygame


class Audio:
    def __init__(self):
        self.ok = False
        self.sounds = {}
        self.rate = 22050
        try:
            pygame.mixer.init(self.rate, -16, 1, 512)
            self.ok = True
        except Exception:
            return
        make = self._tone
        self.sounds = {
            'shoot': make(1100, 600, 0.05, 'square', 0.06),
            'hit': make(300, 200, 0.04, 'square', 0.10),
            'boom': make(220, 40, 0.30, 'noise', 0.30),
            'bigboom': make(160, 20, 0.90, 'noise', 0.45),
            'item': make(600, 1500, 0.15, 'square', 0.15),
            'bomb': make(120, 30, 1.00, 'noise', 0.45),
            'hurt': make(400, 60, 0.40, 'square', 0.25),
            'warn': make(300, 300, 0.30, 'square', 0.20),
        }

    def _tone(self, f0, f1, dur, kind, vol):
        n = int(self.rate * dur)
        buf = array.array('h')
        phase = 0.0
        for i in range(n):
            t = i / n
            phase += (f0 + (f1 - f0) * t) / self.rate
            if kind == 'square':
                v = 1.0 if (phase % 1.0) < 0.5 else -1.0
            else:
                v = random.uniform(-1, 1)
            buf.append(int(v * (1 - t) * vol * 32767))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, name):
        if self.ok and name in self.sounds:
            self.sounds[name].play()
