<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";
import CameraCapture from "../components/CameraCapture.vue";

const router = useRouter();
const store = useSeedDreamStore();
const fileRef = ref(null);

async function onUpload() {
  if (!store.session) return router.replace({ name: "Register" });
  if (!store.session.theme_id)
    return router.replace({ name: "ThemeSelection" });

  const file = fileRef.value?.files?.[0];
  if (!file) return alert("Pilih file dulu");

  await store.uploadPhoto(file);
  router.push({ name: "Loading" });
}

const goNext = () => router.push({ name: "Loading" });
const goBack = () => router.push({ name: "ThemeSelection" });

const handleCapture = () => {
  if (cameraRef.value) {
    cameraRef.value.takePhoto();
  }
};

const handleRetake = () => {
  if (cameraRef.value) {
    cameraRef.value.retakeCamera();
  }
};
</script>

<template>
  <div class="page">
    <div class="camera-wrapper">
      <CameraCapture ref="cameraRef" />

      <div class="camera-btn-wrapper">
        <!-- Button kiri -->
        <button class="btn" @click="state.photoUrl ? handleRetake() : goBack()">
          {{ state.photoUrl ? "Retake" : "Back" }}
        </button>

        <!-- Button kanan -->
        <button
          class="btn"
          @click="state.photoUrl ? goNext() : handleCapture()"
        >
          {{ state.photoUrl ? "Next" : "Capture" }}
        </button>
      </div>
    </div>
  </div>
  <h1>Upload Photo</h1>

  <p v-if="store.error" style="color: red">{{ store.error }}</p>

  <input type="file" ref="fileRef" accept="image/*" />
  <button @click="onUpload" :disabled="store.loading">Upload</button>
</template>
