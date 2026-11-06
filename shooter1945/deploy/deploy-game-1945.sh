#!/usr/bin/env bash
# 1945 게임 배포 스크립트 (Jenkins 가 SSH 로 호출. 서버의 /srv/doc-util/jenkins/ 에 설치되어 있음)
#  - 사용법: deploy-game-1945.sh [커밋 SHA 40자]   (SSH forced command 로는 인자가 SSH_ORIGINAL_COMMAND 로 전달됨)
#  - 순서: 코드 받기 → 이미지 빌드(문법 검사 포함) → 컨테이너 교체 → /api/health 확인 → 실패 시 이전 버전으로 롤백
#  - 로그: /srv/doc-util/jenkins/deploy-game-1945.log
set -euo pipefail

APP=/srv/doc-util/game-1945
LOG=/srv/doc-util/jenkins/deploy-game-1945.log
LOCK=/tmp/deploy-game-1945.lock
HEALTH=http://localhost:9650/api/health

exec > >(tee -a "$LOG") 2>&1
exec 9>"$LOCK"
flock -n 9 || { echo "이미 다른 배포가 실행 중입니다."; exit 1; }

# SSH forced command 로 들어오면 인자는 SSH_ORIGINAL_COMMAND 에 들어있다 ("deploy <sha>")
ARG="${1:-}"
if [ -z "$ARG" ] && [ -n "${SSH_ORIGINAL_COMMAND:-}" ]; then ARG="${SSH_ORIGINAL_COMMAND#deploy }"; fi
SHA=""
if [ -n "$ARG" ] && [ "$ARG" != "deploy" ]; then
  [[ "$ARG" =~ ^[0-9a-f]{40}$ ]] || { echo "잘못된 인자(커밋 SHA 40자만 허용): $ARG"; exit 2; }
  SHA="$ARG"
fi

echo "=== $(date '+%F %T') 배포 시작 sha=${SHA:-origin/main}"
cd "$APP"
PREV=$(git rev-parse HEAD)
git fetch -q origin main
TARGET="${SHA:-$(git rev-parse origin/main)}"
git cat-file -e "$TARGET^{commit}" || { echo "커밋을 찾을 수 없습니다: $TARGET"; exit 3; }
git reset -q --hard "$TARGET"
echo "이전: $PREV"; echo "대상: $TARGET"

build_and_up() { (cd "$APP/shooter1945" && docker compose up -d --build); }
healthy() { for _ in $(seq 1 20); do curl -fsS -m 5 "$HEALTH" >/dev/null 2>&1 && return 0; sleep 3; done; return 1; }

if build_and_up && healthy; then
  echo "=== 배포 성공 $TARGET"
  docker image prune -f >/dev/null 2>&1 || true
  exit 0
fi

echo "!!! 배포 실패 — 이전 버전($PREV)으로 롤백합니다"
git reset -q --hard "$PREV"
build_and_up || true
if healthy; then echo "=== 롤백 완료(서비스 정상)"; else echo "!!! 롤백 후에도 헬스체크 실패 — 수동 확인 필요"; fi
exit 1
