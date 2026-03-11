from __future__ import annotations

import datetime as dt
import json
import mimetypes
import os
import sqlite3
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

LOCK = threading.Lock()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARD_PREFIX = "/card"
DB_PATH = os.path.join(BASE_DIR, "card_admin.db")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin1234")

DEFAULT_CARD_CONFIG = {
    "slug": "woojin",
    "name": "남우진",
    "headline": "애터미와 함께 노후 안정.",
    "tags": ["#성장파트너", "#성장동력"],
    "phone": "010-5429-9916",
    "email": "%%",
    "profile_subtitle": "파트너와 함께 성장합니다.",
    "news_label": "애터미 소식",
    "news_url": "https://www.atomy.kr/",
    "instagram_label": "인스타그램",
    "instagram_url": "https://www.instagram.com/",
    "image_data": "",
}

DEMO_INQUIRIES: list[dict] = []
COMMUNITY_POSTS: list[dict] = [
    {
        "id": 1,
        "title": "2월 주간 리드 전환율 리포트",
        "author": "운영팀",
        "category": "분석",
        "content": "시연 문의 대비 계약 전환율이 전주 대비 3.2%p 상승했습니다.",
        "created_at": "2026-02-24 09:30",
    },
    {
        "id": 2,
        "title": "SNS 채널별 유입 비교",
        "author": "마케팅팀",
        "category": "운영공지",
        "content": "네이버 블로그와 인스타그램 유입 비중이 가장 높았습니다.",
        "created_at": "2026-02-25 08:50",
    },
]

