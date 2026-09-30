<template>
  <div class="filter-alert" role="alert">
    <i class="fa-solid fa-triangle-exclamation filter-alert-icon"></i>
    <div class="filter-alert-body">
      <strong>No matches.</strong>
      <span v-if="suggestion">
        A <strong>{{ suggestion.maxWalk }} min</strong> walk would give {{ suggestion.count }} {{ suggestion.count === 1 ? 'listing' : 'listings' }}.
      </span>
      <span v-else>Try a higher budget or fewer bedrooms.</span>
    </div>
    <button v-if="suggestion" class="filter-alert-btn" type="button" @click="$emit('relax')">
      Use {{ suggestion.maxWalk }} min
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Criteria, RelaxSuggestion } from './data';

defineProps<{ criteria: Criteria; suggestion: RelaxSuggestion | null }>();
defineEmits<{ (e: 'relax'): void }>();
</script>

<style scoped>
.filter-alert {
  position: absolute;
  top: 262px;
  left: 50%;
  transform: translateX(-50%);
  width: min(640px, calc(100vw - 40px));
  z-index: 1001;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: #fff7ed;
  border: 1px solid #fdba74;
  border-left: 5px solid #ea580c;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
  color: #7c2d12;
  font-size: 0.9rem;
}

.filter-alert-icon { color: #ea580c; font-size: 1.3rem; }

.filter-alert-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.4;
}

.filter-alert-btn {
  padding: 8px 14px;
  background: #ea580c;
  color: white;
  border: none;
  border-radius: 8px;
  font: inherit;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
}
</style>
