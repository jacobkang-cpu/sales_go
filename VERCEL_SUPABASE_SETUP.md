# Vercel Serverless + Supabase 연동 가이드

## 1) Supabase 테이블 생성
Supabase SQL Editor에서 아래 파일 실행:

- `supabase/schema.sql`

## 2) Vercel 환경변수 설정
Vercel Project Settings > Environment Variables 에서 추가:

- `SUPABASE_URL` : `https://<project-ref>.supabase.co`
- `SUPABASE_SERVICE_ROLE_KEY` : Supabase service role key
- `ADMIN_TOKEN` : 어드민 페이지에서 사용할 토큰 (예: 강한 임의 문자열)

`ADMIN_TOKEN`을 설정하지 않으면 기본값 `admin1234`가 사용됩니다.

## 3) 배포 후 API 확인
- `GET /api/card-config?slug=woojin`
- `POST /api/card-config` (헤더 `X-Admin-Token`)
- `POST /api/card-event`
- `GET /api/card-analytics?slug=woojin` (헤더 `X-Admin-Token`)

## 4) 페이지 경로
- 어드민: `/admin/index.html?slug=woojin`
- 대시보드: `/admin/dashboard.html?slug=woojin`
- 카드: `/card/woojin_card.html?slug=woojin`
- 상세: `/card/woojin_profile.html?slug=woojin`

## 참고
- `/api`는 Vercel Serverless Functions로 실행됩니다.
- 다수 사용자 데이터 저장/조회는 Supabase DB를 통해 처리됩니다.
