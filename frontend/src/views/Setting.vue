<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";

const router = useRouter();
const store = useSeedDreamStore();
const selectedSource = ref(store.photoSource || "camera");

const handleHome = () => {
    router.push({name : "Welcome"})
}

const saveSetting = () => {
  store.setPhotoSource(selectedSource.value);
};
</script>

<template>
  <h1>Setting</h1>
  <button @click="handleHome">Home</button>
  <div>
    <form @submit.prevent="saveSetting">
      <label for="source">Pilih Sumber Foto</label>
      <select id="source" name="source" v-model="selectedSource">
        <option value="webcam">Webcam</option>
        <option value="camera">Camera</option>
        <option value="manual">Manual Upload</option>
      </select>
      <button type="submit">Save</button>
    </form>
  </div>
</template>
<style>

</style>
