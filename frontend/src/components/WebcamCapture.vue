<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";

const emit = defineEmits(["captured", "retake", "error"]);

const videoDom = ref(null);
const stream = ref(null);
const previewUrl = ref(null);

const stopCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach((t) => t.stop());
    stream.value = null;
  }
};

const startCamera = async () => {
  try {
    stream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    });
  } catch (error) {
    emit("error", error);
    return;
  }

  if (!videoDom.value) return;
  videoDom.value.srcObject = stream.value;
  await videoDom.value.play?.().catch(() => {});
};

const takePhoto = async () => {
  try {
    const video = videoDom.value;
    if (!video || !stream.value) throw new Error("Webcam belum siap.");

    const canvas = document.createElement("canvas");
    const targetRatio = 3 / 2;

    const vw = video.videoWidth;
    const vh = video.videoHeight;
    if (!vw || !vh) throw new Error("Webcam belum siap.");

    const videoRatio = vw / vh;

    let sx, sy, sw, sh;

    if (videoRatio > targetRatio) {
      // video terlalu lebar -> crop kiri-kanan
      sh = vh;
      sw = Math.round(vh * targetRatio);
      sx = Math.round((vw - sw) / 2);
      sy = 0;
    } else {
      // video terlalu tinggi -> crop atas-bawah
      sw = vw;
      sh = Math.round(vw / targetRatio);
      sx = 0;
      sy = Math.round((vh - sh) / 2);
    }

    const outW = sw;
    const outH = sh;

    canvas.width = outW;
    canvas.height = outH;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, sx, sy, sw, sh, 0, 0, outW, outH);

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob(
        (result) => {
          if (!result) {
            reject(new Error("Gagal mengambil foto."));
            return;
          }
          resolve(result);
        },
        "image/jpeg",
        1,
      );
    });

    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = URL.createObjectURL(blob);

    const file = new File([blob], `webcam_${Date.now()}.jpg`, {
      type: blob.type || "image/jpeg",
    });

    stopCamera();
    emit("captured", { file, previewUrl: previewUrl.value });
  } catch (err) {
    emit("error", err);
  }
};

const retakeCamera = async () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = null;
  }

  emit("retake");
  if (!stream.value) await startCamera();
};

onBeforeUnmount(() => {
  stopCamera();
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
});

onMounted(() => {
  startCamera();
});

defineExpose({
  takePhoto,
  retakeCamera,
});
</script>

<template>
  <div class="frame">
    <video v-if="!previewUrl" ref="videoDom" autoplay playsinline></video>
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

.frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  display: block;
}

.frame video {
  width: 100%;
  height: 100%;
  object-fit: cover; /* center crop otomatis */
  object-position: center; /* crop dari tengah */
  display: block;
}
</style>
