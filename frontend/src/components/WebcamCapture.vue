<script setup>
import { computed, onBeforeUnmount, ref } from "vue";
import { onMounted } from "vue";

const videoDom = ref(null);
const stream = ref(null);

const photoBlob = ref(null);
const previewUrl = ref(null);

const isCamReady = computed(() => !!stream.value || !!videoDom.value);

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
    alert(error.message);
    return;
  }
  videoDom.value.srcObject = stream.value;

  // current webcam resolution size
  const track = stream.value.getVideoTracks()[0];
  console.log("Track settings:", track.getSettings());
  videoDom.value.onloadedmetadata = () => {
    console.log(
      "Video element:",
      videoDom.value.videoWidth,
      "x",
      videoDom.value.videoHeight,
    );
  };
};

const capture = async () => {
  const video = videoDom.value;
  if (!video) return;

  const canvas = document.createElement("canvas");
  const targetRatio = 3 / 2;

  const vw = video.videoWidth;
  const vh = video.videoHeight;
  const videoRatio = vw / vh;

  let sx, sy, sw, sh;

  if (videoRatio > targetRatio) {
    // video terlalu lebar → crop kiri-kanan
    sh = vh;
    sw = Math.round(vh * targetRatio);
    sx = Math.round((vw - sw) / 2);
    sy = 0;
  } else {
    // video terlalu tinggi → crop atas-bawah
    sw = vw;
    sh = Math.round(vw / targetRatio);
    sx = 0;
    sy = Math.round((vh - sh) / 2);
  }

  // output canvas 2:3 (bisa kamu tentukan resolusinya)
  const outW = sw;
  const outH = sh;

  canvas.width = outW;
  canvas.height = outH;

  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, sx, sy, sw, sh, 0, 0, outW, outH);

  canvas.toBlob(
    (blob) => {
      if (!blob) return;
      photoBlob.value = blob;

      if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
      previewUrl.value = URL.createObjectURL(blob);
    },
    "image/jpeg",
    1,
  );
};

const reCapture = async () => {

  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = null;
  }


  if (stream.value) {
    stream.value.getTracks().forEach((t) => t.stop());
    stream.value = null;
  }

  await startCamera();
};

onBeforeUnmount(() => {
  if (stream.value) stream.value.getTracks().forEach((t) => t.stop());
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
});

onMounted(() => {
  startCamera();
});
</script>
<template>
  <div>
    <div class="frame">
      <video v-if="!previewUrl" ref="videoDom" autoplay playsinline></video>
        <img v-else :src="previewUrl"  />
      </div>
    </div>

    <div style="margin-top: 12px">
      <button @click="capture" :disabled="!isCamReady">Capture</button>
      <button v-if="previewUrl" @click="reCapture">Retake</button>
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
