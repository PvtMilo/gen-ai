import { api } from "./client";

export async function getThemes() {
  const res = await api.get("/themes");
  console.log(res.data)
  return res.data; // array
}

export async function getThemesInternal() {
  const res = await api.get("/themes/internal");
  console.log(res.data)
  return res.data; // array with prompt & negative_prompt
}

export async function getThemeInternalById(themeId) {
  const res = await api.get(`/themes/internal/${encodeURIComponent(themeId)}`);
  return res.data; // single theme with prompt & negative_prompt
}

export async function createTheme(formData) {
  const res = await api.post("/themes", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function updateTheme(themeId, formData) {
  const res = await api.patch(`/themes/${encodeURIComponent(themeId)}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function deleteTheme(themeId) {
  await api.delete(`/themes/${encodeURIComponent(themeId)}`);
}

export async function getDriveStatus() {
  const res = await api.get("/drive/status");
  return res.data;
}

export async function uploadDriveForJob(jobId, { force = false } = {}) {
  const res = await api.post(`/drive/upload-job/${encodeURIComponent(jobId)}`, null, {
    params: { force },
  });
  return res.data;
}

export async function getTokenEstimatorReport(startDate, endDate) {
  const res = await api.get("/token-estimator/report", {
    params: { start_date: startDate, end_date: endDate },
  });
  return res.data;
}

export async function exportTokenEstimatorCsv(startDate, endDate) {
  const res = await api.get("/token-estimator/export.csv", {
    params: { start_date: startDate, end_date: endDate },
    responseType: "blob",
  });
  return res.data;
}

export async function previewEventDelete(startDate, endDate, password) {
  const res = await api.post("/event-maintenance/preview-delete", {
    start_date: startDate,
    end_date: endDate,
    password,
  });
  return res.data;
}

export async function executeEventDelete(startDate, endDate, password) {
  const res = await api.post("/event-maintenance/execute-delete", {
    start_date: startDate,
    end_date: endDate,
    password,
  });
  return res.data;
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
