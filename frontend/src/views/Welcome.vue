<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

const handleNext = () => router.push({ name: "Register" });
</script>
<template>
  <h1>Welcome</h1>
  <button @click="handleNext">Next</button>
</template>
