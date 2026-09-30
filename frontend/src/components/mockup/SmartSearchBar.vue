<template>
  <div class="smart-search" :class="{ shifted }">
    <div class="smart-search-bar" :class="{ focused: state !== 'idle' }">
      <i class="fa-solid fa-magnifying-glass smart-search-icon"></i>
      <div class="smart-search-input">
        <span v-if="query">{{ query }}</span>
        <span v-else class="smart-search-placeholder">Describe what you're looking for, or type an address…</span>
        <span v-if="state === 'typing'" class="smart-search-caret"></span>
      </div>
      <i v-if="state === 'thinking'" class="fa-solid fa-circle-notch fa-spin smart-search-status"></i>
    </div>

    <transition name="chips">
      <div v-if="state === 'parsed' && chips.length" class="smart-search-chips">
        <button v-for="chip in chips" :key="chip.label" class="smart-chip" :class="{ changed: chip.label === changedChip }" type="button">
          <i class="fa-solid" :class="chip.icon"></i>
          {{ chip.label }}
          <i class="fa-solid fa-pen smart-chip-edit"></i>
        </button>
        <button class="smart-chip smart-chip-add" type="button"><i class="fa-solid fa-plus"></i> Add</button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import type { Chip } from './data';

export type SearchState = 'idle' | 'typing' | 'thinking' | 'parsed';

defineProps<{
  query: string;
  state: SearchState;
  chips: Chip[];
  /** Label of the chip Peter just edited, drawn with emphasis. */
  changedChip?: string;
  /** Slide left to make room for the listing detail card. */
  shifted?: boolean;
}>();
</script>

<style scoped>
.smart-search {
  position: absolute;
  top: 82px;
  left: 50%;
  transform: translateX(-50%);
  width: min(560px, calc(100vw - 40px));
  z-index: 1001;
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}

.smart-search.shifted { transform: translateX(calc(-50% - 60px)); }

.smart-search-bar {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  background: white;
  border: 2px solid #ddd;
  border-radius: 999px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  font-size: 16px;
  color: #111;
  transition: all 0.3s ease;
}

.smart-search-bar.focused {
  border-color: #1d4ed8;
  box-shadow: 0 2px 15px rgba(80, 124, 182, 0.25);
}

.smart-search-icon {
  color: #6b7280;
  flex-shrink: 0;
}

.smart-search-input {
  flex: 1;
  min-height: 24px;
  line-height: 24px;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.smart-search-placeholder {
  color: #9ca3af;
}

.smart-search-caret {
  display: inline-block;
  width: 2px;
  height: 18px;
  margin-left: 1px;
  vertical-align: -3px;
  background: #1d4ed8;
  animation: blink 1s steps(2) infinite;
}

@keyframes blink {
  to { opacity: 0; }
}

.smart-search-status {
  font-size: 1rem;
  color: #1d4ed8;
}

.smart-search-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.smart-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #eff6ff;
  color: #1e3a8a;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  font: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
}

.smart-chip-edit {
  font-size: 0.65rem;
  color: #93c5fd;
}

.smart-chip.changed {
  background: #fef3c7;
  color: #92400e;
  border-color: #fcd34d;
}

.smart-chip-add {
  background: white;
  color: #6b7280;
  border-style: dashed;
  border-color: #cbd5e1;
}

.chips-enter-active { transition: all 0.35s ease; }
.chips-enter-from { opacity: 0; transform: translateY(-6px); }
</style>
