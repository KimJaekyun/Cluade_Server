"""스테이지 정의: 웨이브 타임라인 (초, 적종류, x좌표) + 보스 등장 시각."""
import random
from settings import W


def build(n):
    rng = random.Random(100 + n)
    waves = []
    patterns = ['line', 'vee', 'column', 'medium']
    if n >= 2:
        patterns += ['swoop', 'swoop']
    if n >= 3:
        patterns += ['medium', 'column']
    end = 40 + 6 * n
    t = 2.0
    while t < end:
        p = rng.choice(patterns)
        if p == 'line':
            for i in range(5):
                waves.append((t, 'small', 60 + i * 90))
        elif p == 'vee':
            for i in range(-2, 3):
                waves.append((t + abs(i) * 0.4, 'small', W / 2 + i * 60))
        elif p == 'column':
            x = rng.randint(100, W - 100)
            for i in range(5):
                waves.append((t + i * 0.5, 'zigzag', x))
        elif p == 'swoop':
            x = 20 if rng.random() < 0.5 else W - 20
            for i in range(4):
                waves.append((t + i * 0.5, 'swoop', x))
        elif p == 'medium':
            waves.append((t, 'medium', rng.randint(100, W - 100)))
        t += rng.uniform(2.4, 3.6) - 0.25 * n
    waves.sort(key=lambda w: w[0])
    names = ['STAGE 1  -  태평양 상공', 'STAGE 2  -  산호초 해협', 'STAGE 3  -  최후의 요새']
    return dict(name=names[n - 1], waves=waves, boss_time=end + 4)


STAGES = [build(1), build(2), build(3)]
