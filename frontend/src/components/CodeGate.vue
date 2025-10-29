<template>
  <div class="code-gate-container">
    <div class="code-gate-content">
      <h2>Analytics Access</h2>
      <p class="subtitle">Please enter the 6-digit code to access this section</p>
      
      <form @submit.prevent="checkCode" class="code-form">
        <div class="input-group">
          <input
            v-model="code"
            type="text"
            maxlength="6"
            placeholder="Enter 6-digit code"
            class="code-input"
            :class="{ 'error': errorMessage }"
            @input="errorMessage = ''"
            autocomplete="off"
          />
        </div>
        
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
        
        <button type="submit" class="submit-button" :disabled="isLoading">
          {{ isLoading ? 'Checking...' : 'Submit' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const code = ref('');
const errorMessage = ref('');
const isLoading = ref(false);
const ACCESS_CODE = '420677';

const checkCode = () => {
  isLoading.value = true;
  
  // Simulate small delay for better UX
  setTimeout(() => {
    if (code.value === ACCESS_CODE) {
      // Store authentication in sessionStorage
      sessionStorage.setItem('analytics_authenticated', 'true');
      // Reload to refresh the auth state
      window.location.reload();
    } else {
      errorMessage.value = 'Invalid code. Please try again.';
      code.value = '';
    }
    isLoading.value = false;
  }, 300);
};
</script>

<style scoped>
.code-gate-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
  box-sizing: border-box;
}

.code-gate-content {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 100%;
}

h2 {
  margin: 0 0 8px 0;
  font-size: 1.75rem;
  font-weight: bold;
  color: #151366;
  text-align: center;
}

.subtitle {
  margin: 0 0 32px 0;
  color: #666;
  text-align: center;
  font-size: 0.95rem;
}

.code-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-group {
  display: flex;
  flex-direction: column;
}

.code-input {
  padding: 14px 16px;
  font-size: 0.8rem;
  text-align: center;
  letter-spacing: 8px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  transition: border-color 0.2s;
  font-family: 'Monaco', 'Courier New', monospace;
}

.code-input:focus {
  outline: none;
  border-color: #1d4ed8;
}

.code-input.error {
  border-color: #ef4444;
}

.error-message {
  color: #ef4444;
  font-size: 0.875rem;
  text-align: center;
  margin-top: -8px;
}

.submit-button {
  padding: 14px;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background-color: #1d4ed8;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.submit-button:hover:not(:disabled) {
  background-color: #1e40af;
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .code-gate-content {
    padding: 24px;
  }

  h2 {
    font-size: 1.5rem;
  }

  .code-input {
    font-size: 1rem;
    letter-spacing: 4px;
  }
}
</style>

