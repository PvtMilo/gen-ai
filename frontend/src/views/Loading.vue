<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";

const router = useRouter();
const store = useSeedDreamStore();

onMounted(async () => {
  try {
    const finalJob = await store.generate({ intervalMs: 1000, timeoutMs: 240000 });

    if (finalJob.status === "done") {
      router.replace({ name: "Result" });
      return;
    }

    // failed
    alert(finalJob.error_message || "Job failed");
    router.replace({ name: "UploadPhoto" });
  } catch (e) {
    alert(store.error || e?.message || "Generate failed");
    router.replace({ name: "UploadPhoto" });
  }
});
</script>

<template>
  <h1>Processing...</h1>
  <p>Status: {{ store.job?.status || "starting..." }}</p>
  <p v-if="store.error" style="color:red;">{{ store.error }}</p>
</template>
