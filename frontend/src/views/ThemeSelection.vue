<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";

const router = useRouter();
const store = useSeedDreamStore();

// ✅ ini yang hilang (biar /static/... jadi ke backend)
const assetBase = import.meta.env.VITE_ASSET_BASE || "http://127.0.0.1:8000";

onMounted(async () => {
  await store.loadThemes();
});

async function pickTheme(themeId) {
  await store.chooseTheme(themeId);
  router.push("/upload");
}

function thumbUrl(t) {
  return t.thumbnail_url ? `${assetBase}${t.thumbnail_url}` : "";
}
</script>

<template>
  <h1>Theme Selection</h1>

  <div v-for="t in store.themes" :key="t.id">
    <div>{{ t.title }}</div>

    <!-- ✅ pakai url yang sudah diprefix -->
    <img v-if="t.thumbnail_url" :src="thumbUrl(t)" style="width:120px; height:auto;" />

    <button @click="pickTheme(t.id)">Pakai</button>
  </div>
</template>
