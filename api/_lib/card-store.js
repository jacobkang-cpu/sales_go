const DEFAULT_CARD_CONFIG = {
  slug: "woojin",
  name: "남우진",
  headline: "애터미와 함께 노후 안정.",
  tags: ["#성장파트너", "#성장동력"],
  phone: "010-5429-9916",
  email: "%%",
  profile_subtitle: "파트너와 함께 성장합니다.",
  news_label: "애터미 소식",
  news_url: "https://www.atomy.kr/",
  instagram_label: "인스타그램",
  instagram_url: "https://www.instagram.com/",
  image_data: "",
  updated_at: "",
};

function json(res, status, payload) {
  res.status(status).setHeader("Content-Type", "application/json; charset=utf-8");
  res.send(JSON.stringify(payload));
}

function normalizeSlug(value) {
  const raw = String(value || "").trim().toLowerCase();
  if (!raw) return DEFAULT_CARD_CONFIG.slug;
  const cleaned = raw.replace(/[^a-z0-9_-]/g, "");
  return cleaned || DEFAULT_CARD_CONFIG.slug;
}

function parseTags(value) {
  if (Array.isArray(value)) {
    const tags = value.map((item) => String(item).trim()).filter(Boolean);
    return tags.length ? tags.slice(0, 8) : DEFAULT_CARD_CONFIG.tags.slice();
  }
  const src = String(value || "");
  const tags = src
    .replace(/\n/g, ",")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  return tags.length ? tags.slice(0, 8) : DEFAULT_CARD_CONFIG.tags.slice();
}

function readBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  if (typeof req.body === "string") {
    try {
      return JSON.parse(req.body);
    } catch (_err) {
      return {};
    }
  }
  return {};
}

function getEnv() {
  const url = process.env.SUPABASE_URL || "";
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
  if (!url || !key) {
    throw new Error("SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY 환경변수가 필요합니다.");
  }
  return { url: url.replace(/\/$/, ""), key };
}

function getAdminToken() {
  return process.env.ADMIN_TOKEN || "admin1234";
}

function isAuthorized(req) {
  const token = String(req.headers["x-admin-token"] || "").trim();
  return token && token === getAdminToken();
}

function getClientIp(req) {
  const xff = String(req.headers["x-forwarded-for"] || "").trim();
  if (xff) return xff.split(",")[0].trim();
  const real = String(req.headers["x-real-ip"] || "").trim();
  if (real) return real;
  if (req.socket && req.socket.remoteAddress) return String(req.socket.remoteAddress);
  return "unknown";
}

