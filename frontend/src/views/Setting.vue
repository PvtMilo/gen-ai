<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";
import { getPrinters } from "../api/seeddream";

const router = useRouter();
const store = useSeedDreamStore();

const assetBase = import.meta.env.VITE_ASSET_BASE || "http://127.0.0.1:8000";

const selectedSource = ref(store.photoSource || "camera");
const selectedApi = ref(store.apiSource || "comfy");
const selectedMode = ref(store.runMode || "event");
const selectedPrinter = ref(store.printerName || "");
const selectedOverlayFile = ref(null);
const overlayInput = ref(null);
const overlayUploading = ref(false);
const overlayError = ref("");
const overlayPreviewBroken = ref(false);

const saving = ref(false);
const saveError = ref("");
const saveInfo = ref("");
const loadingPrinters = ref(false);
const printersError = ref("");
const availablePrinters = ref([]);

const overlayPreviewUrl = computed(() => {
  const url = store.overlayUrl;
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${assetBase}${url}`;
});

const overlayFileName = computed(() => {
  const url = store.overlayUrl || "";
  const parts = url.split("/");
  return parts[parts.length - 1] || "";
});

watch(
  () => store.overlayUrl,
  () => {
    overlayPreviewBroken.value = false;
  },
  { immediate: true },
);

const handleOverlayPreviewError = () => {
  overlayPreviewBroken.value = true;
};

const handleOverlayPreviewLoad = () => {
  overlayPreviewBroken.value = false;
};

const handleHome = () => {
  router.push({ name: "Welcome" });
};

const handleThemeSetting = () => {
  router.push({ name: "ThemeSetting" });
};

const onOverlaySelected = async (event) => {
  const file = event?.target?.files?.[0] || null;
  selectedOverlayFile.value = file;
  overlayError.value = "";
  saveError.value = "";

  if (!file) return;

  const isPng =
    file.type === "image/png" || file.name?.toLowerCase?.().endsWith(".png");
  if (!isPng) {
    overlayError.value = "Overlay must be PNG (.png)";
    selectedOverlayFile.value = null;
    if (overlayInput.value) overlayInput.value.value = "";
    return;
  }

  overlayUploading.value = true;

  try {
    const uploaded = await store.uploadOverlay(file);
    saveInfo.value = `Overlay saved: ${uploaded.width}x${uploaded.height}`;
    selectedOverlayFile.value = null;
    if (overlayInput.value) overlayInput.value.value = "";
  } catch (err) {
    overlayError.value =
      store.error || err?.message || "Failed to upload overlay";
  } finally {
    overlayUploading.value = false;
  }
};

const loadPrinters = async () => {
  loadingPrinters.value = true;
  printersError.value = "";
  try {
    const data = await getPrinters();
    availablePrinters.value = Array.isArray(data?.printers)
      ? data.printers
      : [];
    if (data?.error_message) {
      printersError.value = data.error_message;
    }

    const names = availablePrinters.value.map((p) => p.name);
    if (selectedPrinter.value && !names.includes(selectedPrinter.value)) {
      selectedPrinter.value = "";
    }
  } catch (err) {
    availablePrinters.value = [];
    printersError.value = err?.message || "Failed to load printer list";
  } finally {
    loadingPrinters.value = false;
  }
};

const saveSetting = async () => {
  saving.value = true;
  saveError.value = "";
  saveInfo.value = "";

  try {
    store.setPhotoSource(selectedSource.value);
    store.setApiSource(selectedApi.value);
    store.setRunMode(selectedMode.value);
    store.setPrinterName(selectedPrinter.value);

    saveInfo.value = "Settings saved";
  } catch (err) {
    saveError.value = store.error || err?.message || "Failed to save settings";
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  loadPrinters();
});
</script>

<template>
  <section id="feature">
    <div class="form-wrapper">
      <h1 class="setting">Setting</h1>
      <form @submit.prevent="saveSetting">
        <section class="Api-option">
          <label for="api">Select API</label>
          <select id="api" name="api" v-model="selectedApi">
            <option value="native">Native</option>
            <option value="comfy">Comfy Ui</option>
          </select>
        </section>
        <section class="debug-option">
          <label for="mode">Select mode</label>
          <select id="mode" name="mode" v-model="selectedMode">
            <option value="event">Event</option>
            <option value="debugging">Debugging</option>
          </select>
        </section>
        <section class="camera-options">
          <label for="source">Pilih Sumber Foto</label>
          <select id="source" name="source" v-model="selectedSource">
            <option value="webcam">Webcam</option>
            <option value="camera">Camera</option>
            <option value="manual">Manual Upload</option>
          </select>
        </section>
        <!-- <section class="printer-options">
          <label for="printer">Select Printer</label>
          <select
            id="printer"
            name="printer"
            v-model="selectedPrinter"
            :disabled="loadingPrinters || availablePrinters.length === 0"
          >
            <option v-if="loadingPrinters" value="">Loading printers...</option>
            <option v-else-if="availablePrinters.length === 0" value="">
              No printer detected
            </option>
            <template v-else>
              <option
                v-for="printer in availablePrinters"
                :key="printer.name"
                :value="printer.name"
              >
                {{ printer.name }}{{ printer.is_default ? " (Default)" : "" }}
              </option>
            </template>
          </select>
          <div class="refresh-wrapper">
            <button
              type="button"
              class="refresh-btn btn"
              @click="loadPrinters"
              :disabled="loadingPrinters"
            >
              {{ loadingPrinters ? "Refreshing..." : "Refresh printers" }}
            </button>
          </div>

          <small v-if="printersError" class="error">{{ printersError }}</small>
        </section> -->
        <section class="overlay">
          <label for="file">Choose Overlay</label>
          <input
            id="file"
            ref="overlayInput"
            type="file"
            name="overlay"
            accept=".png,image/png"
            :disabled="overlayUploading"
            @change="onOverlaySelected"
          />
          <small v-if="overlayUploading">Uploading overlay...</small>
          <small v-if="selectedOverlayFile"
            >Selected: {{ selectedOverlayFile.name }}</small
          >
          <small v-if="overlayError" class="error">{{ overlayError }}</small>

          <template v-if="store.overlayUrl && !overlayPreviewBroken">
            <small v-if="store.overlayMeta">
              Current overlay: {{ overlayFileName }} ({{
                store.overlayMeta.width
              }}x{{ store.overlayMeta.height }})
            </small>
            <small v-else>Current overlay: {{ overlayFileName }}</small>
            <img
              :src="overlayPreviewUrl"
              class="overlay-preview"
              alt="Current overlay"
              @error="handleOverlayPreviewError"
              @load="handleOverlayPreviewLoad"
            />
          </template>
          <small
            v-else-if="store.overlayUrl && overlayPreviewBroken"
            class="error"
          >
            Saved overlay file is not available on server.
          </small>
        </section>
        <div class="save-info">
          <p v-if="saveInfo">{{ saveInfo }}</p>
          <p v-if="saveError" class="error">{{ saveError }}</p>
        </div>
        <div class="action-button">
          <button
            class="btn save"
            type="submit"
            :disabled="saving || overlayUploading"
          >
            {{ saving ? "Saving..." : "Save" }}
          </button>
        </div>
      </form>
    </div>
    <div class="bottom-btn-wrapper">
      <button class="btn" @click="handleThemeSetting">Theme Setting</button>
      <button class="btn" @click="handleHome">Home</button>
    </div>
  </section>
</template>
<style scoped>
#feature {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
}

.form-wrapper {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(100, 100, 100, 0.171);
  min-width: 80vw;
}

form {
  max-width: 80vw;
}

section {
  display: flex;
  flex-direction: column;
}

.overlay {
  padding-bottom: 1rem;
}

.save-info {
  display: flex;
  justify-content: center;
  padding-bottom: 1rem;
}

label,
button,
input {
  font-size: 3rem;
  color: white;
}

.setting {
  font-size: 4rem;
}

option {
  font-size: 1.5rem;
}

.action-button {
  display: flex;
  justify-content: center;
}

.save {
  width: 25%;
}

.refresh-wrapper {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-top: 1rem;
}

.refresh-btn {
  font-size: 2.5rem;
}

.error {
  color: #c1121f;
}

.bottom-btn-wrapper {
  display: flex;
  margin-top: 3rem;
  width: 50%;
  justify-content: center;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

select {
  font-size: 3rem;
}

.overlay-preview {
  width: min(300px, 60vw);
  margin: 12px auto 0;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}
</style>
