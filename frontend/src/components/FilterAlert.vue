<template>
  <div class="filter-alert" :class="`filter-alert-${kind}`" role="alert">
    <!-- Static classes: FontAwesome's dom.watch swaps each <i> for an <svg> once -->
    <i v-if="kind === 'error'" class="fa-solid fa-circle-exclamation filter-alert-icon"></i>
    <i v-else class="fa-solid fa-triangle-exclamation filter-alert-icon"></i>

    <!-- A filter's data failed to load -->
    <div v-if="kind === 'error'" class="filter-alert-body">
      <strong>Couldn't load the {{ filterLabel(filterKey ?? '') }} filter right now.</strong>
      <span>It's turned off, so the map is showing listings without it. Try again in a bit.</span>
    </div>

    <!-- The filters loaded but nothing passes all of them -->
    <div v-else class="filter-alert-body">
      <strong>No listings match your filters.</strong>
      <span v-if="suggestion">Here's the smallest change that finds some:</span>
      <span v-else>No single change brings any back.</span>
    </div>

    <button v-if="kind === 'error'" class="filter-alert-close" type="button" aria-label="Dismiss" @click="$emit('dismiss')">×</button>
    <button v-else-if="suggestion" class="filter-alert-btn" type="button" @click="$emit('relax')">
      {{ actionText }} → {{ suggestion.count }} {{ suggestion.count === 1 ? 'listing' : 'listings' }}
    </button>
    <button v-else class="filter-alert-btn" type="button" @click="$emit('reset')">Reset all filters</button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { filterLabel, type RelaxSuggestion } from '@/utils/filters';

const props = defineProps<{
  kind: 'empty' | 'error';
  filterKey?: string | null; // for 'error': which filter failed
  suggestion?: RelaxSuggestion | null; // for 'empty': the one-click fix, if any
}>();
defineEmits<{ (e: 'relax'): void; (e: 'reset'): void; (e: 'dismiss'): void }>();

// Step suggestions only come from the commute max-time dropdown, so they are in minutes
const actionText = computed(() => {
  const s = props.suggestion;
  if (!s) return '';
  return s.kind === 'step' ? `Allow up to ${s.value} min` : `Remove ${filterLabel(s.key)} filter`;
});
</script>

<style scoped>
.filter-alert {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
  font-size: 0.9rem;
  pointer-events: auto;
}

/* Nothing matches: orange, it's the filters */
.filter-alert-empty {
  background: #fff7ed;
  border: 1px solid #fdba74;
  border-left: 5px solid #ea580c;
  color: #7c2d12;
}

/* A filter failed to load: red, it's us */
.filter-alert-error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-left: 5px solid #dc2626;
  color: #7f1d1d;
}

.filter-alert-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
}

.filter-alert-empty .filter-alert-icon { color: #ea580c; }
.filter-alert-error .filter-alert-icon { color: #dc2626; }

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
  transition: background 0.2s ease;
}

.filter-alert-btn:hover {
  background: #c2410c;
}

.filter-alert-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  color: inherit;
  cursor: pointer;
  padding: 0 4px;
}
</style>