HTML_PAGE = r"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>닥터팔레트 시연 문의 허브</title>
  <style>
    :root {
      --bg: #f4f6fb;
      --panel: #ffffff;
      --text: #0f172a;
      --sub: #475569;
      --line: #d9e2f1;
      --accent: #0b6ee7;
      --danger: #dc2626;
      --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Pretendard", "SUIT", "Noto Sans KR", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 15% 10%, #dbeafe 0%, transparent 40%),
        radial-gradient(circle at 90% 5%, #ccfbf1 0%, transparent 30%),
        var(--bg);
      line-height: 1.55;
    }

    .wrap {
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
    }

    .hero {
      background: linear-gradient(120deg, #0f172a, #1d4ed8 60%, #0ea5e9);
      color: #fff;
      border-radius: 24px;
      padding: 32px;
      box-shadow: var(--shadow);
      animation: rise 450ms ease-out;
    }

    .hero h1 { margin: 0; font-size: clamp(1.6rem, 2vw, 2.3rem); }

    .hero p {
      margin: 14px 0 0;
      color: rgba(255, 255, 255, 0.92);
      max-width: 760px;
    }

    .hero-actions {
      margin-top: 18px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }

    .share-status {
      color: rgba(255, 255, 255, 0.9);
      font-size: 0.88rem;
      min-height: 1.2em;
    }

    .btn {
      border: none;
      border-radius: 12px;
      padding: 11px 14px;
      font-weight: 700;
      cursor: pointer;
      transition: transform 0.2s ease, opacity 0.2s ease;
      text-decoration: none;
      display: inline-block;
    }

    .btn:hover { transform: translateY(-1px); opacity: 0.95; }
    .btn-primary { background: #fff; color: #0f172a; }

    .btn-ghost {
      background: rgba(255, 255, 255, 0.14);
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.4);
    }

    .grid {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 16px;
      margin-top: 16px;
      align-items: start;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      padding: 18px;
      animation: fadeIn 500ms ease both;
    }

    .panel h2 { margin: 0 0 10px; font-size: 1.1rem; }

    .sub {
      color: var(--sub);
      font-size: 0.92rem;
      margin: 0 0 12px;
    }

    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .input, .textarea, .select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      font: inherit;
      background: #fff;
    }

    .textarea { min-height: 92px; resize: vertical; }
    .full { grid-column: 1 / -1; }

    .status {
      margin-top: 8px;
      font-size: 0.9rem;
      min-height: 1.2em;
    }

    .sns-grid { display: grid; gap: 10px; }

    .sns-card {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: linear-gradient(180deg, #fff, #f8fbff);
    }

    .sns-card strong { display: block; margin-bottom: 4px; }
    .sns-card a { color: var(--accent); text-decoration: none; font-weight: 600; }

    .chat-box {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px;
      background: #fcfdff;
      height: 280px;
      overflow: auto;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .msg {
      max-width: 86%;
      padding: 8px 10px;
      border-radius: 10px;
      font-size: 0.92rem;
      animation: fadeIn 220ms ease;
    }

    .bot { align-self: flex-start; background: #e8f1ff; border: 1px solid #c6ddff; }
    .user { align-self: flex-end; background: #ecfdf5; border: 1px solid #b7efd4; }

    .chat-input { margin-top: 10px; display: flex; gap: 8px; }
    .chat-input input { flex: 1; }

    .reddit-feed { display: grid; gap: 12px; }

    .reddit-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .reddit-tags { display: flex; flex-wrap: wrap; gap: 6px; }

    .chip {
      font-size: 0.75rem;
      background: #eef6ff;
      color: #1d4ed8;
      padding: 4px 8px;
      border-radius: 999px;
      border: 1px solid #d7e7ff;
    }

    .feed-grid { display: grid; gap: 10px; }

    .feed-item {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: linear-gradient(180deg, #ffffff, #f8fbff);
    }

    .feed-item strong { display: block; margin-bottom: 4px; font-size: 0.95rem; }
    .feed-meta { color: var(--sub); font-size: 0.82rem; margin-top: 4px; }

    .image-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }

    .image-card {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fff;
      min-height: 92px;
    }

    .community-list { display: grid; gap: 10px; margin-top: 10px; }

    .post {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: #fff;
    }

    .post h4 { margin: 0; font-size: 1rem; }

    .meta {
      margin: 4px 0 8px;
      color: var(--sub);
      font-size: 0.85rem;
    }

    @keyframes rise {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    @media (max-width: 920px) {
      .grid { grid-template-columns: 1fr; }
      .form-grid { grid-template-columns: 1fr; }
      .image-grid { grid-template-columns: 1fr 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>닥터팔레트 시연 문의 & 운영 커뮤니티 허브</h1>
      <p>
        닥터팔레트 도입 검토 병원을 위한 시연 문의 접수, SNS 채널 연결,
        FAQ 챗봇 응대, 레딧 스타일 커뮤니티 피드까지 한 페이지에서 운영합니다.
      </p>
      <div class="hero-actions">
        <a href="#demo" class="btn btn-primary">시연 문의 접수</a>
        <a href="#community" class="btn btn-ghost">커뮤니티 바로가기</a>
        <button class="btn btn-ghost" id="copyShareLink" type="button">공유 링크 복사</button>
        <span class="share-status" id="shareStatus"></span>
      </div>
    </section>

    <div class="grid">
      <section class="panel" id="demo">
        <h2>시연 문의 접수</h2>
        <p class="sub">입력 후 전송하면 서버 메모리에 저장됩니다. CRM/API 연동 전 단계 목업으로 사용 가능합니다.</p>
        <form id="demoForm" class="form-grid">
          <input class="input" name="hospital" placeholder="병원명" required />
          <input class="input" name="name" placeholder="담당자명" required />
          <input class="input" name="contact" placeholder="연락처" required />
          <input class="input" name="department" placeholder="진료 과목" required />
          <input class="input" type="date" name="preferred_date" required />
          <select class="select" name="source" required>
            <option value="">유입 채널 선택</option>
            <option>홈페이지</option>
            <option>네이버 블로그</option>
            <option>인스타그램</option>
            <option>카카오채널</option>
          </select>
          <textarea class="textarea full" name="memo" placeholder="요청사항"></textarea>
          <button class="btn btn-primary full" type="submit">시연 문의 보내기</button>
        </form>
        <div id="demoStatus" class="status"></div>
      </section>

      <section class="panel">
        <h2>SNS 유입 동선</h2>
        <p class="sub">채널별 랜딩/문의 유도를 위한 링크 블록입니다.</p>
        <div class="sns-grid">
          <div class="sns-card">
            <strong>네이버 블로그</strong>
            최신 도입 사례와 실사용 후기를 노출합니다.<br />
            <a href="#">채널 연결</a>
          </div>
          <div class="sns-card">
            <strong>인스타그램</strong>
            카드뉴스, 숏폼 영상 중심의 브랜딩/문의 유입.<br />
            <a href="#">채널 연결</a>
          </div>
          <div class="sns-card">
            <strong>카카오채널</strong>
            빠른 1:1 상담 및 이벤트 메시지 발송.<br />
            <a href="#">채널 연결</a>
          </div>
        </div>
      </section>
    </div>

    <div class="grid" style="margin-top: 16px;">
      <section class="panel">
        <h2>FAQ 챗봇</h2>
        <p class="sub">자주 묻는 질문을 키워드 기반으로 즉시 응답합니다.</p>
        <div class="chat-box" id="chatBox"></div>
        <div class="chat-input">
          <input class="input" id="chatInput" placeholder="예) 가격, 기능, 도입기간" />
          <button class="btn btn-primary" id="chatSend">전송</button>
        </div>
      </section>

      <section class="panel" id="community">
        <h2>커뮤니티 피드</h2>
        <p class="sub">레딧 게시판 스타일로 인기, 뉴스, 이미지 중심의 피드를 한 화면에서 확인합니다.</p>
        <div class="reddit-feed">
          <div class="reddit-head">
            <strong>오늘의 핫 토픽</strong>
            <div class="reddit-tags">
              <span class="chip">인기</span>
              <span class="chip">뉴스</span>
              <span class="chip">이미지</span>
            </div>
          </div>
          <div id="popularFeed" class="feed-grid"></div>
          <div id="newsFeed" class="feed-grid"></div>
          <div id="imageFeed" class="image-grid"></div>
        </div>
      </section>
    </div>

    <section class="panel" style="margin-top: 16px;">
      <h2>커뮤니티 게시판</h2>
      <p class="sub">팀이 직접 공지/분석 게시물을 올리는 운영용 게시판입니다.</p>
      <form id="postForm" class="form-grid">
        <input class="input" name="title" placeholder="제목" required />
        <input class="input" name="author" placeholder="작성자" required />
        <select class="select" name="category" required>
          <option>운영공지</option>
          <option>분석</option>
          <option>사례공유</option>
        </select>
        <input class="input" name="content" placeholder="내용 요약" required />
        <button class="btn btn-primary full" type="submit">게시물 등록</button>
      </form>
      <div id="postStatus" class="status"></div>
      <div class="community-list" id="communityList"></div>
    </section>
  </div>

  <script>
    const initialPosts = __POSTS_JSON__;

    const faqMap = [
      { keys: ["가격", "비용", "요금"], answer: "병원 규모별 요금제가 다릅니다. 시연 문의를 남기면 맞춤 견적을 안내해드립니다." },
      { keys: ["기능", "분석", "대시보드"], answer: "유입·상담·전환 단계를 한 번에 확인하고 팀별 성과를 비교할 수 있습니다." },
      { keys: ["기간", "도입", "설치"], answer: "평균 도입 기간은 1~2주이며, 데이터 연동 범위에 따라 조정됩니다." },
      { keys: ["문의", "상담", "데모"], answer: "상단 시연 문의 폼을 보내주시면 담당자가 영업일 기준 24시간 내 연락드립니다." }
    ];

    const redditFeed = {
      popular: [
        { title: "개원 병원 CRM 자동화 사례", meta: "인기 · 업보트 182" },
        { title: "진료과별 리드 전환 개선 체크리스트", meta: "인기 · 업보트 141" }
      ],
      news: [
        { title: "의료 SaaS 도입 트렌드 2026 상반기", meta: "뉴스 · 2시간 전" },
        { title: "병원 마케팅 개인정보 가이드 업데이트", meta: "뉴스 · 오늘" }
      ],
      images: [
        { title: "주간 성과 대시보드", tag: "이미지" },
        { title: "SNS 유입 흐름도", tag: "이미지" },
        { title: "도입 프로세스 맵", tag: "이미지" }
      ]
    };

    function appendMessage(type, text) {
      const box = document.getElementById("chatBox");
      const el = document.createElement("div");
      el.className = `msg ${type}`;
      el.textContent = text;
      box.appendChild(el);
      box.scrollTop = box.scrollHeight;
    }

    function answerFaq(input) {
      const q = input.toLowerCase();
      const hit = faqMap.find((item) => item.keys.some((k) => q.includes(k)));
      return hit
        ? hit.answer
        : "해당 질문은 상담원이 도와드릴 수 있어요. 시연 문의 폼에 남겨주시면 빠르게 연락드리겠습니다.";
    }

    function bindChatbot() {
      appendMessage("bot", "안녕하세요. 닥터팔레트 FAQ 챗봇입니다. 궁금한 내용을 입력해주세요.");
      const input = document.getElementById("chatInput");
      const send = document.getElementById("chatSend");
      const onSend = () => {
        const text = input.value.trim();
        if (!text) return;
        appendMessage("user", text);
        input.value = "";
        setTimeout(() => appendMessage("bot", answerFaq(text)), 160);
      };
      send.addEventListener("click", onSend);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") onSend();
      });
    }

    function renderRedditFeed() {
      const popularEl = document.getElementById("popularFeed");
      const newsEl = document.getElementById("newsFeed");
      const imageEl = document.getElementById("imageFeed");

      popularEl.innerHTML = redditFeed.popular
        .map((item) => `<article class="feed-item"><strong>${item.title}</strong><div class="feed-meta">${item.meta}</div></article>`)
        .join("");

      newsEl.innerHTML = redditFeed.news
        .map((item) => `<article class="feed-item"><strong>${item.title}</strong><div class="feed-meta">${item.meta}</div></article>`)
        .join("");

      imageEl.innerHTML = redditFeed.images
        .map((item) => `<article class="image-card"><strong>${item.title}</strong><div class="feed-meta">${item.tag}</div></article>`)
        .join("");
    }

    async function postFormJson(url, formEl) {
      const formData = new FormData(formEl);
      const payload = Object.fromEntries(formData.entries());
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      return res.json();
    }

    function renderPosts(posts) {
      const list = document.getElementById("communityList");
      list.innerHTML = "";
      posts.forEach((post) => {
        const item = document.createElement("article");
        item.className = "post";
        item.innerHTML = `
          <h4>${post.title}</h4>
          <div class="meta">${post.category} · ${post.author} · ${post.created_at}</div>
          <div>${post.content}</div>
        `;
        list.appendChild(item);
      });
    }

    async function copyShareLink() {
      const status = document.getElementById("shareStatus");
      const url = window.location.href;
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(url);
        } else {
          const temp = document.createElement("input");
          temp.value = url;
          document.body.appendChild(temp);
          temp.select();
          document.execCommand("copy");
          temp.remove();
        }
        status.textContent = "링크가 복사되었습니다.";
      } catch (err) {
        status.textContent = "복사 실패: 링크를 수동으로 복사해주세요.";
      }
      setTimeout(() => {
        status.textContent = "";
      }, 2500);
    }

    function bindForms() {
      const demoForm = document.getElementById("demoForm");
      const demoStatus = document.getElementById("demoStatus");
      demoForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
          const result = await postFormJson("/api/inquiry", demoForm);
          demoStatus.style.color = "#166534";
          demoStatus.textContent = result.message;
          demoForm.reset();
        } catch (err) {
          demoStatus.style.color = "var(--danger)";
          demoStatus.textContent = "전송에 실패했습니다.";
        }
      });

      const postForm = document.getElementById("postForm");
      const postStatus = document.getElementById("postStatus");
      postForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
          const result = await postFormJson("/api/community", postForm);
          renderPosts(result.posts);
          postStatus.style.color = "#166534";
          postStatus.textContent = "게시물이 등록되었습니다.";
          postForm.reset();
        } catch (err) {
          postStatus.style.color = "var(--danger)";
          postStatus.textContent = "등록에 실패했습니다.";
        }
      });
    }

    bindChatbot();
    bindForms();
    renderPosts(initialPosts);
    renderRedditFeed();
    document.getElementById("copyShareLink").addEventListener("click", copyShareLink);
  </script>
