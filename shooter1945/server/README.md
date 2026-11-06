# 1945game 서버 (Node.js + Express + MySQL)

게임 파일(`../web`)과 API(`/api/*`)를 한 프로세스에서 서빙합니다.

## 1. DB 만들기 (Oracle 서버의 MySQL)
```bash
mysql -u root -p < schema.sql          # 1945game DB, 테이블 3개, 기본 설정값 생성
```
앱 전용 계정을 만들려면 `schema.sql` 맨 아래 주석을 풀고 비밀번호를 바꿔 실행하세요 (이 DB에만 권한 부여).

테이블: `players`(계정) · `play_logs`(판별 기록: 랭킹+통계) · `game_config`(밸런스 JSON)

## 2. 환경변수
```bash
cp .env.example .env   # DB_USER / DB_PASSWORD / JWT_SECRET 채우기
```

## 3. 실행
```bash
npm install --omit=dev
npm start              # http://localhost:3000
# 상시 실행: sudo npm i -g pm2 && pm2 start server.js --name 1945game && pm2 save
```

## 4. nginx 리버스 프록시 (예)
```
location / { proxy_pass http://127.0.0.1:3000; proxy_set_header X-Forwarded-For $remote_addr; }
```
3000 포트는 외부에 열지 말고 80/443만 여세요.

## API
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | /api/register, /api/login | 계정 (JWT 반환) |
| GET | /api/config | 게임 설정 (`game_config`) |
| POST | /api/runs | 1판 결과 저장 (로그인 시 랭킹 반영) |
| GET | /api/ranking?limit=10 | TOP 랭킹 |
| GET | /api/me | 내 통계 (로그인 필요) |

## AI 도우미 (OpenRouter)
게임 화면 우측 상단 `🤖 AI 도우미` 버튼으로 여는 채팅창입니다. 브라우저는 서버의 `/api/chat`만 호출하고, 서버가 OpenRouter를 대신 호출하므로 **API 키가 브라우저에 노출되지 않습니다.**

`.env` 설정 (서버에서 직접 입력, 채팅/저장소에 올리지 마세요):
```
OPENROUTER_API_KEY=<키>
OPENROUTER_MODEL=openai/gpt-4o-mini   # 선택: OpenRouter 모델 ID
CHAT_DAILY_LIMIT=500                  # 선택: 하루 전체 호출 상한
```
키가 비어 있으면 도우미는 "설정되지 않았습니다"라고 안내합니다. 남용 방지로 IP당 10분에 15회, 질문 500자, 대화 기록 최근 8개까지만 전송합니다. 게임 정보(조작/아이템/스테이지/보스)는 `server.js`의 `CHAT_SYSTEM`에 들어 있으니 게임이 바뀌면 함께 고치세요.

## 관리자 대시보드
`https://<도메인>/dashboard` — 랭킹 TOP 20, 요약 카드, 일별 플레이 추이(30일), 도달 스테이지/종료 원인 분포, 최근 50판.

1. 서버 `.env`에 `ADMIN_PASSWORD=<길고 추측하기 어려운 비밀번호>`를 추가합니다. 비워 두면 대시보드는 꺼집니다.
2. `docker compose up -d --force-recreate`로 반영합니다.
3. `/dashboard`에서 그 비밀번호로 로그인합니다 (12시간 유지, 브라우저 탭을 닫으면 로그아웃).

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | /api/admin/login | 관리자 로그인 (15분에 10회 제한) |
| GET | /api/admin/stats | 대시보드 데이터 (관리자 토큰 필요) |

날짜는 한국시간(KST) 기준으로 집계합니다.

## 밸런스 수정
`UPDATE game_config SET cfg_value = JSON_SET(cfg_value, '$.medium.hp', 24) WHERE cfg_key='enemies';`
(적 체력/점수/드롭률, 보스 체력, 시작 목숨·폭탄 — 재시작 없이 1분 내 반영)
