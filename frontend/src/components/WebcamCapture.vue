<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from "vue";

const props = defineProps({
  externalStream: { type: Object, default: null }, // MediaStream dari store
  autoStart: { type: Boolean, default: true },     // fallback kalau externalStream null
  countdownSeconds: { type: Number, default: 3 },
});

const emit = defineEmits(["captured", "retake", "error"]);

const videoDom = ref(null);
const stream = ref(null);
const previewUrl = ref(null);
const countdown = ref(0);
const isCapturing = ref(false);

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

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

const runCountdown = async () => {
  const seconds = Math.max(0, Number(props.countdownSeconds) || 0);
  for (let current = seconds; current > 0; current -= 1) {
    countdown.value = current;
    await sleep(1000);
  }
  countdown.value = 0;
};

const captureNow = async () => {
  try {
    const v = videoDom.value;
    if (!v || !stream.value) throw new Error("Webcam belum siap.");

    const vw = v.videoWidth;
    const vh = v.videoHeight;
    if (!vw || !vh) throw new Error("Webcam belum siap.");

    // === samakan dengan preview CSS ===
    const frameRatio = 2 / 3; // container portrait 2:3
    const rotateDeg = 90;     // rotate(90deg)
    const zoom = 1;         // scale(1.8)

    // Karena preview diputar 90deg, area sumber yang dibutuhkan sebelum rotate
    // harus punya rasio kebalikan dari frame (3/2)
    const neededSrcRatio = 1 / frameRatio; // 3/2

    // Tentukan crop area di koordinat video asli (landscape)
    const videoRatio = vw / vh;
    let sw, sh;

    if (videoRatio > neededSrcRatio) {
      // video lebih lebar -> crop kiri kanan
      sh = vh;
      sw = Math.round(vh * neededSrcRatio);
    } else {
      // video lebih tinggi -> crop atas bawah
      sw = vw;
      sh = Math.round(vw / neededSrcRatio);
    }

    // apply zoom (scale): zoom besar => crop makin ketat
    sw = Math.round(sw / zoom);
    sh = Math.round(sh / zoom);

    const sx = Math.round((vw - sw) / 2);
    const sy = Math.round((vh - sh) / 2);

    // Output canvas portrait 2:3
    // Kamu bisa set resolusi bebas, ini contoh bagus untuk print/AI
    const outW = 1200;
    const outH = Math.round(outW / frameRatio); // 1800 untuk 2:3

    const canvas = document.createElement("canvas");
    canvas.width = outW;
    canvas.height = outH;

    const ctx = canvas.getContext("2d");

    // Rotate & draw supaya hasil sama seperti preview
    ctx.save();
    ctx.translate(outW / 2, outH / 2);
    ctx.rotate((rotateDeg * Math.PI) / 180);

    // setelah rotate 90deg, dimensi gambar tertukar
    ctx.drawImage(v, sx, sy, sw, sh, -outH / 2, -outW / 2, outH, outW);

    ctx.restore();

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob(
        (b) => (b ? resolve(b) : reject(new Error("Gagal mengambil foto."))),
        "image/jpeg",
        1
      );
    });

    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = URL.createObjectURL(blob);

    const file = new File([blob], `webcam_${Date.now()}.jpg`, {
      type: blob.type || "image/jpeg",
    });

    if (!props.externalStream) stopInternal();

    emit("captured", { file, previewUrl: previewUrl.value });
  } catch (e) {
    emit("error", e);
  }
};

const takePhoto = async () => {
  if (isCapturing.value) return;
  isCapturing.value = true;
  try {
    await runCountdown();
    await captureNow();
  } finally {
    countdown.value = 0;
    isCapturing.value = false;
  }
};


const retakeCamera = async () => {
  countdown.value = 0;
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
    <div v-if="countdown > 0 && !previewUrl" class="countdown-overlay">{{ countdown }}</div>
    <img v-else :src="previewUrl" />
  </div>
</template>

<style>
.frame {
  width: 80%;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  /* border: 10px solid blue; */
  position: relative;
}

.frame video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  transform: rotate(90deg) scale(1.8);
  transform-origin: center;
}

/* IMPORTANT: img hasil capture JANGAN di-rotate lagi */
.frame img {
  width: 100%;
  height: 100%;
  object-fit: cover; /* atau contain, pilih sesuai kebutuhan */
  display: block;
  transform: none;
}

.countdown-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: clamp(5rem, 12vw, 9rem);
  font-weight: 800;
  color: #fff;
  text-shadow: 0 8px 30px rgba(0, 0, 0, 0.55);
  background: rgba(0, 0, 0, 0.15);
  pointer-events: none;
}

</style>
