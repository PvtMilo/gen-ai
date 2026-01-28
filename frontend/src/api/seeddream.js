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

export async function createJob(sessionId) {
  const res = await api.post("/jobs", { session_id: sessionId });
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
