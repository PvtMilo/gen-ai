<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

const handleNext = () => router.push({ name: "Register" });
</script>
<template>
  <div id="welcome">
    <img @click="handleNext" src="../assets/ui/tap.png" alt="tap-button">
  </div>
</template>
<style>
  #welcome{
    display: flex;
    flex-direction: column;
    padding-bottom: 13rem;
    padding-top: 5rem;
  }

</style>
