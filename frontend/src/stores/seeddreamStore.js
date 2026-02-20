import { defineStore } from "pinia";
import {
  getThemes,
  startSession,
  setTheme,
  uploadPhoto as uploadPhotoApi,
  uploadOverlay as uploadOverlayApi,
  createJob,
  getJob,
  getSession,
} from "../api/seeddream";

function extractErrorMessage(err, fallback = "UNKNOWN_ERROR") {
  const data = err?.response?.data;

  if (data?.detail) {
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail) && data.detail[0]?.msg) return data.detail[0].msg;
  }

  return err?.message || fallback;
}

function normalizeRunMode(mode) {
  const normalized = typeof mode === "string" ? mode.trim().toLowerCase() : "";
  return normalized === "debugging" ? "debugging" : "event";
}

export const useSeedDreamStore = defineStore("seeddream", {
  state: () => ({
    themes: [],
    session: null,
    job: null,
    photoSource: "webcam",
    runMode: "event",
    apiSource : "Native Byte",
    printerName: "",
    overlayUrl: null,
    overlayMeta: null,

    loadingThemes: false,
    loadingSession: false,
    loadingJob: false,

    cameraStream: null,   // MediaStream
    cameraReady: false,
    cameraError: null,

    error: null,
  }),

  actions: {
    hydrate() {
      try {
        const s = localStorage.getItem("sd_session");
        const j = localStorage.getItem("sd_job");
        const p = localStorage.getItem("sd_photo_source");
        const m = localStorage.getItem("sd_run_mode");
        const a = localStorage.getItem("sd_api_source");
        const pn = localStorage.getItem("sd_printer_name");
        const o = localStorage.getItem("sd_overlay_url");
        const om = localStorage.getItem("sd_overlay_meta");
        if (s) this.session = JSON.parse(s);
        if (j) this.job = JSON.parse(j);
        if (p) this.photoSource = p;
        if (m) this.runMode = normalizeRunMode(m);
        if (a) this.apiSource = a;
        if (pn) this.printerName = pn;
        if (o) this.overlayUrl = o;
        if (om) this.overlayMeta = JSON.parse(om);
      } catch (_) {}
    },

    persist() {
      try {
        localStorage.setItem("sd_session", JSON.stringify(this.session));
        localStorage.setItem("sd_job", JSON.stringify(this.job));
        localStorage.setItem("sd_photo_source", this.photoSource || "webcam");
        localStorage.setItem("sd_run_mode", this.runMode || "event");
        localStorage.setItem("sd_api_source", this.apiSource || "native");
        localStorage.setItem("sd_printer_name", this.printerName || "");
        localStorage.setItem("sd_overlay_url", this.overlayUrl || "");
        localStorage.setItem("sd_overlay_meta", JSON.stringify(this.overlayMeta || null));
      } catch (_) {}
    },

    clear() {
      this.themes = [];
      this.session = null;
      this.job = null;
      this.photoSource = "webcam";
      this.runMode = "event";
      this.printerName = "";
      this.overlayUrl = null;
      this.overlayMeta = null;
      this.error = null;
      localStorage.removeItem("sd_session");
      localStorage.removeItem("sd_job");
      localStorage.removeItem("sd_photo_source");
      localStorage.removeItem("sd_run_mode");
      localStorage.removeItem("sd_printer_name");
      localStorage.removeItem("sd_overlay_url");
      localStorage.removeItem("sd_overlay_meta");

      // optional: juga stop webcam kalau lagi nyala
      this.stopWebcam();
    },

    async loadThemes() {
      this.loadingThemes = true;
      this.error = null;
      try {
        this.themes = await getThemes();
        return this.themes;
      } catch (e) {
        this.error = extractErrorMessage(e, "LOAD_THEMES_FAILED");
        throw e;
      } finally {
        this.loadingThemes = false;
      }
    },

    async beginSession(payload) {
      this.loadingSession = true;
      this.error = null;
      try {
        this.session = await startSession(payload);
        this.persist();
        return this.session;
      } catch (e) {
        this.error = extractErrorMessage(e, "START_SESSION_FAILED");
        throw e;
      } finally {
        this.loadingSession = false;
      }
    },

    async refreshSession() {
      if (!this.session?.session_id) throw new Error("NO_SESSION");
      this.session = await getSession(this.session.session_id);
      this.persist();
      return this.session;
    },

    async chooseTheme(themeId) {
      if (!this.session?.session_id) throw new Error("NO_SESSION");
      this.error = null;
      try {
        this.session = await setTheme(this.session.session_id, themeId);
        this.persist();
        return this.session;
      } catch (e) {
        this.error = extractErrorMessage(e, "SET_THEME_FAILED");
        throw e;
      }
    },

    setPhotoSource(source) {
      const allowed = ["webcam", "camera", "manual"];
      this.photoSource = allowed.includes(source) ? source : "webcam";
      this.persist();
      return this.photoSource;
    },

    setRunMode(mode) {
      this.runMode = normalizeRunMode(mode);
      this.persist();
      return this.runMode;
    },

    setApiSource(source) {
      const allowed = ["native", "comfy"];
      this.apiSource = allowed.includes(source) ? source : "native";
      this.persist();
      return this.apiSource;
    },

    setPrinterName(name) {
      this.printerName = (name || "").trim();
      this.persist();
      return this.printerName;
    },

    setOverlay(overlayUrl, overlayMeta = null) {
      this.overlayUrl = overlayUrl || null;
      this.overlayMeta = overlayMeta || null;
      this.persist();
      return this.overlayUrl;
    },

    async uploadOverlay(file) {
      this.error = null;
      try {
        const uploaded = await uploadOverlayApi(file);
        this.overlayUrl = uploaded.overlay_url;
        this.overlayMeta = {
          width: uploaded.width,
          height: uploaded.height,
        };
        this.persist();
        return uploaded;
      } catch (e) {
        this.error = extractErrorMessage(e, "OVERLAY_UPLOAD_FAILED");
        throw e;
      }
    },

    async uploadPhoto(file) {
      if (!this.session?.session_id) throw new Error("NO_SESSION");
      this.error = null;

      try {
        this.session = await uploadPhotoApi(this.session.session_id, file);
        this.persist();
        return this.session;
      } catch (e) {
        this.error = extractErrorMessage(e, "UPLOAD_FAILED");
        throw e;
      }
    },

    async generate({ intervalMs = 1000, timeoutMs = 240000 } = {}) {
      if (!this.session?.session_id) throw new Error("NO_SESSION");
      this.loadingJob = true;
      this.error = null;

      try {
        const created = await createJob(
          this.session.session_id,
          this.runMode,
          this.overlayUrl,
        );
        this.job = created;
        this.persist();

        const started = Date.now();
        while (true) {
          const j = await getJob(created.job_id);
          this.job = j;
          this.persist();

          if (j.status === "done" || j.status === "failed") {
            if (this.session) this.session.latest_job = j;
            this.persist();
            return j;
          }

          if (Date.now() - started > timeoutMs) {
            const err = new Error("POLL_TIMEOUT");
            err.code = "POLL_TIMEOUT";
            throw err;
          }

          await new Promise((r) => setTimeout(r, intervalMs));
        }
      } catch (e) {
        this.error = extractErrorMessage(e, "GENERATE_FAILED");
        throw e;
      } finally {
        this.loadingJob = false;
      }
    },

    // ✅ pindahkan ke sini
    async warmupWebcam(constraints = { video: true, audio: false }) {
      this.cameraError = null;

      // kalau sudah ada stream dan masih hidup, reuse aja (biar instant)
      const hasLiveTrack =
        this.cameraStream?.getTracks?.().some((t) => t.readyState === "live");

      if (this.cameraStream && hasLiveTrack) {
        this.cameraReady = true;
        return this.cameraStream;
      }

      this.cameraReady = false;
      // bersihin stream lama (kalau ada)
      this.stopWebcam();

      try {
        if (!navigator?.mediaDevices?.getUserMedia) {
          throw new Error("getUserMedia not supported");
        }
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        this.cameraStream = stream;
        this.cameraReady = true;
        return stream;
      } catch (e) {
        this.cameraError = e?.message || "WEBCAM_FAILED";
        this.cameraReady = false;
        throw e;
      }
    },

    stopWebcam() {
      if (this.cameraStream?.getTracks) {
        this.cameraStream.getTracks().forEach((t) => t.stop());
      }
      this.cameraStream = null;
      this.cameraReady = false;
    },
  },
});
