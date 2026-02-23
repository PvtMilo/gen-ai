<script setup>
import { ref, onMounted } from "vue";
import { useSeedDreamStore } from "../stores/seeddreamStore";

const assetBase = import.meta.env.VITE_ASSET_BASE || "http://127.0.0.1:8000";
const store = useSeedDreamStore();

const themeName = ref("");
const prompt = ref("");
const negativePrompt = ref("");
const ismodalOpen = ref(false);
const isAddingNewTheme = ref(false);
const isAddingThemeImage = ref(false);
const addImagePath = ref("../assets/ui/add-image.png");

const handleAddImage = () => {
  isAddingThemeImage.value = true;
  addImagePath.value = "../assset/image-b.png";
};

function thumbUrl(t) {
  return t.thumbnail_url ? `${assetBase}${t.thumbnail_url}` : "";
}

const openModal = () => {
  ismodalOpen.value = true;
};

const closeModal = () => {
  ismodalOpen.value = false;
};

const handleAddNewTheme = () => {
  isAddingNewTheme.value = true;
  openModal();
};

const imageUrl = ref("");
const imageFile = ref(""); // To store the file object for upload

function onFileChange(e) {
  const file = e.target.files?.[0];
  if (!file) return;

  imageFile.value = file;

  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value); // bersihin url lama
  imageUrl.value = URL.createObjectURL(file);
}

onMounted(async () => {
  await store.loadThemesInternal();
});
</script>
<template>
  <section id="ThemeSetting">
    <h1>ThemeSetting</h1>
    <div class="grid">
      <div class="theme-wrapper" v-for="t in store.themes" :key="t.id">
        <button>EDIT</button>
        <img
          v-if="t.thumbnail_url"
          :src="thumbUrl(t)"
          class="thumb"
          alt="theme thumbnail"
        />
        <div class="prompt-wrapper">
          <p><strong>Prompt:</strong> {{ t.prompt }}</p>
          <p v-if="t.negative_prompt">
            <strong>Negative:</strong> {{ t.negative_prompt }}
          </p>
        </div>
      </div>
      <div class="add-theme-wrapper">
        <button @click="handleAddNewTheme">ADD NEW THEME</button>
        <div v-if="isAddingNewTheme">
          <div v-if="ismodalOpen" class="modal">
            <div class="complete-form">
              <h1>Add New Theme</h1>
              <div class="insert-theme-wrapper">
                <div class="insert-theme-image">
                  <input
                    type="file"
                    accept="image/*"
                    @change="onFileChange"
                    ref="fileInput"
                  />
                  <div v-if="imageUrl">
                    <img
                      :src="imageUrl"
                      alt="Preview"
                      class="uploading-image"
                    />
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
                  </div>
                </div>
              </div>
              <div class="button-wrapper">
                <button class="btn" @click="closeModal">Cancel</button>
                <button class="btn">Save</button>
              </div>
            </div>
          </div>
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
  overflow-y: auto;
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
  min-height: 50%;
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
</style>
