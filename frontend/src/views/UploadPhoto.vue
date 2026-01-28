<script setup>
import { ref, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";
import CameraCapture from "../components/CameraCapture.vue";
import WebcamCapture from "../components/WebcamCapture.vue";

const router = useRouter();
const store = useSeedDreamStore();
const fileRef = ref(null);
const captureRef = ref(null);

const capturedPhotoUrl = ref(null);
const capturedPhotoFile = ref(null);
const captureError = ref(null);
const capturing = ref(false);
const uploadingManual = ref(false);
const uploadingCapture = ref(false);

const assetBase = (import.meta.env.VITE_ASSET_BASE || "http://127.0.0.1:8000").replace(/\/$/, "");

const photoSource = computed(() => store.photoSource || "camera");
const isCameraSource = computed(() => photoSource.value === "camera");
const isWebcamSource = computed(() => photoSource.value === "webcam");
const isManualSource = computed(() => photoSource.value === "manual");
const captureTitle = computed(() => (isWebcamSource.value ? "Webcam" : "Camera"));

const hasCapturedPhoto = computed(
  () => Boolean(capturedPhotoUrl.value || capturedPhotoFile.value),
);
const isCameraBusy = computed(() => capturing.value || uploadingCapture.value);

function ensureSession() {
  if (!store.session) {
    router.replace({ name: "Register" });
    return false;
  }
  if (!store.session.theme_id) {
    router.replace({ name: "ThemeSelection" });
    return false;
  }
  return true;
}

function resolvePhotoUrl(url) {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  const prefix = url.startsWith("/") ? "" : "/";
  return `${assetBase}${prefix}${url}`;
}

async function photoUrlToFile(photoUrl) {
  const targetUrl = resolvePhotoUrl(photoUrl);
  const res = await fetch(targetUrl);
  if (!res.ok) throw new Error(`Failed to fetch captured photo (${res.status})`);
  const blob = await res.blob();
  const cleanUrl = photoUrl.split("?")[0];
  const baseName = cleanUrl.split("/").pop();
  const extFromType = blob.type?.split("/")[1] || "jpg";
  const fileName =
    baseName && baseName.includes(".")
      ? baseName
      : `camera_${Date.now()}.${extFromType}`;
  return new File([blob], fileName, { type: blob.type || "image/jpeg" });
}

async function onUpload() {
  if (!ensureSession()) return;

  const file = fileRef.value?.files?.[0];
  if (!file) return alert("Pilih file dulu");

  uploadingManual.value = true;
  try {
    await store.uploadPhoto(file);
    router.push({ name: "Loading" });
  } catch (_) {
    // store.error sudah di-set
  } finally {
    uploadingManual.value = false;
  }
}

const goBack = () => router.push({ name: "ThemeSelection" });

const handleCapture = async () => {
  if (!captureRef.value?.takePhoto) return;
  capturing.value = true;
  captureError.value = null;
  try {
    await captureRef.value.takePhoto();
  } catch (err) {
    captureError.value = err?.message || "Gagal capture foto.";
  } finally {
    capturing.value = false;
  }
};

const handleRetake = () => {
  captureError.value = null;
  capturedPhotoUrl.value = null;
  capturedPhotoFile.value = null;
  captureRef.value?.retakeCamera();
};

const handleRetakeEvent = () => {
  captureError.value = null;
  capturedPhotoUrl.value = null;
  capturedPhotoFile.value = null;
};

const handleUsePhoto = async () => {
  if (!ensureSession()) return;
  if (!capturedPhotoUrl.value && !capturedPhotoFile.value) return;

  uploadingCapture.value = true;
  captureError.value = null;
  try {
    const file = capturedPhotoFile.value
      ? capturedPhotoFile.value
      : await photoUrlToFile(capturedPhotoUrl.value);
    await store.uploadPhoto(file);
    router.push({ name: "Loading" });
  } catch (err) {
    captureError.value = err?.message || "Upload gagal.";
  } finally {
    uploadingCapture.value = false;
  }
};

const handleCaptured = (payload) => {
  captureError.value = null;
  if (payload?.file) {
    capturedPhotoFile.value = payload.file;
    capturedPhotoUrl.value = null;
    return;
  }
  capturedPhotoUrl.value = payload?.photoUrl || null;
  capturedPhotoFile.value = null;
};

const handleCaptureError = (err) => {
  captureError.value = err?.message || "Gagal capture foto.";
};

watch(photoSource, () => {
  captureError.value = null;
  capturedPhotoUrl.value = null;
  capturedPhotoFile.value = null;
  capturing.value = false;
  uploadingCapture.value = false;
});
</script>

<template>
  <div class="page">
    <h1>Upload Photo</h1>

    <p v-if="store.error" class="error">{{ store.error }}</p>

    <section v-if="!isManualSource" class="camera-wrapper">
      <h2>{{ captureTitle }}</h2>

      <CameraCapture
        v-if="isCameraSource"
        ref="captureRef"
        @captured="handleCaptured"
        @retake="handleRetakeEvent"
        @error="handleCaptureError"
      />

      <WebcamCapture
        v-else-if="isWebcamSource"
        ref="captureRef"
        @captured="handleCaptured"
        @retake="handleRetakeEvent"
        @error="handleCaptureError"
      />

      <div class="camera-btn-wrapper">
        <button
          class="btn"
          :disabled="isCameraBusy"
          @click="hasCapturedPhoto ? handleRetake() : goBack()"
        >
          {{ hasCapturedPhoto ? "Retake" : "Back" }}
        </button>

        <button
          class="btn"
          :disabled="isCameraBusy"
          @click="hasCapturedPhoto ? handleUsePhoto() : handleCapture()"
        >
          {{
            hasCapturedPhoto
              ? uploadingCapture
                ? "Uploading..."
                : "Next"
              : capturing
                ? "Capturing..."
                : "Capture"
          }}
        </button>
      </div>

      <p v-if="captureError" class="error">{{ captureError }}</p>
    </section>

    <section v-if="isManualSource" class="manual-upload">
      <h2>Manual Upload</h2>
      <input type="file" ref="fileRef" accept="image/*" />
      <button @click="onUpload" :disabled="uploadingManual">
        {{ uploadingManual ? "Uploading..." : "Upload" }}
      </button>
    </section>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.camera-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.camera-btn-wrapper {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.manual-upload {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error {
  color: #c1121f;
}
</style>
