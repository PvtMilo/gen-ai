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
  <div id="gallery">
    <div class="header">
      <h1>Gallery</h1>
      <button class="btn" @click="handleHome">Home</button>
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
        <div v-if="selectedPhoto.drive_link || selectedPhoto.qr_url" class="modal-actions">
          <a
            v-if="selectedPhoto.drive_link"
            class="btn-link"
            :href="selectedPhoto.drive_link"
            target="_blank"
            rel="noopener"
          >
            Drive Link
          </a>
          <img
            v-if="selectedPhoto.qr_url"
            class="qr"
            :src="selectedPhoto.qr_url"
            alt="QR Code"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
#gallery {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 16px;
  max-height: 80vh;
  min-height: 80vh;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  color: white;
}

h1 {
  margin-bottom: 1.5rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  /* grid-auto-flow :column ;
  grid-auto-columns: 25%; */
  gap: 12px;
  overflow-y: auto;
  /* border: 3px solid white; */
  margin: 3rem;
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

.modal-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.btn-link {
  text-decoration: none;
  padding: 8px 14px;
  border-radius: 8px;
  background: #111827;
  color: #ffffff;
  font-size: 14px;
}

.qr {
  width: 160px;
  height: 160px;
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




