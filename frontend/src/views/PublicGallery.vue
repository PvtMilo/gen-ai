<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getGallery, uploadDriveForJob } from "../api/seeddream";

const router = useRouter();

const photos = ref([]);
const loading = ref(false);
const error = ref(null);
const selectedPhoto = ref(null);
const uploadingQr = ref(false);
const uploadLog = ref("");

const assetBase = (
  import.meta.env.VITE_ASSET_BASE || "http://127.0.0.1:8000"
).replace(/\/$/, "");

const handleHome = () => {
  router.push({ name: "Welcome" });
};

const resolvePhotoUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  const prefix = url.startsWith("/") ? "" : "/";
  return `${assetBase}${prefix}${url}`;
};

const resolveQrUrl = (url) => {
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

function patchPhotoDriveData(jobId, payload) {
  const patch = {
    drive_link: payload?.drive_link || null,
    download_link: payload?.download_link || null,
    qr_url: payload?.qr_url || null,
  };

  photos.value = photos.value.map((p) =>
    p.id === jobId ? { ...p, ...patch } : p,
  );

  if (selectedPhoto.value?.id === jobId) {
    selectedPhoto.value = { ...selectedPhoto.value, ...patch };
  }
}

async function ensureSelectedPhotoQrUploaded() {
  const photo = selectedPhoto.value;
  if (!photo || photo.qr_url || uploadingQr.value) return;

  uploadingQr.value = true;
  uploadLog.value = "UPLOADING FILE.....";

  try {
    const uploaded = await uploadDriveForJob(photo.id);
    patchPhotoDriveData(photo.id, uploaded);

    if (!uploaded?.qr_url) {
      uploadLog.value = "UPLOAD FAILED: QR URL is empty";
    }
  } catch (err) {
    const detail =
      err?.response?.data?.detail || err?.message || "Unknown upload error";
    uploadLog.value = `UPLOAD FAILED: ${detail}`;
  } finally {
    uploadingQr.value = false;
  }
}

const openModal = async (photo) => {
  selectedPhoto.value = photo;
  uploadLog.value = "";
  await ensureSelectedPhotoQrUploaded();
};

const closeModal = () => {
  selectedPhoto.value = null;
  uploadingQr.value = false;
  uploadLog.value = "";
};

onMounted(loadGallery);
</script>

<template>
  <div id="gallery">
    <div class="header">
      <h1>Gallery</h1>
      <div class="header-button">
        <img class="exit-btn" src="../assets/ui/exit.png" @click="handleHome">
      </div>
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
        <img
          :src="resolvePhotoUrl(selectedPhoto.url)"
          :alt="`Result ${selectedPhoto.id}`"
        />
        <div class="modal-actions">
          <!-- <a
            v-if="selectedPhoto.drive_link"
            class="btn-link"
            :href="selectedPhoto.drive_link"
            target="_blank"
            rel="noopener"
          >
            Drive Link
          </a> -->
          <img
            v-if="selectedPhoto.qr_url"
            class="qr"
            :src="resolveQrUrl(selectedPhoto.qr_url)"
            alt="QR Code"
          />
          <img
            v-else-if="uploadingQr"
            src="../assets/ui/loading.gif"
            class="loading"
          />
          <span
            class="uploading-log"
            v-if="!selectedPhoto.qr_url && uploadLog"
            >{{ uploadLog }}</span
          >
          <button class="btn" type="button" @click="closeModal">BACK</button>
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
  max-height: 88vh;
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

.header-button {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 2rem;
}

.switch-wrapper{
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  font-size: 2rem;
  gap: 1rem;
}

.switch {
  transform: scale(1.4);
  transform-origin: left center;
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
  overflow-y: scroll;
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
  max-width: 90%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #4e4e4e71;
  padding: 4rem;
  gap: 2rem;
}

.modal-content {
  width: 80%;
  height: auto;
}

.modal-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 40%;
  gap: 2rem;
}

.loading {
  width: 200px;
}

.uploading-log {
  color: #c1121f;
  font-size: 1.2rem;
  text-align: center;
}

.btn-link {
  text-decoration: none;
  padding: 8px 14px;
  border-radius: 8px;
  background: #111827;
  color: #ffffff;
  font-size: 14px;
}

.exit-btn {
  width: 130px;
}
</style>
