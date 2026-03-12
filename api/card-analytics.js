const { json, normalizeSlug, isAuthorized, loadAnalytics } = require("./_lib/card-store");

module.exports = async function handler(req, res) {
  try {
    if (req.method !== "GET") {
      json(res, 405, { error: "Method not allowed" });
      return;
    }
    if (!isAuthorized(req)) {
      json(res, 401, { error: "관리자 권한이 필요합니다." });
      return;
    }
    const slug = normalizeSlug(req.query.slug);
    const data = await loadAnalytics(slug);
    json(res, 200, data);
  } catch (err) {
    json(res, 500, { error: err.message || "서버 오류" });
  }
};
