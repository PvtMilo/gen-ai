<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";

const router = useRouter();
const store = useSeedDreamStore();
const fileRef = ref(null);

async function onUpload() {
  if (!store.session) return router.replace({ name: "Register" });
  if (!store.session.theme_id) return router.replace({ name: "ThemeSelection" });

  const file = fileRef.value?.files?.[0];
  if (!file) return alert("Pilih file dulu");

  await store.uploadPhoto(file);
  router.push({ name: "Loading" });
}
</script>

<template>
  <h1>Upload Photo</h1>

  <p v-if="store.error" style="color:red;">{{ store.error }}</p>

  <input type="file" ref="fileRef" accept="image/*" />
  <button @click="onUpload" :disabled="store.loading">Upload</button>
</template>
