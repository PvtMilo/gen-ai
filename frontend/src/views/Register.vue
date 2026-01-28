<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useSeedDreamStore } from "../stores/seeddreamStore";
import { computed } from "vue";

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

const fillDummy = computed(() => {
  name.value = "Samuel Debug";
  email.value = "samuel.debug@mail.com";
  phone.value = "081234567890";
});

const handleGallery = () => {
  router.push({ name: "PublicGallery" });
};

const handleSetting = () => {
  router.push({ name: "Setting" });
};

onMounted(() => {
  name.value = "Samuel Debug";
  email.value = "samuel.debug@mail.com";
  phone.value = "081234567890";
});

</script>

<template>
  <h1>Register</h1>
  <div>
    <button @click="handleGallery">gallery</button>
    <button @click="handleSetting">Setting</button>
  </div>
  <div
    style="display: flex; flex-direction: column; gap: 8px; max-width: 320px"
  >
    <input v-model="name" placeholder="Name" />
    <input v-model="email" placeholder="Email" />
    <input v-model="phone" placeholder="Phone" />
    <button @click="fillDummy">fill</button>

    <button @click="submit" :disabled="store.loadingSession">
      {{ store.loadingSession ? "Creating session..." : "Next" }}
    </button>
    <p v-if="store.error" style="color: red">{{ store.error }}</p>
  </div>
</template>
