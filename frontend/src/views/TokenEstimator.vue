<script setup>
import { computed, ref } from "vue";
import {
  executeEventDelete,
  exportTokenEstimatorCsv,
  getTokenEstimatorReport,
  previewEventDelete,
} from "../api/seeddream";

function wibTodayIsoDate() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Jakarta",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

function currencyUsd(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

const startDate = ref(wibTodayIsoDate());
const endDate = ref(wibTodayIsoDate());
const password = ref("");

const loadingReport = ref(false);
const exporting = ref(false);
const previewing = ref(false);
const executing = ref(false);

const error = ref("");
const info = ref("");

const rows = ref([]);
const summary = ref({
  total_requests: 0,
  price_per_req: 0.04,
  total_cost: 0,
  currency: "USD",
});

const preview = ref(null);
const canConfirmDelete = computed(() => {
  return !!preview.value && !executing.value;
});

function validateRange() {
  if (!startDate.value || !endDate.value) {
    error.value = "start_date and end_date are required";
    return false;
  }

  if (endDate.value < startDate.value) {
    error.value = "end_date must be >= start_date";
    return false;
  }

  return true;
}

async function loadReport() {
  error.value = "";
  info.value = "";

  if (!validateRange()) return;

  loadingReport.value = true;
  preview.value = null;

  try {
    const data = await getTokenEstimatorReport(startDate.value, endDate.value);
    rows.value = Array.isArray(data?.rows) ? data.rows : [];
    summary.value = data?.summary || {
      total_requests: 0,
      price_per_req: 0.04,
      total_cost: 0,
      currency: "USD",
    };
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || "Failed to load report";
  } finally {
    loadingReport.value = false;
  }
}

async function onExportCsv() {
  error.value = "";
  info.value = "";

  if (!validateRange()) return;

  exporting.value = true;

  try {
    const blob = await exportTokenEstimatorCsv(startDate.value, endDate.value);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `token_estimator_${startDate.value}_${endDate.value}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || "Failed to export CSV";
  } finally {
    exporting.value = false;
  }
}

async function onPreviewDelete() {
  error.value = "";
  info.value = "";

  if (!validateRange()) return;
  if (!password.value) {
    error.value = "Password is required for delete preview";
    return;
  }

  previewing.value = true;

  try {
    preview.value = await previewEventDelete(startDate.value, endDate.value, password.value);
  } catch (err) {
    preview.value = null;
    error.value = err?.response?.data?.detail || err?.message || "Failed to preview delete";
  } finally {
    previewing.value = false;
  }
}

async function onConfirmDelete() {
  error.value = "";
  info.value = "";

  if (!validateRange()) return;
  if (!password.value) {
    error.value = "Password is required for delete execution";
    return;
  }

  executing.value = true;

  try {
    const result = await executeEventDelete(startDate.value, endDate.value, password.value);
    info.value = `Deleted jobs: ${result.jobs_deleted_count}, sessions: ${result.sessions_deleted_count}, users: ${result.users_deleted_count}, files deleted: ${result.result_files_deleted_count}/${result.result_files_target_count}`;
    preview.value = null;
    await loadReport();
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || "Failed to execute delete";
  } finally {
    executing.value = false;
  }
}
</script>

<template>
  <section class="token-estimator">
    <h1>Token Estimator</h1>

    <div class="controls">
      <label>
        <span>Start Date (WIB)</span>
        <input v-model="startDate" type="date" />
      </label>

      <label>
        <span>End Date (WIB)</span>
        <input v-model="endDate" type="date" />
      </label>

      <button class="btn" @click="loadReport" :disabled="loadingReport">
        {{ loadingReport ? "Loading..." : "Load Report" }}
      </button>

      <button class="btn" @click="onExportCsv" :disabled="exporting || loadingReport">
        {{ exporting ? "Exporting..." : "Export CSV" }}
      </button>
    </div>

    <div class="summary">
      <p>Total Requests: {{ summary.total_requests }}</p>
      <p>Price / Req: {{ currencyUsd(summary.price_per_req) }}</p>
      <p>Total Cost: {{ currencyUsd(summary.total_cost) }}</p>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>id</th>
            <th>user_name</th>
            <th>user_id</th>
            <th>mode</th>
            <th>error</th>
            <th>price per req</th>
            <th>timestamp</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!loadingReport && rows.length === 0">
            <td colspan="7">No data in selected range.</td>
          </tr>
          <tr v-for="row in rows" :key="row.id">
            <td>{{ row.id }}</td>
            <td>{{ row.user_name }}</td>
            <td>{{ row.user_id }}</td>
            <td>{{ row.mode }}</td>
            <td>{{ row.error || "-" }}</td>
            <td>{{ currencyUsd(row.price_per_req) }}</td>
            <td>{{ row.timestamp }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="delete-box">
      <h2>Bulk Delete (Event Data)</h2>
      <label>
        <span>Password</span>
        <input v-model="password" type="password" placeholder="Enter admin password" />
      </label>

      <div class="delete-actions">
        <button class="btn danger" @click="onPreviewDelete" :disabled="previewing || executing">
          {{ previewing ? "Previewing..." : "Preview Delete" }}
        </button>
        <button class="btn danger" @click="onConfirmDelete" :disabled="!canConfirmDelete">
          {{ executing ? "Deleting..." : "Confirm Delete" }}
        </button>
      </div>

      <div v-if="preview" class="preview">
        <p>Jobs: {{ preview.jobs_count }}</p>
        <p>Result files: {{ preview.result_files_count }}</p>
        <p>Sessions to delete: {{ preview.sessions_to_delete_count }}</p>
        <p>Users to delete: {{ preview.users_to_delete_count }}</p>
        <p>Missing files: {{ preview.missing_files_count }}</p>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="info" class="info">{{ info }}</p>
  </section>
</template>

<style scoped>
.token-estimator {
  width: min(1200px, 96vw);
  margin: 0 auto;
  padding: 1rem;
  color: white;
}

h1,
h2 {
  margin: 0 0 0.75rem 0;
}

.controls {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
  align-items: end;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

input,
button {
  font-size: 1rem;
}

.summary {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin: 0.75rem 0;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
}

th,
td {
  border: 1px solid rgba(255, 255, 255, 0.35);
  padding: 0.45rem;
  text-align: left;
  white-space: nowrap;
}

.delete-box {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.delete-actions {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.preview {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.4rem 1rem;
}

.error {
  color: #ff7b7b;
}

.info {
  color: #9ef0b3;
}

@media (max-width: 900px) {
  .controls {
    grid-template-columns: 1fr 1fr;
  }

  .preview {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .controls {
    grid-template-columns: 1fr;
  }

  .summary {
    flex-direction: column;
    gap: 0.3rem;
  }
}
</style>
