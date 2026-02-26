param(
    [string]$Branch = "beta",
    [string]$Message = "",
    [switch]$SkipPull
)

$ErrorActionPreference = "Stop"

function Fail($msg) {
    Write-Host "[ERROR] $msg" -ForegroundColor Red
    exit 1
}

$script:GitPath = $null
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if ($gitCmd) {
    $script:GitPath = $gitCmd.Source
} else {
    $candidates = @(
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe",
        "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $script:GitPath = $candidate
            break
        }
    }
}

if (-not $script:GitPath) {
    Fail "Git을 찾을 수 없습니다. Git 설치 후 터미널을 재시작하세요."
}

function GitCmd {
    param([Parameter(ValueFromRemainingArguments = $true)] [string[]]$Args)
    & $script:GitPath @Args
}

function RunGit($argsText, [string[]]$argsArray) {
    Write-Host "`n> git $argsText" -ForegroundColor Cyan
    GitCmd @argsArray
}

# 1) Git 동작 확인
try {
    GitCmd --version | Out-Null
} catch {
    Fail "Git 실행에 실패했습니다. 터미널 재시작 후 다시 시도하세요."
}

# 2) Git 저장소 확인
if (-not (Test-Path ".git")) {
    Fail "현재 폴더는 Git 저장소가 아닙니다. 먼저 'git init' 또는 저장소 클론을 진행하세요."
}

# 3) 원격 저장소 확인
$remote = (GitCmd remote) -join " "
if ($remote -notmatch "origin") {
    Fail "origin 원격 저장소가 없습니다. 'git remote add origin <repo-url>' 먼저 실행하세요."
}

# 4) 변경사항 확인
$status = GitCmd status --porcelain
if (-not $status) {
    Write-Host "변경사항이 없습니다. 업로드할 내용이 없습니다." -ForegroundColor Yellow
    exit 0
}

# 5) 커밋 메시지 자동 생성
if ([string]::IsNullOrWhiteSpace($Message)) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Message = "chore: auto upload ($timestamp)"
}

# 6) 브랜치 체크아웃 + 동기화
RunGit "checkout $Branch" @("checkout", $Branch)

if (-not $SkipPull) {
    RunGit "pull origin $Branch" @("pull", "origin", $Branch)
}

# 7) add / commit / push
RunGit "add ." @("add", ".")
RunGit "commit -m \"$Message\"" @("commit", "-m", $Message)
RunGit "push origin $Branch" @("push", "origin", $Branch)

Write-Host "`n완료: $Branch 브랜치로 업로드되었습니다." -ForegroundColor Green
