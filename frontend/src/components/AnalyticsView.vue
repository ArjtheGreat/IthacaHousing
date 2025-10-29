<template>
  <div>
    <NavBar />
    <div v-if="isAuthenticated" style="margin-top: 60px;">
      <InsideIthacaView />
    </div>
    <CodeGate v-else />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import NavBar from './NavBar.vue';
import CodeGate from './CodeGate.vue';
import InsideIthacaView from './InsideIthacaView.vue';

const router = useRouter();
const isAuthenticated = ref(false);

const checkAuth = () => {
  const auth = sessionStorage.getItem('analytics_authenticated');
  isAuthenticated.value = auth === 'true';
};

// Watch for changes in sessionStorage
const handleStorageChange = () => {
  checkAuth();
};

onMounted(() => {
  checkAuth();
  // Listen for storage changes (in case user authenticates in another tab)
  window.addEventListener('storage', handleStorageChange);
});

// Also watch sessionStorage manually since storage event doesn't fire in same tab
setInterval(() => {
  checkAuth();
}, 500);
</script>

