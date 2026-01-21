<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useSession } from '../stores/useSession'

// ---------------------------------------------------------------------
// Konfigurasi endpoint backend
// ---------------------------------------------------------------------
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const LIVEVIEW_ENDPOINT = `${API_BASE}/api/camera/liveview`
const CAPTURE_ENDPOINT  = `${API_BASE}/api/camera/capture`

// ---------------------------------------------------------------------
// State
// ---------------------------------------------------------------------
const { state } = useSession() 
const hasPhoto = ref(false)
const photoUrl = ref(null)

const liveTick = ref(0)
let liveIntervalId = null

const liveViewUrl = computed(() => {
  return `${LIVEVIEW_ENDPOINT}?_=${liveTick.value}`
})

// ---------------------------------------------------------------------
// Fungsi kontrol kamera
// ---------------------------------------------------------------------
const startCamera = () => {
  hasPhoto.value = false
  photoUrl.value = null
  state.photoUrl = null              // 🔥 reset juga di session

  if (!liveIntervalId) {
    liveIntervalId = setInterval(() => {
      liveTick.value++
    }, 500)
  }
}

const stopCamera = () => {
  if (liveIntervalId) {
    clearInterval(liveIntervalId)
    liveIntervalId = null
  }
}

const takePhoto = async () => {
  try {
    stopCamera()

    const res = await fetch(CAPTURE_ENDPOINT, { method: 'POST' })
    if (!res.ok) throw new Error(`Capture failed: ${res.status}`)

    const data = await res.json()

    // URL dari backend
    photoUrl.value = data.photo_url
    hasPhoto.value = true

    // 🔥 SIMPAN ke session supaya halaman lain bisa pakai
    state.photoUrl = data.photo_url

  } catch (err) {
    console.error('Error capture:', err)
    alert('Gagal capture foto. Coba lagi.')
    startCamera()
  }
}


const retakeCamera = () => {
  photoUrl.value = null
  hasPhoto.value = false
  state.photoUrl = null              // 🔥 reset di session juga
  startCamera()
}
// ---------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------
onMounted(startCamera)
onBeforeUnmount(stopCamera)

defineExpose({
  takePhoto,
  retakeCamera,
})

</script>

<template>
  <div>
    <!-- Frame untuk live view / hasil foto -->
    <div class="camera-frame">
      <!-- Jika belum ada foto: tampilkan live view -->
       <div class="live-view-wrapper"  v-if="!hasPhoto"> 
      <img
        :src="liveViewUrl"
        alt="Live view"
        class="camera-live"
      />
      <img
        src="../assets/siluet.png"
        alt="Silhouette"
        class="overlay-siluet"
      />      
      </div>

      <!-- Jika sudah ada foto: tampilkan hasil capture -->
      <img
        v-else-if="photoUrl"
        :src="photoUrl"
        alt="Captured photo"
        class="camera-image"
      />

      <p v-else>Tidak ada foto.</p>
    </div>

    <!-- Tombol -->
    <!-- <button
      v-if="!hasPhoto"
      class="btn"
      @click="takePhoto"
    >
      Capture &amp; Upload
    </button>
    <button
      v-else
      class="btn btn-secondary"
      @click="retakeCamera"
    >
      Retake
    </button> -->
  </div>
</template>

<style>
.camera-frame {
  width: 100%;
  margin: 0 auto;     /* center di tengah container */

}

.camera-live{
  display: flex;
  width: 100%;        /* isi lebar frame */
  height: auto;       /* tinggi mengikuti rasio asli gambar */
  margin: 0 auto; 
  border-radius: 24px;
}

/* Pastikan rasio gambar terjaga, tidak gepeng */
.camera-image {
  display: flex;
  width: 90%;        /* isi lebar frame */
  height: auto;       /* tinggi mengikuti rasio asli gambar */
  margin: 0 auto; 
    border-radius: 24px;
}

.overlay-siluet{
  position: absolute;
  top: 33.5em;
  left: 0;
}
</style>
