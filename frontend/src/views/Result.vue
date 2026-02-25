<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";
import { getJob } from "../api/seeddream";

const router = useRouter();
const store = useSeedDreamStore();

// base backend (tanpa /api/v1)
const assetBase =
  import.meta.env.VITE_ASSET_BASE_URL || "http://127.0.0.1:8000";
const apiBase =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
const backendBase = apiBase.replace(/\/api\/v1\/?$/, "");

const resultUrl = computed(() => {
  const p = store.job?.result_url;
  if (!p) return null;
  return p.startsWith("http") ? p : assetBase + p;
});

const singleQrCode = ref(null);
const isQrOpen = ref(false);
const isFmodalOpen = ref(false);
const isPrintingModalOpen = ref(false);

const driveLink = computed(() => {
  return (
    store.job?.drive_url ||
    store.job?.drive_link ||
    store.job?.driveLink ||
    null
  );
});

const downloadLink = computed(() => {
  return store.job?.download_link || store.job?.downloadLink || null;
});

const qrUrl = computed(() => store.job?.qr_url || null);

const qrImageUrl = computed(() => {
  const value = singleQrCode.value;
  if (!value) return "";

  if (value.startsWith("/")) {
    return `${backendBase}${value}`;
  }

  const lower = value.toLowerCase();
  const isImage =
    value.startsWith("data:image/") ||
    lower.includes("/drive/qr") ||
    /\.(png|jpe?g|gif|webp|svg)$/.test(lower);

  if (isImage) return value;

  return `${backendBase}/api/v1/drive/qr?url=${encodeURIComponent(value)}`;
});

watch(
  [downloadLink, driveLink, qrUrl],
  ([download, drive, qr]) => {
    if (qr) {
      singleQrCode.value = qr;
      return;
    }

    if (download) {
      singleQrCode.value = download;
      return;
    }

    if (drive) {
      singleQrCode.value = drive;
      return;
    }

    singleQrCode.value = null;
  },
  { immediate: true },
);

// DRIVE QR MODAL
const openQrModal = () => {
  if (!singleQrCode.value) return;
  isQrOpen.value = true;
};

const closeQrModal = () => {
  isQrOpen.value = false;
};

let pollTimer = null;
let pollTries = 0;

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
};

const pollJobForDrive = async () => {
  if (!store.job?.job_id) return;
  if (downloadLink.value || qrUrl.value) {
    stopPolling();
    return;
  }

  pollTries += 1;

  try {
    const latest = await getJob(store.job.job_id);
    store.job = latest;
    store.persist?.();
  } catch (_) {
    // ignore and retry
  }

  if (downloadLink.value || qrUrl.value) {
    stopPolling();
  }

  if (pollTries >= 12) {
    stopPolling();
  }
};

// PRINTING MODAL

const openPrintingModal = () => {
  isPrintingModalOpen.value = true;
};

const closePrintingModal = () => {
  isPrintingModalOpen.value = false;
};

const confirmPrinting = () => {
  isPrintingModalOpen.value = false;
  if (typeof window === "undefined") return;

  const resultPath = store.job?.result_url || "";
  const imageUrl = resultUrl.value;

  if (!imageUrl) {
    alert("Result image is not ready.");
    return;
  }

  // Guard: only print generated output from static/results, never captured/upload source.
  if (!resultPath.includes("/static/results/")) {
    alert("Printable result image not found.");
    return;
  }

  const printWindow = window.open("", "_blank", "width=1200,height=900");
  if (!printWindow) {
    alert("Unable to open print window.");
    return;
  }

  const safeUrl = imageUrl.replace(/"/g, "&quot;");
  printWindow.document.write(`
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Print Result</title>
        <style>
          @page { margin: 0; }
          html, body {
            margin: 0;
            padding: 0;
            background: #fff;
          }
          .print-wrap {
            width: 2400px;
            height: 3600px;
            margin: 0 auto;
          }
          img {
            display: block;
            width: 100%;
            height: 100%;
            object-fit: contain;
          }
        </style>
      </head>
      <body>
        <div class="print-wrap">
          <img id="print-image" src="${safeUrl}" alt="Result Image" />
        </div>
      </body>
    </html>
  `);
  printWindow.document.close();

  const img = printWindow.document.getElementById("print-image");
  if (!img) {
    printWindow.close();
    alert("Failed to load result image for printing.");
    return;
  }

  const triggerPrint = () => {
    printWindow.focus();
    printWindow.print();
    setTimeout(() => printWindow.close(), 200);
  };

  img.onload = triggerPrint;
  img.onerror = () => {
    printWindow.document.body.innerHTML =
      "<p>Failed to load result image for printing.</p>";
  };

  if (img.complete) {
    triggerPrint();
  }
};

// FINISH MODAL

const openFModal = () => {
  isFmodalOpen.value = true;
};

const closeFModal = () => {
  isFmodalOpen.value = false;
};

onMounted(() => {
  if (!store.job?.job_id) return;
  if (downloadLink.value || qrUrl.value) return;

  pollTries = 0;
  pollJobForDrive();
  pollTimer = setInterval(pollJobForDrive, 2000);
});

onBeforeUnmount(() => {
  stopPolling();
});

function handleFinish() {
  router.push({ name: "Welcome" });
}
</script>

<template>
  <div class="result-page">
    <h1 class="result-title">This Is Yours</h1>
    <div v-if="resultUrl">
      <img :src="resultUrl" style="max-width: 700px" />
    </div>
    <div class="action-button">
      <img
        v-if="singleQrCode"
        @click="openQrModal"
        src="../assets/ui/qrcode.png"
      />
      <img v-else src="../assets/ui/loading.gif" alt="loading" />
      <img src="../assets/ui/done.png" @click="openFModal" />
      <img
        src="../assets/ui/print.png"
        @click="openPrintingModal"
        alt="print"
      />
    </div>

    <div v-if="isQrOpen" class="modal" @click.self="closeQrModal">
      <div class="modal-content">
        <img
          v-if="qrImageUrl"
          :src="qrImageUrl"
          @click="closeQrModal"
          alt="QR Code"
        />
        <p v-else class="muted">QR code belum tersedia.</p>
      </div>
    </div>

    <div v-if="isFmodalOpen" class="modal">
      <div class="modal-content">
        <span>END THE SESSION ?</span>
        <div class="end-confirmation">
          <button class="btn" @click="handleFinish">YES</button>
          <button class="btn" @click="closeFModal">NO</button>
        </div>
      </div>
    </div>

    <div v-if="isPrintingModalOpen" class="modal">
      <div class="modal-content">
        <span>DO YOU WANT TO PRINT ?</span>
        <div class="end-confirmation">
          <button class="btn" @click="confirmPrinting">YES</button>
          <button class="btn" @click="closePrintingModal">NO</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.result-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding-bottom: 1rem;
}

.result-title {
  color: white;
  font-size: 5rem;
}

.action-button {
  display: flex;
  padding-top: 2rem;
  gap: 1rem;
}

.action-button > img {
  max-width: 125px;
  height: auto;
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
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  width: 80%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  font-size: 4rem;
}

.modal-content img {
  width: 100%;
  height: auto;
  border-radius: 8px;
  display: block;
}

.modal-close {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  border: none;
  background: #111827;
  color: #ffffff;
  cursor: pointer;
  line-height: 1;
}

.muted {
  color: #6b7280;
}

.end-confirmation {
  display: flex;
  gap: 1rem;

}
</style>