</body>
</html>
"""


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def parse_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length else b""
    ctype = handler.headers.get("Content-Type", "")

    if "application/json" in ctype:
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError:
            return {}

    if "application/x-www-form-urlencoded" in ctype:
        parsed = parse_qs(raw.decode("utf-8"))
        return {k: v[0] if v else "" for k, v in parsed.items()}

    return {}


def _db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _db_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS card_profiles (
              slug TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              headline TEXT NOT NULL,
              tags_json TEXT NOT NULL,
              phone TEXT NOT NULL,
              email TEXT NOT NULL,
              profile_subtitle TEXT NOT NULL,
              news_label TEXT NOT NULL,
              news_url TEXT NOT NULL,
              instagram_label TEXT NOT NULL,
              instagram_url TEXT NOT NULL,
              image_data TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS card_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              slug TEXT NOT NULL,
              event_type TEXT NOT NULL,
              event_target TEXT NOT NULL,
              page TEXT NOT NULL,
              session_id TEXT NOT NULL,
              ip TEXT NOT NULL,
              user_agent TEXT NOT NULL,
              referer TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _normalize_slug(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return DEFAULT_CARD_CONFIG["slug"]
    cleaned = "".join(ch for ch in raw if ch.isalnum() or ch in ("-", "_"))
    return cleaned or DEFAULT_CARD_CONFIG["slug"]


def _split_tags(value: str | list[str] | None) -> list[str]:
    if isinstance(value, list):
        tags = [str(item).strip() for item in value if str(item).strip()]
    else:
        src = str(value or "")
        tags = [item.strip() for item in src.replace("\n", ",").split(",") if item.strip()]
    if not tags:
        return DEFAULT_CARD_CONFIG["tags"][:]
    return tags[:8]


def _row_to_profile(row: sqlite3.Row) -> dict:
    try:
        tags = json.loads(row["tags_json"]) if row["tags_json"] else []
    except json.JSONDecodeError:
        tags = []
    return {
        "slug": row["slug"],
        "name": row["name"],
        "headline": row["headline"],
        "tags": tags if isinstance(tags, list) else [],
        "phone": row["phone"],
        "email": row["email"],
        "profile_subtitle": row["profile_subtitle"],
        "news_label": row["news_label"],
        "news_url": row["news_url"],
        "instagram_label": row["instagram_label"],
        "instagram_url": row["instagram_url"],
        "image_data": row["image_data"],
        "updated_at": row["updated_at"],
    }


def get_card_profile(slug: str) -> dict:
    slug = _normalize_slug(slug)
    with _db_conn() as conn:
        row = conn.execute("SELECT * FROM card_profiles WHERE slug = ?", (slug,)).fetchone()
        if row:
            return _row_to_profile(row)

        default = DEFAULT_CARD_CONFIG.copy()
        default["slug"] = slug
        now = now_text()
        conn.execute(
            """
            INSERT INTO card_profiles (
              slug, name, headline, tags_json, phone, email, profile_subtitle,
              news_label, news_url, instagram_label, instagram_url, image_data, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                default["slug"],
                default["name"],
                default["headline"],
                json.dumps(default["tags"], ensure_ascii=False),
                default["phone"],
                default["email"],
                default["profile_subtitle"],
                default["news_label"],
                default["news_url"],
                default["instagram_label"],
                default["instagram_url"],
                default["image_data"],
                now,
            ),
        )
        conn.commit()
        return {**default, "updated_at": now}


