<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getGallery } from "../api/seeddream";

const router = useRouter();

const photos = ref([]);
const loading = ref(false);
const error = ref(null);
const selectedPhoto = ref(null);

const assetBase = (import.meta.env.VITE_ASSET_BASE || "http://127.0.0.1:8000").replace(/\/$/, "");

const handleHome = () => {
  router.push({ name: "Welcome" });
};

const resolvePhotoUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  const prefix = url.startsWith("/") ? "" : "/";
  return `${assetBase}${prefix}${url}`;
};

const loadGallery = async () => {
  loading.value = true;
  error.value = null;
  try {
    const data = await getGallery();
    photos.value = Array.isArray(data) ? data : [];
  } catch (err) {
    error.value = err?.message || "Gagal memuat gallery.";
  } finally {
    loading.value = false;
  }
};

const openModal = (photo) => {
  selectedPhoto.value = photo;
};

const closeModal = () => {
  selectedPhoto.value = null;
};

onMounted(loadGallery);
</script>

<template>
  <div class="page">
    <div class="header">
      <h1>Public Gallery</h1>
      <button @click="handleHome">Home</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="loading" class="muted">Loading...</p>
    <p v-else-if="photos.length === 0" class="muted">Belum ada hasil.</p>

    <div v-else class="grid">
      <button
        v-for="photo in photos"
        :key="photo.id"
        class="tile"
        type="button"
        @click="openModal(photo)"
      >
        <img
          :src="resolvePhotoUrl(photo.url)"
          :alt="`Result ${photo.id}`"
          loading="lazy"
        />
      </button>
    </div>

    <div v-if="selectedPhoto" class="modal" @click.self="closeModal">
      <div class="modal-content">
        <button class="modal-close" type="button" @click="closeModal">x</button>
        <img
          :src="resolvePhotoUrl(selectedPhoto.url)"
          :alt="`Result ${selectedPhoto.id}`"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.tile {
  border: none;
  padding: 0;
  background: transparent;
  cursor: pointer;
}

.tile img {
  width: 100%;
  height: 100%;
  aspect-ratio: 2 / 3;
  object-fit: cover;
  border-radius: 12px;
  display: block;
}

.muted {
  color: #6b7280;
}

.error {
  color: #c1121f;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 50;
}

.modal-content {
  position: relative;
  max-width: min(90vw, 960px);
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content img {
  width: 100%;
  height: auto;
  max-height: 90vh;
  border-radius: 12px;
  display: block;
  background: #111;
}

.modal-close {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: none;
  background: #ffffff;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}
</style>
