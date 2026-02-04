<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from "vue";

const props = defineProps({
  externalStream: { type: Object, default: null }, // MediaStream dari store
  autoStart: { type: Boolean, default: true },     // fallback kalau externalStream null
});

const emit = defineEmits(["captured", "retake", "error"]);

const videoDom = ref(null);
const stream = ref(null);
const previewUrl = ref(null);

const stopInternal = () => {
  // hanya stop stream yang dibuat INTERNAL oleh komponen
  if (stream.value && stream.value !== props.externalStream) {
    stream.value.getTracks().forEach((t) => t.stop());
  }
  stream.value = null;
};

const attachToVideo = async () => {
  await nextTick();
  const v = videoDom.value;
  if (!v || !stream.value) return;

  v.srcObject = stream.value;

  // tunggu metadata biar videoWidth/videoHeight siap
  await new Promise((resolve) => {
    if (v.readyState >= 1) return resolve(); // HAVE_METADATA
    v.onloadedmetadata = () => resolve();
  });

  await v.play?.().catch(() => {});
};

const startInternal = async () => {
  try {
    const s = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    stream.value = s;
    await attachToVideo();
  } catch (e) {
    emit("error", e);
  }
};

// kalau externalStream berubah / baru datang, attach ulang
watch(
  () => props.externalStream,
  async (s) => {
    if (s) {
      stream.value = s;
      await attachToVideo();
    }
  },
  { immediate: true },
);

onMounted(async () => {
  // kalau ada externalStream, watch immediate sudah attach
  if (!props.externalStream && props.autoStart) {
    await startInternal();
  } else if (props.externalStream) {
    // safety: attach juga dari mounted
    stream.value = props.externalStream;
    await attachToVideo();
  }
});

const takePhoto = async () => {
  try {
    const v = videoDom.value;
    if (!v || !stream.value) throw new Error("Webcam belum siap.");

    const vw = v.videoWidth;
    const vh = v.videoHeight;
    if (!vw || !vh) throw new Error("Webcam belum siap.");

    const canvas = document.createElement("canvas");
    const targetRatio = 3 / 2;
    const videoRatio = vw / vh;

    let sx, sy, sw, sh;
    if (videoRatio > targetRatio) {
      sh = vh;
      sw = Math.round(vh * targetRatio);
      sx = Math.round((vw - sw) / 2);
      sy = 0;
    } else {
      sw = vw;
      sh = Math.round(vw / targetRatio);
      sx = 0;
      sy = Math.round((vh - sh) / 2);
    }

    canvas.width = sw;
    canvas.height = sh;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(v, sx, sy, sw, sh, 0, 0, sw, sh);

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob(
        (b) => (b ? resolve(b) : reject(new Error("Gagal mengambil foto."))),
        "image/jpeg",
        1,
      );
    });

    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = URL.createObjectURL(blob);

    const file = new File([blob], `webcam_${Date.now()}.jpg`, {
      type: blob.type || "image/jpeg",
    });

    // kalau stream external (dari store) jangan stop di sini
    if (!props.externalStream) stopInternal();

    emit("captured", { file, previewUrl: previewUrl.value });
  } catch (e) {
    emit("error", e);
  }
};

const retakeCamera = async () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = null;
  }

  emit("retake");

  // kalau internal & sudah stop, start lagi
  if (!props.externalStream && !stream.value) {
    await startInternal();
  }

  // kalau external, cukup attach ulang
  if (props.externalStream) {
    stream.value = props.externalStream;
    await attachToVideo();
  }
};

onBeforeUnmount(() => {
  if (!props.externalStream) stopInternal();
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
});

defineExpose({ takePhoto, retakeCamera });
</script>

<template>
  <div class="frame">
    <video
      v-if="!previewUrl"
      ref="videoDom"
      autoplay
      playsinline
      muted
    ></video>
    <img v-else :src="previewUrl" />
  </div>
</template>

<style>
.frame {
  width: 100%;
  aspect-ratio: 3 / 2;
  overflow: hidden;
  border-radius: 12px;
}

.frame img,
.frame video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  display: block;
}
</style>
