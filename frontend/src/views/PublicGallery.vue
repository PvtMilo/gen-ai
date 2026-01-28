<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

const handleHome = () => {
  router.push({name : "Welcome"})
}
</script>
<template>
  <h1>Public gallery</h1>
  <button @click="handleHome">Home</button>
</template>
<style></style>
