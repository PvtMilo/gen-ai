<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";

const router = useRouter();
const store = useSeedDreamStore();

const name = ref("");
const email = ref("");
const phone = ref("");

const submit = async () => {
  await store.beginSession({
    name: name.value,
    email: email.value,
    phone: phone.value,
  });
  router.push({ name: "ThemeSelection" });
};

const handleGallery = () => {
  router.push({ name: "PublicGallery" });
};

const handleSetting = () => {
  router.push({ name: "Setting" });
};

const handleBack = () => {
  router.push({name : "Welcome"})
}

onMounted(() => {
  name.value = "Samuel Debug";
  email.value = "samuel.debug@mail.com";
  phone.value = "081234567890";
});
</script>

<template>
  <div id="register">
    <div class="menu">
      <img class="gallery btn-menu" src="../assets/ui/gallery.png" @click="handleGallery"/>
      <img class="setting btn-menu" src="../assets/ui/setting.png" @click="handleSetting"/>
    </div>
    <div class="input">
      <input v-model="name" placeholder="Name" />
      <input v-model="email" placeholder="Email" />
      <input v-model="phone" placeholder="Phone" />
    </div>
    <div class="action-btn">
      <button class="back btn" @click="handleBack">BACK</button>
      <button class="next btn" @click="submit" :disabled="store.loadingSession">
        {{ store.loadingSession ? "NEXT" : "NEXT" }}
      </button>
    </div>
    <p v-if="store.error" style="color: red">{{ store.error }}</p>
  </div>
</template>
<style>
#register {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  font-size: 4rem;
  margin: 4em 0em 4em 0em;
}

.input {
  display: flex;
  flex-direction: column;
  width: 75%;
  font-size: 7rem;
  gap: 4rem;
}

.menu{
  display: flex;
  justify-content: space-between;
  width: 100%;
  position: absolute;
  top: 20px;
  padding: 0.5em;
}

.btn-menu {
  width: 20%;
}
</style>
