<script setup>
import { RouterView } from "vue-router";
</script>

<template>
  <RouterView v-slot="{ Component, route }">
    <transition name="fade" mode="out-in">
      <div class="page" :key="route.fullPath">
        <main class="content">
          <component :is="Component" />
        </main>

        <footer class="brand">
          <img src="./assets/ui/logo.png" alt="logo" />
        </footer>
      </div>
    </transition>
  </RouterView>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
