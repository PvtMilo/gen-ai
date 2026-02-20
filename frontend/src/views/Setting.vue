<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";
import { getPrinters } from "../api/seeddream";

const router = useRouter();
const store = useSeedDreamStore();
const selectedSource = ref(store.photoSource || "camera");
const selectedApi = ref(store.apiSource || "comfy")
const selectedMode = ref(store.runMode || "event");
const selectedPrinter = ref(store.printerName || "");
const selectedOverlayFile = ref(null);
const saving = ref(false);
const saveError = ref("");
const saveInfo = ref("");
const loadingPrinters = ref(false);
const printersError = ref("");
const availablePrinters = ref([]);

const handleHome = () => {
  router.push({ name: "Welcome" });
};

const onOverlaySelected = (event) => {
  const file = event?.target?.files?.[0] || null;
  selectedOverlayFile.value = file;
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

    if (selectedOverlayFile.value) {
      const isPng =
        selectedOverlayFile.value.type === "image/png" ||
        selectedOverlayFile.value.name?.toLowerCase?.().endsWith(".png");
      if (!isPng) {
        throw new Error("Overlay must be PNG (.png)");
      }

      const uploaded = await store.uploadOverlay(selectedOverlayFile.value);
      saveInfo.value = `Overlay saved: ${uploaded.width}x${uploaded.height}`;
    } else {
      saveInfo.value = "Settings saved";
    }
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
        <section class="printer-options">
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
        </section>
        <section class="overlay">
          <label for="file">Choose Overlay</label>
          <input
            id="file"
            type="file"
            name="overlay"
            accept=".png,image/png"
            @change="onOverlaySelected"
          />
          <small v-if="store.overlayMeta">
            Current overlay: {{ store.overlayMeta.width }}x{{
              store.overlayMeta.height
            }}
          </small>
        </section>
        <p v-if="saveInfo">{{ saveInfo }}</p>
        <p v-if="saveError" class="error">{{ saveError }}</p>
        <div class="action-button">
          <button class="btn save" type="submit" :disabled="saving">
            {{ saving ? "Saving..." : "Save" }}
          </button>
        </div>
      </form>
    </div>
    <div class="home-wrapper">
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

.home-wrapper {
  display: flex;
  margin-top: 3rem;
  width: 70%;
  justify-content: center;
}

select {
  font-size: 3rem;
}
</style>