def save_card_profile(slug: str, payload: dict) -> dict:
    current = get_card_profile(slug)
    merged = {
        **current,
        "slug": _normalize_slug(payload.get("slug", current["slug"])),
        "name": str(payload.get("name", current["name"])).strip() or current["name"],
        "headline": str(payload.get("headline", current["headline"])).strip() or current["headline"],
        "tags": _split_tags(payload.get("tags", current["tags"])),
        "phone": str(payload.get("phone", current["phone"])).strip() or current["phone"],
        "email": str(payload.get("email", current["email"])).strip() or current["email"],
        "profile_subtitle": str(payload.get("profile_subtitle", current["profile_subtitle"])).strip()
        or current["profile_subtitle"],
        "news_label": str(payload.get("news_label", current["news_label"])).strip() or current["news_label"],
        "news_url": str(payload.get("news_url", current["news_url"])).strip() or current["news_url"],
        "instagram_label": str(payload.get("instagram_label", current["instagram_label"])).strip()
        or current["instagram_label"],
        "instagram_url": str(payload.get("instagram_url", current["instagram_url"])).strip()
        or current["instagram_url"],
        "image_data": str(payload.get("image_data", current["image_data"])).strip() or current["image_data"],
        "updated_at": now_text(),
    }

    with _db_conn() as conn:
        conn.execute(
            """
            INSERT INTO card_profiles (
              slug, name, headline, tags_json, phone, email, profile_subtitle,
              news_label, news_url, instagram_label, instagram_url, image_data, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
              name = excluded.name,
              headline = excluded.headline,
              tags_json = excluded.tags_json,
              phone = excluded.phone,
              email = excluded.email,
              profile_subtitle = excluded.profile_subtitle,
              news_label = excluded.news_label,
              news_url = excluded.news_url,
              instagram_label = excluded.instagram_label,
              instagram_url = excluded.instagram_url,
              image_data = excluded.image_data,
              updated_at = excluded.updated_at
            """,
            (
                merged["slug"],
                merged["name"],
                merged["headline"],
                json.dumps(merged["tags"], ensure_ascii=False),
                merged["phone"],
                merged["email"],
                merged["profile_subtitle"],
                merged["news_label"],
                merged["news_url"],
                merged["instagram_label"],
                merged["instagram_url"],
                merged["image_data"],
                merged["updated_at"],
            ),
        )
        conn.commit()
    return merged


