<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getDriveStatus } from "../api/seeddream";

const router = useRouter();
const checkingDrive = ref(true);
const driveOk = ref(false);
const driveStatus = ref("");
const driveDetail = ref("");

const handleNext = () => router.push({ name: "Register" });

async function loadDriveStatus() {
  checkingDrive.value = true;
  driveOk.value = false;
  driveStatus.value = "";
  driveDetail.value = "";

  try {
    const status = await getDriveStatus();

    driveOk.value = Boolean(status?.ok);
    if (driveOk.value) {
      return;
    }

    driveStatus.value = status?.message || "DRIVE TOKEN EXPIRED";
    const parts = [];
    if (status?.status) parts.push(`status: ${status.status}`);
    if (status?.expiry) parts.push(`expiry: ${status.expiry}`);
    if (status?.checked_at) parts.push(`checked: ${status.checked_at}`);
    driveDetail.value = parts.join(" | ");
  } catch (err) {
    driveStatus.value = "Failed to check Google Drive authorization.";
    driveDetail.value = err?.message || "";
  } finally {
    checkingDrive.value = false;
  }
}

onMounted(() => {
  loadDriveStatus();
});
</script>
<template>
  <div id="welcome">
    <h1 class="driveLog" v-if="checkingDrive">Checking Google Drive authorization...</h1>
    <div v-else-if="!driveOk" class="drive-warning">
      <h1 class="driveLog">{{ driveStatus }}</h1>
      <p v-if="driveDetail" class="driveDetail">{{ driveDetail }}</p>
      <button class="btn retryBtn" @click="loadDriveStatus">Recheck Drive</button>
    </div>
    <img v-else @click="handleNext" src="../assets/ui/tap.png" alt="tap-button" />
  </div>
</template>
<style>
#welcome {
  display: flex;
  flex-direction: column;
  padding-bottom: 13rem;
  padding-top: 5rem;
}

.driveLog {
  text-align: center;
  color: red;
  background-color: aliceblue;
  width: 100vw;
}

.drive-warning {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.driveDetail {
  color: white;
  font-size: 1.5rem;
  text-align: center;
  padding: 0 20px;
}

.retryBtn {
  font-size: 2rem;
}
</style>
