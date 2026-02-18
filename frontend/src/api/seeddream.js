import { api } from "./client";

export async function getThemes() {
  const res = await api.get("/themes");
  return res.data; // array
}

export async function startSession({ name, email, phone }) {
  const res = await api.post("/sessions/start", { name, email, phone });
  return res.data; // SessionOut
}

export async function getSession(sessionId) {
  const res = await api.get(`/sessions/${sessionId}`);
  return res.data; // SessionOut
}

export async function setTheme(sessionId, theme_id) {
  const res = await api.patch(`/sessions/${sessionId}/theme`, { theme_id });
  return res.data; // SessionOut
}

export async function uploadPhoto(sessionId, file) {
  const form = new FormData();
  form.append("file", file);

  const res = await api.post(`/sessions/${sessionId}/upload`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data; // SessionOut
}

export async function uploadOverlay(file) {
  const form = new FormData();
  form.append("file", file);

  const res = await api.post("/settings/overlay", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data; // { overlay_url, width, height }
}

export async function getPrinters() {
  const res = await api.get("/printer/devices");
  return res.data; // { printers: [{ name, is_default }], detected_on, error_message }
}

export async function createJob(sessionId, mode = "event", overlayUrl = null) {
  const res = await api.post("/jobs", {
    session_id: sessionId,
    mode,
    overlay_url: overlayUrl,
  });
  return res.data; // JobOut
}

export async function getJob(jobId) {
  const res = await api.get(`/jobs/${jobId}`);
  return res.data; // JobOut
}

export async function getGallery({ limit = 100 } = {}) {
  const res = await api.get("/gallery", { params: { limit } });
  return res.data; // [{ id, url }]
}

// polling helper
export async function pollJob(jobId, { intervalMs = 1000, timeoutMs = 180000 } = {}) {
  const started = Date.now();

  while (true) {
    const job = await getJob(jobId);

    if (job.status === "done" || job.status === "failed") return job;

    if (Date.now() - started > timeoutMs) {
      const err = new Error("POLL_TIMEOUT");
      err.code = "POLL_TIMEOUT";
      throw err;
    }

    await new Promise((r) => setTimeout(r, intervalMs));
  }
}
