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
