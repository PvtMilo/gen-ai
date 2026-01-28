<script setup>
import { useRouter } from "vue-router";

const router = useRouter();
const handleHome = () => {
    router.push({name : "Welcome"})
}
</script>

<template>
  <h1>Setting</h1>
  <button @click="handleHome">Home</button>
  <div>
    <form>
      <label for="source">Pilih Sumber Foto</label>
      <select id="source" name="source">
        <option value="">-- Pilih --</option>
        <option value="webcam">Webcam</option>
        <option value="camera">Camera</option>
        <option value="manual">Manual Upload</option>
      </select>
      <button>Submit</button>
    </form>
  </div>
</template>
<style>

</style>
