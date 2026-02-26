# Auto Upload 스크립트 사용법

## 기본 (beta 브랜치 업로드)
```powershell
.\upload.ps1
```

## 메시지 지정
```powershell
.\upload.ps1 -Message "feat: 시연문의 폼 수정"
```

## main 브랜치 업로드
```powershell
.\upload.ps1 -Branch main -Message "release: beta 검증 완료 반영"
```

## pull 생략
```powershell
.\upload.ps1 -SkipPull
```

## 주의
- 현재 폴더가 Git 저장소여야 합니다.
- `origin` remote가 연결되어 있어야 합니다.
- 충돌 방지를 위해 기본적으로 push 전 `git pull`을 수행합니다.
