<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";

const router = useRouter();
const store = useSeedDreamStore();

const logText = computed(() => store.job?.log_text || "");
const latestLog = computed(() => {
  if (!logText.value) return "";
  const lines = logText.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  return lines.length ? lines[lines.length - 1] : "";
});
const statusText = computed(() => store.job?.status || "processing");

onMounted(async () => {
  store.stopWebcam();

  try {
    const finalJob = await store.generate({
      intervalMs: 1000,
      timeoutMs: 240000,
    });

    if (finalJob.status === "done") {
      router.replace({ name: "Result" });
      return;
    }

    alert(finalJob.error_message || "Job failed");
    router.replace({ name: "UploadPhoto" });
  } catch (e) {
    alert(store.error || e?.message || "Generate failed");
    router.replace({ name: "UploadPhoto" });
  } finally {
    store.stopWebcam();
  }
});
</script>

<template>
  <div class="loading-page">
    <img class="loading" src="../assets/ui/loading.gif" alt="loading" />
    <p class="job-log">
      {{ latestLog || statusText }}
    </p>
  </div>
</template>
<style scoped>
.job-log {
  white-space: pre-line;
  color: white;
  font-size: 2rem;
  text-align: center;
}

.loading-page{
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
</style>
