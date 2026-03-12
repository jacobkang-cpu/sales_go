const { json, readBody, saveEvent } = require("./_lib/card-store");

module.exports = async function handler(req, res) {
  try {
    if (req.method !== "POST") {
      json(res, 405, { error: "Method not allowed" });
      return;
    }
    const payload = readBody(req);
    await saveEvent(payload, req);
    json(res, 200, { ok: true });
  } catch (err) {
    json(res, 400, { error: err.message || "요청 처리 실패" });
  }
};
