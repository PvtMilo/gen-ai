<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useSeedDreamStore } from "../stores/seeddreamStore";
import { useRouter } from "vue-router";
import Setting from "./Setting.vue";

const router = useRouter();
const assetBase = import.meta.env.VITE_ASSET_BASE || "http://127.0.0.1:8000";
const store = useSeedDreamStore();

const themeName = ref("");
const prompt = ref("");
const negativePrompt = ref("");
const aspectRatio = ref("2:3");
const ismodalOpen = ref(false);
const formMode = ref("create");
const editingThemeId = ref("");
const loadingThemeDetail = ref(false);
const existingThumbnailUrl = ref("");
const savingTheme = ref(false);
const deletingThemeId = ref("");
const formError = ref("");
const actionError = ref("");
const fileInput = ref(null);

function thumbUrl(t) {
  return resolveThumbnailUrl(t.thumbnail_url);
}

function resolveThumbnailUrl(url) {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${assetBase}${url}`;
}

const openModal = () => {
  ismodalOpen.value = true;
};

const closeModal = () => {
  ismodalOpen.value = false;
  resetForm();
};

const handleAddNewTheme = () => {
  actionError.value = "";
  resetForm();
  openModal();
};

const handleBack = () => {
  router.push({ name: "Setting" });
};

const imageUrl = ref("");
const imageFile = ref(null);

function clearPreviewImageUrl() {
  if (
    typeof imageUrl.value === "string" &&
    imageUrl.value.startsWith("blob:")
  ) {
    URL.revokeObjectURL(imageUrl.value);
  }
}

function resetForm() {
  clearPreviewImageUrl();

  themeName.value = "";
  prompt.value = "";
  negativePrompt.value = "";
  aspectRatio.value = "2:3";
  formError.value = "";
  formMode.value = "create";
  editingThemeId.value = "";
  loadingThemeDetail.value = false;
  existingThumbnailUrl.value = "";
  imageUrl.value = "";
  imageFile.value = null;

  if (fileInput.value) {
    fileInput.value.value = "";
  }
}

function onFileChange(e) {
  const file = e.target.files?.[0];
  if (!file) return;

  imageFile.value = file;
  existingThumbnailUrl.value = "";

  clearPreviewImageUrl();
  imageUrl.value = URL.createObjectURL(file);
}

async function handleEditTheme(themeId) {
  actionError.value = "";
  resetForm();
  formMode.value = "edit";
  editingThemeId.value = themeId;
  openModal();

  formError.value = "";
  loadingThemeDetail.value = true;

  try {
    const selectedTheme = await store.loadThemeInternalById(themeId);
    themeName.value = selectedTheme.title || "";
    prompt.value = selectedTheme.prompt || "";
    negativePrompt.value = selectedTheme.negative_prompt || "";
    aspectRatio.value = selectedTheme?.params?.aspect_ratio || "2:3";

    existingThumbnailUrl.value = resolveThumbnailUrl(
      selectedTheme.thumbnail_url,
    );
    imageUrl.value = existingThumbnailUrl.value;
  } catch (_) {
    formError.value = store.error || "Failed to load selected theme.";
  } finally {
    loadingThemeDetail.value = false;
  }
}

async function handleSaveTheme() {
  actionError.value = "";
  formError.value = "";

  const title = themeName.value.trim();
  const promptValue = prompt.value.trim();
  const negativePromptValue = negativePrompt.value.trim();
  const aspectRatioValue = aspectRatio.value.trim() || "2:3";

  if (!title) {
    formError.value = "Theme name is required.";
    return;
  }

  if (!promptValue) {
    formError.value = "Prompt is required.";
    return;
  }

  if (formMode.value === "edit" && !editingThemeId.value) {
    formError.value = "Theme id is missing.";
    return;
  }

  if (formMode.value === "create" && !imageFile.value) {
    formError.value = "Thumbnail image is required.";
    return;
  }

  savingTheme.value = true;

  try {
    if (formMode.value === "edit") {
      await store.updateTheme(editingThemeId.value, {
        title,
        prompt: promptValue,
        negativePrompt: negativePromptValue || "",
        aspectRatio: aspectRatioValue,
        thumbnailFile: imageFile.value || null,
      });
    } else {
      await store.addTheme({
        title,
        prompt: promptValue,
        negativePrompt: negativePromptValue || "",
        aspectRatio: aspectRatioValue,
        thumbnailFile: imageFile.value,
      });
    }

    closeModal();
  } catch (_) {
    formError.value =
      store.error ||
      (formMode.value === "edit"
        ? "Failed to save edited theme."
        : "Failed to create theme.");
  } finally {
    savingTheme.value = false;
  }
}

async function handleDeleteTheme(themeId) {
  actionError.value = "";

  if (!themeId) return;

  const confirmed = window.confirm("Delete this theme?");
  if (!confirmed) return;

  deletingThemeId.value = themeId;

  try {
    await store.deleteTheme(themeId);

    if (
      ismodalOpen.value &&
      formMode.value === "edit" &&
      editingThemeId.value === themeId
    ) {
      closeModal();
    }
  } catch (_) {
    actionError.value = store.error || "Failed to delete theme.";
  } finally {
    deletingThemeId.value = "";
  }
}

onMounted(async () => {
  await store.loadThemesInternal();
});

onBeforeUnmount(() => {
  clearPreviewImageUrl();
});
</script>
<template>
  <section id="ThemeSetting">
    <h1>THEME SETTING</h1>
    <img class="exit" src="../assets/ui/exit.png" @click="handleBack" />
    <p v-if="actionError" class="error-message">
      {{ actionError }}
    </p>
    <div class="grid">
      <div class="theme-wrapper" v-for="t in store.themes" :key="t.id">
        <div class="action-button">
          <button @click="handleEditTheme(t.id)">EDIT</button>
          <button
            :disabled="deletingThemeId === t.id"
            @click="handleDeleteTheme(t.id)"
          >
            {{ deletingThemeId === t.id ? "DELETING..." : "DELETE" }}
          </button>
        </div>
        <img
          v-if="t.thumbnail_url"
          :src="thumbUrl(t)"
          class="thumb"
          alt="theme thumbnail"
        />
        <div class="prompt-wrapper">
          <p><strong>Title:</strong> {{ t.title }}</p>
          <p><strong>Prompt:</strong> {{ t.prompt }}</p>
          <p v-if="t.negative_prompt">
            <strong>Negative:</strong> {{ t.negative_prompt }}
          </p>
        </div>
      </div>
      <div class="add-theme-wrapper">
        <button @click="handleAddNewTheme">ADD NEW THEME</button>
      </div>
    </div>
    <div v-if="ismodalOpen" class="modal">
      <div class="complete-form">
        <h1>{{ formMode === "edit" ? "Edit Theme" : "Add New Theme" }}</h1>
        <p v-if="formMode === 'edit'" class="edit-note">
          Saving will update this theme.
        </p>
        <div v-if="loadingThemeDetail" class="loading-message">
          Loading selected theme...
        </div>
        <div v-else class="insert-theme-wrapper">
          <div class="insert-theme-image">
            <input
              type="file"
              accept="image/*"
              @change="onFileChange"
              ref="fileInput"
            />
            <div v-if="imageUrl">
              <img :src="imageUrl" alt="Preview" class="uploading-image" />
            </div>
          </div>
          <div class="from-wrapper">
            <div class="input-form">
              <label>Nama Tema</label>
              <input v-model="themeName" placeholder="Name Tema" />
              <label>Prompt</label>
              <textarea v-model="prompt" placeholder="Prompt"></textarea>
              <label>Negative prompt</label>
              <textarea v-model="negativePrompt" placeholder="OPTIONAL">
              </textarea>
              <label>Aspect ratio</label>
              <input v-model="aspectRatio" placeholder="2:3" />
              <p v-if="formError" class="error-message">
                {{ formError }}
              </p>
            </div>
          </div>
        </div>
        <div class="button-wrapper">
          <button class="btn" @click="closeModal">Cancel</button>
          <button
            class="btn"
            :disabled="savingTheme || loadingThemeDetail"
            @click="handleSaveTheme"
          >
            {{
              savingTheme
                ? "Saving..."
                : formMode === "edit"
                  ? "Save Changes"
                  : "Save"
            }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
<style scoped>
#ThemeSetting {
  display: flex;
  flex-direction: column;
  border: 2px solid red;
  justify-content: center;
  align-items: center;
  max-height: 80vh;
}

h1,
p,
span,
label {
  color: white;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
  overflow-y: scroll;
  margin: 3rem;
}

.complete-form {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.add-theme-wrapper {
  background-color: rgb(0, 0, 0);
  min-height: 35rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.insert-theme-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  background-color: aqua;
  border: 2px solid green;
  align-items: stretch;
  width: min(1100px, 92vw);
  height: min(75vh, 720px);
}

.insert-theme-image,
.from-wrapper {
  min-height: 0;
  min-width: 0;
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

.form-wrapper {
  background-color: white;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 50%;
  min-width: 80%;
}

.input-form {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: stretch;
  background-color: red;
  border: 2px solid salmon;
  height: 100%;
  width: 100%;
  gap: 10px;
  padding: 16px;
  box-sizing: border-box;
}

.input-form textarea {
  width: 100%;
  min-height: 35%;
  box-sizing: border-box;
}

.insert-theme-image {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  padding: 12px;
  box-sizing: border-box;
  min-height: 0;
}

.insert-theme-image > div {
  flex: 1;
  min-height: 0;
  max-height: 100%;
}

.uploading-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.error-message {
  color: #c1121f;
}

.loading-message,
.edit-note {
  color: white;
}

.exit {
  padding-top: 1rem;
  width: 100px;
}
</style>
