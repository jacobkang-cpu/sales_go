from __future__ import annotations

import datetime as dt
import json
import os
import random
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

LOCK = threading.Lock()

DEMO_INQUIRIES: list[dict] = []
COMMUNITY_POSTS: list[dict] = [
    {
        "id": 1,
        "title": "2월 주간 리드 전환율 리포트",
        "author": "운영팀",
        "category": "차트업데이트",
        "content": "시연 문의 대비 계약 전환율이 전주 대비 3.2%p 상승했습니다.",
        "created_at": "2026-02-24 09:30",
    },
    {
        "id": 2,
        "title": "SNS 채널별 유입 비교",
        "author": "마케팅팀",
        "category": "분석",
        "content": "네이버 블로그와 인스타그램 유입 비중이 가장 높았습니다.",
        "created_at": "2026-02-25 08:50",
    },
]

# 최근 7개 구간의 샘플 지표 (예: 일자별 시연 문의 건수)
CHART_SERIES = [14, 19, 17, 22, 24, 21, 26]

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
      --accent-2: #14b8a6;
      --danger: #dc2626;
      --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }

    * {
      box-sizing: border-box;
    }

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

    .hero h1 {
      margin: 0;
      font-size: clamp(1.6rem, 2vw, 2.3rem);
      letter-spacing: -0.02em;
    }

    .hero p {
      margin: 14px 0 0;
      color: rgba(255, 255, 255, 0.92);
      max-width: 720px;
    }

    .hero-actions {
      margin-top: 18px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
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

    .btn:hover {
      transform: translateY(-1px);
      opacity: 0.95;
    }

    .btn-primary {
      background: #fff;
      color: #0f172a;
    }

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

    .panel h2 {
      margin: 0 0 10px;
      font-size: 1.1rem;
      letter-spacing: -0.01em;
    }

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

    .input,
    .textarea,
    .select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      font: inherit;
      background: #fff;
    }

    .textarea {
      min-height: 92px;
      resize: vertical;
    }

    .full {
      grid-column: 1 / -1;
    }

    .status {
      margin-top: 8px;
      font-size: 0.9rem;
      min-height: 1.2em;
    }

    .sns-grid {
      display: grid;
      gap: 10px;
    }

    .sns-card {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: linear-gradient(180deg, #fff, #f8fbff);
    }

    .sns-card strong {
      display: block;
      margin-bottom: 4px;
    }

    .sns-card a {
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }

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

    .bot {
      align-self: flex-start;
      background: #e8f1ff;
      border: 1px solid #c6ddff;
    }

    .user {
      align-self: flex-end;
      background: #ecfdf5;
      border: 1px solid #b7efd4;
    }

    .chat-input {
      margin-top: 10px;
      display: flex;
      gap: 8px;
    }

    .chat-input input {
      flex: 1;
    }

    .community-list {
      display: grid;
      gap: 10px;
      margin-top: 10px;
    }

    .post {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: #fff;
    }

    .post h4 {
      margin: 0;
      font-size: 1rem;
    }

    .meta {
      margin: 4px 0 8px;
      color: var(--sub);
      font-size: 0.85rem;
    }

    .chart-wrap {
      margin-top: 10px;
      display: grid;
      gap: 8px;
    }

    .bar-row {
      display: grid;
      grid-template-columns: 50px 1fr 36px;
      align-items: center;
      gap: 8px;
      font-size: 0.86rem;
    }

    .bar-bg {
      height: 10px;
      border-radius: 999px;
      background: #e5eefc;
      overflow: hidden;
    }

    .bar {
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      transition: width 380ms ease;
    }

    .tag {
      display: inline-block;
      font-size: 0.75rem;
      background: #eef6ff;
      color: #1d4ed8;
      padding: 3px 8px;
      border-radius: 999px;
      margin-left: 6px;
    }

    @keyframes rise {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @media (max-width: 920px) {
      .grid {
        grid-template-columns: 1fr;
      }

      .form-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>닥터팔레트 시연 문의 & 운영 커뮤니티 허브</h1>
      <p>
        닥터팔레트 도입 검토 병원을 위한 시연 문의 접수, SNS 채널 연결,
        FAQ 챗봇 응대, 차트 기반 커뮤니티 업데이트를 한 페이지에서 운영합니다.
      </p>
      <div class="hero-actions">
        <a href="#demo" class="btn btn-primary">시연 문의 접수</a>
        <a href="#community" class="btn btn-ghost">커뮤니티 바로가기</a>
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
        <h2>차트 모니터링</h2>
        <p class="sub">최근 7개 구간 시연 문의 추이 <span class="tag" id="updatedAt"></span></p>
        <div class="chart-wrap" id="chartWrap"></div>
      </section>
    </div>

    <section class="panel" style="margin-top: 16px;">
      <h2>커뮤니티 게시판</h2>
      <p class="sub">차트 관련 공지/분석 내용을 팀이 주기적으로 업데이트하는 공간입니다.</p>
      <form id="postForm" class="form-grid">
        <input class="input" name="title" placeholder="제목" required />
        <input class="input" name="author" placeholder="작성자" required />
        <select class="select" name="category" required>
          <option>차트업데이트</option>
          <option>분석</option>
          <option>운영공지</option>
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
    const initialChart = __CHART_JSON__;

    const faqMap = [
      { keys: ["가격", "비용", "요금"], answer: "병원 규모별 요금제가 다릅니다. 시연 문의를 남기면 맞춤 견적을 안내해드립니다." },
      { keys: ["기능", "차트", "분석"], answer: "접수/리드/전환 차트를 실시간으로 조회하고 팀별 성과를 비교할 수 있습니다." },
      { keys: ["기간", "도입", "설치"], answer: "평균 도입 기간은 1~2주이며, 데이터 연동 범위에 따라 조정됩니다." },
      { keys: ["문의", "상담", "데모"], answer: "상단 시연 문의 폼을 보내주시면 담당자가 영업일 기준 24시간 내 연락드립니다." }
    ];

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

    function renderChart(chart) {
      const wrap = document.getElementById("chartWrap");
      const updated = document.getElementById("updatedAt");
      const maxValue = Math.max(...chart.values, 1);
      wrap.innerHTML = "";
      chart.labels.forEach((label, idx) => {
        const value = chart.values[idx];
        const row = document.createElement("div");
        row.className = "bar-row";
        const ratio = (value / maxValue) * 100;
        row.innerHTML = `
          <span>${label}</span>
          <div class="bar-bg"><div class="bar" style="width:${ratio}%"></div></div>
          <strong>${value}</strong>
        `;
        wrap.appendChild(row);
      });
      updated.textContent = `업데이트: ${chart.updated_at}`;
    }

    async function refreshChart() {
      const res = await fetch("/api/chart");
      const data = await res.json();
      renderChart(data);
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
    renderChart(initialChart);
    setInterval(refreshChart, 30000);
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


def next_chart() -> dict:
    with LOCK:
        last = CHART_SERIES[-1]
        drift = random.randint(-3, 4)
        CHART_SERIES.append(max(3, last + drift))
        if len(CHART_SERIES) > 7:
            CHART_SERIES.pop(0)

        labels = [f"D-{6 - i}" for i in range(7)]
        return {
            "labels": labels,
            "values": CHART_SERIES[:],
            "updated_at": now_text(),
        }


def initial_chart() -> dict:
    labels = [f"D-{6 - i}" for i in range(7)]
    return {"labels": labels, "values": CHART_SERIES[:], "updated_at": now_text()}


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

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "ok", "time": now_text()})
            return

        if self.path in ["/", "/index.html"]:
            with LOCK:
                posts = COMMUNITY_POSTS[:]
            page = (
                HTML_PAGE.replace("__POSTS_JSON__", json.dumps(posts, ensure_ascii=False))
                .replace("__CHART_JSON__", json.dumps(initial_chart(), ensure_ascii=False))
            )
            self._send_html(page)
            return

        if self.path == "/api/chart":
            self._send_json(next_chart())
            return

        if self.path == "/api/community":
            with LOCK:
                posts = COMMUNITY_POSTS[:]
            self._send_json({"posts": posts})
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path == "/api/inquiry":
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

        if self.path == "/api/community":
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
        # 콘솔 로그를 줄여 데모 출력이 복잡해지지 않게 유지
        return


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Demo page running: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
