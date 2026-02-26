# 배포 가이드 (GitHub + Render, Beta 검증 후 운영 반영)

## 1) 로컬에서 실행 확인
```powershell
python blog.py
```
브라우저에서 `http://127.0.0.1:8000` 접속 후 기능 점검

## 2) GitHub 저장소 생성 및 초기 업로드
아래 명령은 프로젝트 폴더(`바이브코딩`)에서 실행

```powershell
git init
git add .
git commit -m "feat: demo inquiry landing with faq chatbot and community board"
git branch -M main
git remote add origin https://github.com/<YOUR_ID>/<YOUR_REPO>.git
git push -u origin main
```

## 3) Beta 브랜치 생성
```powershell
git checkout -b beta
git push -u origin beta
```

## 4) Render 배포 (Beta/Prod 분리)
1. Render 가입 후 Dashboard 진입
2. `New +` -> `Blueprint` 선택
3. GitHub 저장소 연결
4. `render.yaml` 인식 후 배포 실행

생성되는 서비스:
- `drpalette-beta` (beta 브랜치)
- `drpalette-prod` (main 브랜치)

## 5) Beta 검증 플로우
1. 개발 변경 작업
2. `beta` 브랜치에 push
3. `drpalette-beta` URL에서 QA 체크
4. 문제 없으면 `beta -> main` PR/merge
5. `drpalette-prod` 자동 반영 확인

## 6) 업데이트 배포 방법
### Beta 먼저 배포
```powershell
git checkout beta
# 코드 수정
python blog.py   # 로컬 확인
git add .
git commit -m "feat: ..."
git push
```

### 운영 반영
- GitHub에서 `beta -> main` Pull Request 생성
- 리뷰/머지
- Render `drpalette-prod` 자동 배포 확인

## 7) 꼭 확인할 운영 포인트
- 현재 데이터는 메모리 저장이라 재시작 시 초기화됨
- 운영에서는 SQLite/PostgreSQL 같은 영구 저장소 권장
- 챗봇은 현재 키워드 룰 기반이므로 추후 LLM API 연동 가능

## 8) 헬스체크
```text
GET /health
```
정상 응답 예시:
```json
{"status":"ok","time":"2026-02-25 21:10"}
```