async function supabaseFetch(path, options = {}) {
  const { url, key } = getEnv();
  const headers = {
    apikey: key,
    Authorization: `Bearer ${key}`,
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  const res = await fetch(`${url}/rest/v1/${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body,
  });
  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (_err) {
      data = text;
    }
  }
  return { ok: res.ok, status: res.status, headers: res.headers, data };
}

function profileFromRow(row = {}) {
  const tags = Array.isArray(row.tags) ? row.tags : parseTags(row.tags);
  return {
    slug: normalizeSlug(row.slug || DEFAULT_CARD_CONFIG.slug),
    name: String(row.name || DEFAULT_CARD_CONFIG.name),
    headline: String(row.headline || DEFAULT_CARD_CONFIG.headline),
    tags,
    phone: String(row.phone || DEFAULT_CARD_CONFIG.phone),
    email: String(row.email || DEFAULT_CARD_CONFIG.email),
    profile_subtitle: String(row.profile_subtitle || DEFAULT_CARD_CONFIG.profile_subtitle),
    news_label: String(row.news_label || DEFAULT_CARD_CONFIG.news_label),
    news_url: String(row.news_url || DEFAULT_CARD_CONFIG.news_url),
    instagram_label: String(row.instagram_label || DEFAULT_CARD_CONFIG.instagram_label),
    instagram_url: String(row.instagram_url || DEFAULT_CARD_CONFIG.instagram_url),
    image_data: String(row.image_data || DEFAULT_CARD_CONFIG.image_data),
    updated_at: String(row.updated_at || ""),
  };
}

async function loadProfile(slug) {
  const normalized = normalizeSlug(slug);
  const query = `card_profiles?slug=eq.${encodeURIComponent(normalized)}&select=*`;
  const result = await supabaseFetch(query);
  if (!result.ok) {
    throw new Error(typeof result.data === "string" ? result.data : JSON.stringify(result.data));
  }
  const list = Array.isArray(result.data) ? result.data : [];
  if (!list.length) return { ...DEFAULT_CARD_CONFIG, slug: normalized };
  return profileFromRow(list[0]);
}

function buildMergedProfile(current, payload) {
  const base = current || DEFAULT_CARD_CONFIG;
  const slug = normalizeSlug(payload.slug || base.slug);
  return {
    slug,
    name: String(payload.name || base.name || DEFAULT_CARD_CONFIG.name).trim() || DEFAULT_CARD_CONFIG.name,
    headline:
      String(payload.headline || base.headline || DEFAULT_CARD_CONFIG.headline).trim() ||
      DEFAULT_CARD_CONFIG.headline,
    tags: parseTags(payload.tags || base.tags),
    phone:
      String(payload.phone || base.phone || DEFAULT_CARD_CONFIG.phone).trim() || DEFAULT_CARD_CONFIG.phone,
    email:
      String(payload.email || base.email || DEFAULT_CARD_CONFIG.email).trim() || DEFAULT_CARD_CONFIG.email,
    profile_subtitle:
      String(payload.profile_subtitle || base.profile_subtitle || DEFAULT_CARD_CONFIG.profile_subtitle).trim() ||
      DEFAULT_CARD_CONFIG.profile_subtitle,
    news_label:
      String(payload.news_label || base.news_label || DEFAULT_CARD_CONFIG.news_label).trim() ||
      DEFAULT_CARD_CONFIG.news_label,
    news_url:
      String(payload.news_url || base.news_url || DEFAULT_CARD_CONFIG.news_url).trim() ||
      DEFAULT_CARD_CONFIG.news_url,
    instagram_label:
      String(payload.instagram_label || base.instagram_label || DEFAULT_CARD_CONFIG.instagram_label).trim() ||
      DEFAULT_CARD_CONFIG.instagram_label,
    instagram_url:
      String(payload.instagram_url || base.instagram_url || DEFAULT_CARD_CONFIG.instagram_url).trim() ||
      DEFAULT_CARD_CONFIG.instagram_url,
    image_data: String(payload.image_data || base.image_data || "").trim(),
    updated_at: new Date().toISOString(),
  };
}

async function saveProfile(payload) {
  const slug = normalizeSlug(payload.slug);
  const current = await loadProfile(slug);
  const merged = buildMergedProfile(current, payload);
  const result = await supabaseFetch("card_profiles?on_conflict=slug&select=*", {
    method: "POST",
    headers: { Prefer: "resolution=merge-duplicates,return=representation" },
    body: JSON.stringify([merged]),
  });
  if (!result.ok) {
    throw new Error(typeof result.data === "string" ? result.data : JSON.stringify(result.data));
  }
  const list = Array.isArray(result.data) ? result.data : [];
  return profileFromRow(list[0] || merged);
}

async function saveEvent(payload, req) {
  const eventType = String(payload.event_type || "").trim();
  if (!eventType) throw new Error("event_type 값이 필요합니다.");

  const row = {
    slug: normalizeSlug(payload.slug),
    event_type: eventType.slice(0, 60),
    event_target: String(payload.event_target || "").trim().slice(0, 120),
    page: String(payload.page || "").trim().slice(0, 120),
    session_id: String(payload.session_id || "").trim().slice(0, 120),
    ip: getClientIp(req).slice(0, 120),
    user_agent: String(req.headers["user-agent"] || "").slice(0, 500),
    referer: String(req.headers.referer || "").slice(0, 500),
    created_at: new Date().toISOString(),
  };
  const result = await supabaseFetch("card_events", {
    method: "POST",
    headers: { Prefer: "return=minimal" },
    body: JSON.stringify(row),
  });
  if (!result.ok) {
    throw new Error(typeof result.data === "string" ? result.data : JSON.stringify(result.data));
  }
  return true;
}

function formatVisitors(rows) {
  const map = new Map();
  for (const row of rows) {
    const key = `${row.session_id || ""}|${row.ip || ""}|${row.user_agent || ""}`;
    const found = map.get(key);
    if (!found) {
      map.set(key, {
        session_id: row.session_id || "",
        ip: row.ip || "",
        user_agent: row.user_agent || "",
        first_seen: row.created_at || "",
        last_seen: row.created_at || "",
        events: 1,
      });
      continue;
    }
    found.events += 1;
    if (row.created_at && row.created_at < found.first_seen) found.first_seen = row.created_at;
    if (row.created_at && row.created_at > found.last_seen) found.last_seen = row.created_at;
  }
  return Array.from(map.values())
    .sort((a, b) => String(b.last_seen).localeCompare(String(a.last_seen)))
    .slice(0, 100);
}

function summarize(rows) {
  const summary = {
    total_events: rows.length,
    views_card: 0,
    views_profile: 0,
    total_clicks: 0,
    click_rate_percent: 0,
    clicks_by_target: {},
  };

  for (const row of rows) {
    const type = String(row.event_type || "");
    const target = String(row.event_target || "unknown");
    if (type === "view_card") summary.views_card += 1;
    if (type === "view_profile") summary.views_profile += 1;
    if (type.startsWith("click_")) {
      summary.total_clicks += 1;
      summary.clicks_by_target[target] = (summary.clicks_by_target[target] || 0) + 1;
    }
  }

  if (summary.views_card > 0) {
    summary.click_rate_percent = Math.round((summary.total_clicks / summary.views_card) * 1000) / 10;
  }
  return summary;
}

async function loadAnalytics(slug) {
  const normalized = normalizeSlug(slug);
  const query =
    "card_events?" +
    `slug=eq.${encodeURIComponent(normalized)}` +
    "&select=event_type,event_target,page,session_id,ip,user_agent,referer,created_at" +
    "&order=created_at.desc" +
    "&limit=10000";
  const result = await supabaseFetch(query);
  if (!result.ok) {
    throw new Error(typeof result.data === "string" ? result.data : JSON.stringify(result.data));
  }
  const rows = Array.isArray(result.data) ? result.data : [];
  return {
    slug: normalized,
    summary: summarize(rows),
    visitors: formatVisitors(rows),
    recent_events: rows.slice(0, 100),
    note:
      rows.length >= 10000
        ? "최근 10,000개 이벤트 기준으로 집계되었습니다. 더 오래된 데이터는 별도 집계 로직이 필요합니다."
        : "",
  };
}

module.exports = {
  DEFAULT_CARD_CONFIG,
  json,
  normalizeSlug,
  readBody,
  isAuthorized,
  loadProfile,
  saveProfile,
  saveEvent,
  loadAnalytics,
};