def save_card_event(
    *,
    slug: str,
    event_type: str,
    event_target: str,
    page: str,
    session_id: str,
    ip: str,
    user_agent: str,
    referer: str,
) -> None:
    with _db_conn() as conn:
        conn.execute(
            """
            INSERT INTO card_events (
              slug, event_type, event_target, page, session_id, ip, user_agent, referer, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _normalize_slug(slug),
                event_type.strip()[:60],
                event_target.strip()[:120],
                page.strip()[:120],
                session_id.strip()[:120],
                ip.strip()[:120],
                user_agent.strip()[:400],
                referer.strip()[:400],
                now_text(),
            ),
        )
        conn.commit()


def get_card_analytics(slug: str) -> dict:
    slug = _normalize_slug(slug)
    with _db_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM card_events WHERE slug = ?", (slug,)).fetchone()[0]
        views_card = conn.execute(
            "SELECT COUNT(*) FROM card_events WHERE slug = ? AND event_type = 'view_card'", (slug,)
        ).fetchone()[0]
        views_profile = conn.execute(
            "SELECT COUNT(*) FROM card_events WHERE slug = ? AND event_type = 'view_profile'", (slug,)
        ).fetchone()[0]
        total_clicks = conn.execute(
            "SELECT COUNT(*) FROM card_events WHERE slug = ? AND event_type LIKE 'click_%'", (slug,)
        ).fetchone()[0]

        target_rows = conn.execute(
            """
            SELECT event_target, COUNT(*) AS cnt
            FROM card_events
            WHERE slug = ? AND event_type LIKE 'click_%'
            GROUP BY event_target
            ORDER BY cnt DESC
            """,
            (slug,),
        ).fetchall()
        clicks_by_target = {row["event_target"] or "unknown": row["cnt"] for row in target_rows}

        visitors_rows = conn.execute(
            """
            SELECT
              session_id,
              ip,
              user_agent,
              MIN(created_at) AS first_seen,
              MAX(created_at) AS last_seen,
              COUNT(*) AS events
            FROM card_events
            WHERE slug = ?
            GROUP BY session_id, ip, user_agent
            ORDER BY last_seen DESC
            LIMIT 100
            """,
            (slug,),
        ).fetchall()
        visitors = [
            {
                "session_id": row["session_id"],
                "ip": row["ip"],
                "user_agent": row["user_agent"],
                "first_seen": row["first_seen"],
                "last_seen": row["last_seen"],
                "events": row["events"],
            }
            for row in visitors_rows
        ]

        recent_rows = conn.execute(
            """
            SELECT created_at, event_type, event_target, page, session_id, ip, referer
            FROM card_events
            WHERE slug = ?
            ORDER BY id DESC
            LIMIT 100
            """,
            (slug,),
        ).fetchall()
        recent_events = [dict(row) for row in recent_rows]

    click_rate = round((total_clicks / views_card) * 100, 1) if views_card else 0.0
    return {
        "slug": slug,
        "summary": {
            "total_events": total,
            "views_card": views_card,
            "views_profile": views_profile,
            "total_clicks": total_clicks,
            "click_rate_percent": click_rate,
            "clicks_by_target": clicks_by_target,
        },
        "visitors": visitors,
        "recent_events": recent_events,
    }


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = HTTPStatus.OK) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static_file(self, path: str) -> bool:
        """명함 페이지용 정적 파일 서빙. path는 BASE_DIR 기준 상대경로."""
        if ".." in path or path.startswith("/"):
            return False
        file_path = os.path.join(BASE_DIR, path)
        if not os.path.isfile(file_path):
            return False
        try:
            with open(file_path, "rb") as f:
                body = f.read()
        except OSError:
            return False
        content_type, _ = mimetypes.guess_type(path)
        content_type = content_type or "application/octet-stream"
        if path.endswith(".html"):
            content_type = "text/html; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return True

    def _client_ip(self) -> str:
        forwarded = self.headers.get("X-Forwarded-For", "").strip()
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = self.headers.get("X-Real-IP", "").strip()
        if real_ip:
            return real_ip
        if self.client_address and self.client_address[0]:
            return self.client_address[0]
        return "unknown"

    def _is_admin(self) -> bool:
        token = self.headers.get("X-Admin-Token", "").strip()
        return bool(token) and token == ADMIN_TOKEN

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path_raw = parsed.path
        query = parse_qs(parsed.query)

        if path_raw == "/health":
            self._send_json({"status": "ok", "time": now_text()})
            return

        if path_raw in ["/admin", "/admin.html"]:
            if self._serve_static_file("admin.html"):
                return

        if path_raw in ["/dashboard", "/dashboard.html"]:
            if self._serve_static_file("dashboard.html"):
                return

        if path_raw == "/api/card-config":
            slug = _normalize_slug(query.get("slug", [DEFAULT_CARD_CONFIG["slug"]])[0])
            self._send_json({"card": get_card_profile(slug)})
            return

        if path_raw == "/api/card-analytics":
            if not self._is_admin():
                self._send_json({"error": "관리자 권한이 필요합니다."}, status=HTTPStatus.UNAUTHORIZED)
                return
            slug = _normalize_slug(query.get("slug", [DEFAULT_CARD_CONFIG["slug"]])[0])
            self._send_json(get_card_analytics(slug))
            return

        # 디지털 명함: /card, /card/, /card/index.html, /card/profile.html, /card/style.css 등
        if path_raw == CARD_PREFIX or path_raw == CARD_PREFIX + "/":
            if self._serve_static_file("index.html"):
                return
        if path_raw.startswith(CARD_PREFIX + "/"):
            sub = path_raw[len(CARD_PREFIX) + 1 :].lstrip("/")
            if sub in ("", "index.html"):
                if self._serve_static_file("index.html"):
                    return
            elif self._serve_static_file(sub):
                return

        if path_raw in ["/", "/index.html"]:
            with LOCK:
                posts = COMMUNITY_POSTS[:]
            page = HTML_PAGE.replace("__POSTS_JSON__", json.dumps(posts, ensure_ascii=False))
            self._send_html(page)
            return

        if path_raw == "/api/community":
            with LOCK:
                posts = COMMUNITY_POSTS[:]
            self._send_json({"posts": posts})
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path_raw = urlparse(self.path).path

        if path_raw == "/api/card-config":
            if not self._is_admin():
                self._send_json({"error": "관리자 권한이 필요합니다."}, status=HTTPStatus.UNAUTHORIZED)
                return
            payload = parse_body(self)
            slug = _normalize_slug(payload.get("slug"))
            profile = save_card_profile(slug, payload)
            self._send_json({"message": "저장되었습니다.", "card": profile})
            return

        if path_raw == "/api/card-event":
            payload = parse_body(self)
            event_type = str(payload.get("event_type", "")).strip()
            if not event_type:
                self._send_json({"error": "event_type 값이 필요합니다."}, status=HTTPStatus.BAD_REQUEST)
                return
            save_card_event(
                slug=_normalize_slug(payload.get("slug")),
                event_type=event_type,
                event_target=str(payload.get("event_target", "")).strip(),
                page=str(payload.get("page", "")).strip(),
                session_id=str(payload.get("session_id", "")).strip(),
                ip=self._client_ip(),
                user_agent=self.headers.get("User-Agent", ""),
                referer=self.headers.get("Referer", ""),
            )
            self._send_json({"ok": True})
            return

        if path_raw == "/api/inquiry":
            payload = parse_body(self)
            required = ["hospital", "name", "contact", "department", "preferred_date", "source"]
            if any(not str(payload.get(key, "")).strip() for key in required):
                self._send_json({"error": "필수 값이 누락되었습니다."}, status=HTTPStatus.BAD_REQUEST)
                return

            with LOCK:
                DEMO_INQUIRIES.append(
                    {
                        "hospital": payload.get("hospital", "").strip(),
                        "name": payload.get("name", "").strip(),
                        "contact": payload.get("contact", "").strip(),
                        "department": payload.get("department", "").strip(),
                        "preferred_date": payload.get("preferred_date", "").strip(),
                        "source": payload.get("source", "").strip(),
                        "memo": payload.get("memo", "").strip(),
                        "created_at": now_text(),
                    }
                )
            self._send_json({"message": "시연 문의가 접수되었습니다. 담당자가 빠르게 연락드리겠습니다."})
            return

        if path_raw == "/api/community":
            payload = parse_body(self)
            required = ["title", "author", "content", "category"]
            if any(not str(payload.get(key, "")).strip() for key in required):
                self._send_json({"error": "필수 값이 누락되었습니다."}, status=HTTPStatus.BAD_REQUEST)
                return

            with LOCK:
                new_post = {
                    "id": (COMMUNITY_POSTS[-1]["id"] + 1) if COMMUNITY_POSTS else 1,
                    "title": payload.get("title", "").strip(),
                    "author": payload.get("author", "").strip(),
                    "category": payload.get("category", "").strip(),
                    "content": payload.get("content", "").strip(),
                    "created_at": now_text(),
                }
                COMMUNITY_POSTS.insert(0, new_post)
                posts = COMMUNITY_POSTS[:]

            self._send_json({"message": "등록 완료", "posts": posts})
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:
        return


def run() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Demo page running: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
