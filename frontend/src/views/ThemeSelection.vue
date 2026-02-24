<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";

import { Swiper, SwiperSlide } from "swiper/vue";
import "swiper/css";
import "swiper/css/pagination";

const router = useRouter();
const store = useSeedDreamStore();

const assetBase = import.meta.env.VITE_ASSET_BASE || "http://127.0.0.1:8000";

const selectedThemeId = ref(null);
const hasPicked = ref(false);

onMounted(async () => {
  await store.loadThemes();
});

function thumbUrl(t) {
  return t.thumbnail_url ? `${assetBase}${t.thumbnail_url}` : "";
}

function onSlideChange() {
  //
}

function pickByClick(themeId) {
  selectedThemeId.value = themeId;
  hasPicked.value = true;
}

async function goNext() {
  if (!hasPicked.value || !selectedThemeId.value) return;

  try {
    await store.chooseTheme(selectedThemeId.value);

    // Warmup webcam sebelum pindah halaman (biar UploadPhoto langsung ready)
    if (store.photoSource === "webcam") {
      await store.warmupWebcam({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
    }

    router.push("/upload");
  } catch (e) {
    // 1) error dari chooseTheme sudah ada di store.error
    // 2) error permission webcam ada di store.cameraError (kalau kamu set di store)
    // tinggal tampilkan di UI
    console.error(e);
  }
}

const handleBack = () => {
  router.push({ name: "Register" });
};
</script>
<template>
  <div id="themes">
    <h1 class="title">Select your themes</h1>
    <Swiper
      :slides-per-view="'auto'"
      :space-between="12"
      :centered-slides="store.themes.length <= 2"
      :watch-overflow="true"
      :allow-touch-move="store.themes.length > 1"
      :simulate-touch="true"
      :grab-cursor="store.themes.length > 1"
      :pagination="{ clickable: true }"
      @slideChange="onSlideChange"
      class="theme-swiper"
    >
      <SwiperSlide v-for="t in store.themes" :key="t.id" class="theme-slide">
        <div
          class="card"
          :class="{ active: t.id === selectedThemeId }"
          role="button"
          tabindex="0"
          @click="pickByClick(t.id)"
        >
          <img
            v-if="t.thumbnail_url"
            :src="thumbUrl(t)"
            class="thumb"
            alt="theme thumbnail"
          />
        </div>
      </SwiperSlide>
    </Swiper>
    <div class="action-btn">
      <button class="back btn" @click="handleBack">Back</button>
      <button class="next btn" :disabled="!hasPicked" @click="goNext">
        Next
      </button>
    </div>
  </div>
</template>

<style scoped>
#themes {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: min(100vw, 1400px);
  min-width: 0;
  font-size: 4rem;
  margin: 2em 0em 2em 0em;
  padding: 0 10px;
}

.theme-swiper {
  width: 100%;
  max-width: 1200px;
  padding: 8px 8px 22px;
  overflow: hidden;
  touch-action: pan-y;
}

.theme-slide {
  width: clamp(180px, 34vw, 360px);
}

.card {
  padding: 10px;
  border-radius: 16px;
  background: rgba(0, 0, 0, 0.05);
  border: 3px solid transparent;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.card.active {
  border-color: #ffd400;
  box-shadow: 0 0 0 4px rgba(255, 212, 0, 0.35);
  transform: scale(1.02);
}

.thumb {
  width: 100%;
  aspect-ratio: 2 / 3;
  object-fit: cover;
  border-radius: 14px;
  display: block;
}

.footer {
  margin-top: 18px;
  display: flex;
  justify-content: center;
}

.next:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
