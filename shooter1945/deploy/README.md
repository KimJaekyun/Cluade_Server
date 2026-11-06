# Jenkins CI/CD 설정

GitHub `main` 푸시 → Jenkins 파이프라인(`/Jenkinsfile`) → 서버 `deploy-game-1945.sh` → Docker 빌드(문법 검사) → 컨테이너 교체 → 헬스체크 → 실패 시 자동 롤백.

Jenkins 컨테이너에는 docker 권한이 없고, **`deploy` 한 가지 명령만 실행할 수 있는 전용 SSH 키**로 서버에 접속합니다.

## 1. 서버: 전용 키 만들기 (한 번만, ubuntu 계정)
```bash
ssh-keygen -t ed25519 -N "" -C "jenkins-game1945-deploy" -f ~/.ssh/jenkins_game1945_deploy
echo "restrict,command=\"/srv/doc-util/jenkins/deploy-game-1945.sh\",from=\"172.19.0.0/16\" $(cat ~/.ssh/jenkins_game1945_deploy.pub)" >> ~/.ssh/authorized_keys
```
- `restrict`: 터미널·포트포워딩 등 모두 차단 / `command=`: 이 키로는 지정한 스크립트만 실행 / `from=`: Docker 내부망(Jenkins 컨테이너)에서만 접속 허용.
- 스크립트 설치 위치: `/srv/doc-util/jenkins/deploy-game-1945.sh` (원본: `shooter1945/deploy/deploy-game-1945.sh`).

## 2. Jenkins: 자격 증명 등록
Manage Jenkins → Credentials → (global) → Add Credentials
- Kind: **SSH Username with private key**
- ID: **`game1945-deploy`** (Jenkinsfile 과 같아야 함)
- Username: `ubuntu`
- Private Key → Enter directly → 서버에서 `cat ~/.ssh/jenkins_game1945_deploy` 한 내용을 붙여넣기
- 등록 후 서버의 개인키 파일은 삭제해도 됩니다: `shred -u ~/.ssh/jenkins_game1945_deploy*`

## 3. Jenkins: 파이프라인 Job
New Item → 이름 `game-1945` → **Pipeline**
- Build Triggers: **GitHub hook trigger for GITScm polling** 체크
- Pipeline: **Pipeline script from SCM** → SCM `Git`
  - Repository URL: `https://github.com/KimJaekyun/Cluade_Server.git` (공개 저장소라 자격 증명 불필요)
  - Branch Specifier: `*/main`
  - Script Path: `Jenkinsfile`

## 4. GitHub 웹훅
저장소 → Settings → Webhooks → Add webhook
- Payload URL: `https://jenkins.kjkwiner.shop/github-webhook/`
- Content type: `application/json`
- Events: Just the push event

## 확인
- Jenkins 에서 `Build Now` → 로그에 `배포 성공` 이 나오면 완료.
- 서버 로그: `/srv/doc-util/jenkins/deploy-game-1945.log`
- 문법 오류가 있는 커밋을 푸시하면 Docker 빌드(`node check.js`)가 실패하고, 기존 컨테이너는 그대로 유지됩니다.
