const { json, normalizeSlug, readBody, isAuthorized, loadProfile, saveProfile } = require("./_lib/card-store");

module.exports = async function handler(req, res) {
  try {
    if (req.method === "GET") {
      const slug = normalizeSlug(req.query.slug);
      const card = await loadProfile(slug);
      json(res, 200, { card });
      return;
    }

    if (req.method === "POST") {
      if (!isAuthorized(req)) {
        json(res, 401, { error: "관리자 권한이 필요합니다." });
        return;
      }
      const payload = readBody(req);
      const card = await saveProfile(payload);
      json(res, 200, { message: "저장되었습니다.", card });
      return;
    }

    json(res, 405, { error: "Method not allowed" });
  } catch (err) {
    json(res, 500, { error: err.message || "서버 오류" });
  }
};
