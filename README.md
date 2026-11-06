# Cluade_Server

브라우저에서 즐기는 미니 게임 모음과 게임 서버입니다.

| 폴더/파일 | 설명 |
|---|---|
| `shooter1945/` | **1945 SKY STRIKER** — 세로 스크롤 슈팅게임 (Pygame 버전 + 브라우저 버전) |
| `shooter1945/server/` | 1945 게임용 Node.js + Express + MySQL(`1945game`) 서버 |
| `index.html`, `intro.html` | 토끼 당근 피하기 (단일 HTML 캔버스 게임)과 인트로 애니메이션 |

## 1945 SKY STRIKER

3개 스테이지, 스테이지별 3단계 패턴 보스, 파워업·폭탄·목숨 아이템이 있는 세로 스크롤 슈팅게임입니다.
이미지와 사운드 파일 없이 코드로 그리고 합성합니다.

### 조작

| 키 | 동작 |
|---|---|
| 방향키 / WASD | 이동 (Shift: 정밀 이동, 피격 판정 점 표시) |
| Space / J / Z | 발사 |
| B / X / Ctrl | 폭탄 (적탄 제거 + 광역 피해) |
| P | 일시정지 |
| Esc | 타이틀로 |

모바일(브라우저 버전)은 화면을 드래그하면 이동하고 자동 발사되며, 우측 하단 BOMB 버튼으로 폭탄을 씁니다.

### 실행 방법

**브라우저 버전 (서버 없이)** — `shooter1945/web/index.html`을 브라우저로 엽니다.
이 경우 로그인·랭킹은 동작하지 않고, 하이스코어는 브라우저에 저장됩니다.

**Pygame 버전**
```bash
cd shooter1945
pip install pygame
python main.py
```

**서버와 함께 (로그인·랭킹·통계)**
```bash
cd shooter1945/server
cp .env.example .env          # DB 접속 정보와 JWT_SECRET 입력
npm install --omit=dev
npm start                     # http://localhost:3000
```
MySQL에는 먼저 `shooter1945/server/schema.sql`을 실행해 `1945game` 데이터베이스를 만들어야 합니다.
자세한 내용(nginx 설정, pm2, API 목록, 밸런스 수정)은 [`shooter1945/server/README.md`](shooter1945/server/README.md)를 보세요.

### 스테이지 (브라우저 버전)

4개 스테이지가 **무작위 순서**로 모두 나오고, 뒤에 나올수록 적과 탄막이 강해집니다. 각 스테이지 끝의 보스는 체력 50%에서 두 번째 형태로 변신합니다.

| 스테이지 | 배경 | 특징 | 보스 |
|---|---|---|---|
| 독일 군사기지 | 설산·벙커 | 전투기 편대, 지상 포탑 | Graf Zeppelin → 인간형 로봇 |
| 일본 수도 | 기와지붕 도시 | 자폭기, 지상 포탑 | Syumi Type O → 날개 접힌 메카 |
| 해상 전함 | 바다·섬 | 호위함, 곡선 비행기 | Iron Casket → 양팔 로봇 |
| 지상 요새 | 사막·바위 | 전차, 지상 포탑 | Goliath → 다각 보행 형태 |

Pygame 버전은 기존 3스테이지 그대로입니다.

### 서버가 저장하는 데이터

- `players` — 계정 (비밀번호는 bcrypt 해시)
- `play_logs` — 한 판마다 점수, 스테이지, 플레이 시간, 격추 수, 폭탄 사용 수, 종료 원인 (랭킹·통계용)
- `game_config` — 적 체력/점수/드롭률, 보스 체력, 시작 목숨·폭탄 (DB에서 수정하면 게임에 반영)

### 구조 참고

Pygame 코드와 `web/index.html`은 같은 게임의 별도 구현이라 코드를 공유하지 않습니다.
밸런스나 게임플레이를 바꾸면 두 곳을 모두 수정해야 합니다. 서버 연동은 브라우저 버전에만 있습니다.

## 보안 참고

- `.env`(DB 비밀번호, `JWT_SECRET`)는 저장소에 올리지 않습니다 (`.gitignore`로 제외).
- 로그인 기능이 있으므로 공개 서비스는 HTTPS로 운영하세요.
