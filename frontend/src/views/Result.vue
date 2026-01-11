<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";

const router = useRouter();
const store = useSeedDreamStore();

// base backend (tanpa /api/v1)
const assetBase = import.meta.env.VITE_ASSET_BASE_URL || "http://127.0.0.1:8000";

const resultUrl = computed(() => {
  const p = store.job?.result_url;
  if (!p) return null;
  return p.startsWith("http") ? p : assetBase + p;
});

function handleFinish() {
  router.push({ name: "Welcome" });
}
</script>

<template>
  <h1>Result</h1>

  <div v-if="resultUrl">
    <img :src="resultUrl" style="max-width: 360px;" />
    <div>
      <a :href="resultUrl" target="_blank">Open image</a>
    </div>
  </div>

  <button @click="handleFinish">Finish</button>
</template>
