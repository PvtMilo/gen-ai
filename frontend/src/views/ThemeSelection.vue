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
}

function pickByClick(themeId) {
  selectedThemeId.value = themeId;
  hasPicked.value = true;
}

async function goNext() {
  if (!hasPicked.value || !selectedThemeId.value) return;
  await store.chooseTheme(selectedThemeId.value);
  router.push("/upload");
}
</script>
<template>
  <h1>Theme Selection</h1>

  <Swiper
    :slides-per-view="'auto'"
    :space-between="12"
    :centered-slides="store.themes.length <= 2"
    :watch-overflow="true"
    :pagination="{ clickable: true }"
    @slideChange="onSlideChange"
    class="theme-swiper"
  >
    <SwiperSlide
      v-for="t in store.themes"
      :key="t.id"
      class="theme-slide"
    >
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

  <div class="footer">
    <button class="next-btn" :disabled="!hasPicked" @click="goNext">
      Next
    </button>
  </div>
</template>

<style scoped>

.theme-swiper {
  padding: 8px 8px 22px;
}

.theme-slide {
  width: clamp(160px, 42vw, 260px);
}

.card {
  padding: 10px;
  border-radius: 16px;
  background: rgba(0,0,0,0.05);
  border: 3px solid transparent;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
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
.next-btn {
  padding: 14px 28px;
  font-size: 16px;
  border-radius: 999px;
  border: none;
  background: #111;
  color: #fff;
  cursor: pointer;
}
.next-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

</style>

