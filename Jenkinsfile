// 1945 게임 CI/CD 파이프라인
//  - GitHub main 푸시 → (웹훅) → 이 파이프라인 실행
//  - 배포는 서버의 deploy-game-1945.sh 가 수행: 코드 받기 → Docker 빌드(문법 검사 포함) → 교체 → 헬스체크 → 실패 시 자동 롤백
//  - Jenkins 에는 docker 권한이 없고, 'deploy 한 가지 명령만' 실행 가능한 제한된 SSH 키(자격 증명 ID: game1945-deploy)만 사용한다.
pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    timeout(time: 20, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '30'))
  }

  triggers { githubPush() }

  environment {
    DEPLOY_HOST = '172.19.0.1'   // Jenkins 컨테이너 기준 Docker 호스트(게이트웨이)
    DEPLOY_USER = 'ubuntu'
    HEALTH_URL  = 'https://game-1945.kjkwiner.shop/api/health'
    // 서버 sshd 호스트 키(공개키) 고정 — 중간자 공격 방지
    HOST_KEY    = '172.19.0.1 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINAdtTlkDYq+b8us1H+zvcHwOVa5lYMMy2wuP8ahZl2w'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'git log -1 --pretty="%h %s (%an)"'
        script { env.COMMIT_SHA = sh(returnStdout: true, script: 'git rev-parse HEAD').trim() }
      }
    }

    stage('Sanity') {
      steps {
        // 필수 파일 존재 확인 (문법 검사는 서버의 Docker 빌드 단계에서 node check.js 로 수행)
        sh '''
          for f in shooter1945/Dockerfile shooter1945/docker-compose.yml shooter1945/server/server.js \
                   shooter1945/server/check.js shooter1945/web/index.html shooter1945/web/dashboard.html; do
            test -f "$f" || { echo "누락: $f"; exit 1; }
          done
          echo "필수 파일 확인 완료"
        '''
      }
    }

    stage('Deploy') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'game1945-deploy', keyFileVariable: 'KEY')]) {
          sh '''
            set -e
            KH="$(mktemp)"; echo "$HOST_KEY" > "$KH"
            ssh -i "$KEY" -o IdentitiesOnly=yes -o BatchMode=yes \
                -o UserKnownHostsFile="$KH" -o StrictHostKeyChecking=yes \
                "$DEPLOY_USER@$DEPLOY_HOST" "deploy $COMMIT_SHA"
            rm -f "$KH"
          '''
        }
      }
    }

    stage('Verify') {
      steps {
        sh 'curl -fsS --retry 5 --retry-delay 3 --retry-all-errors -m 10 "$HEALTH_URL"'
      }
    }
  }

  post {
    success { echo "배포 성공: ${env.COMMIT_SHA}" }
    failure { echo '배포 실패 — 서버가 이전 버전으로 롤백했을 수 있습니다. 서버 로그: /srv/doc-util/jenkins/deploy-game-1945.log' }
  }
}
