<template>
  <div class="story">
    <div class="story-meta">
      <span class="story-kicker"><i class="fa-solid fa-clapperboard"></i> Design walkthrough</span>
      <span class="story-count">{{ index + 1 }} / {{ frames.length }}</span>
      <div class="story-dots">
        <button
          v-for="(f, i) in frames"
          :key="f.id"
          class="story-dot"
          :class="{ active: i === index }"
          type="button"
          :title="f.title"
          @click="$emit('go', i)"
        ></button>
      </div>
    </div>
    <div class="story-text">
      <h2 class="story-title">{{ frame.title }}</h2>
      <p class="story-caption">{{ frame.caption }}</p>
    </div>
    <div class="story-nav">
      <button class="story-btn" type="button" :disabled="index === 0" @click="$emit('go', index - 1)">
        <i class="fa-solid fa-arrow-left"></i> Back
      </button>
      <button class="story-btn primary" type="button" :disabled="index === frames.length - 1" @click="$emit('go', index + 1)">
        Next <i class="fa-solid fa-arrow-right"></i>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Frame } from './story';

const props = defineProps<{ frames: Frame[]; index: number }>();
defineEmits<{ (e: 'go', index: number): void }>();

const frame = computed(() => props.frames[props.index]);
</script>

<style scoped>
.story {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  min-height: 104px;
  z-index: 1002;
  display: grid;
  grid-template-columns: 170px 1fr auto;
  gap: 24px;
  align-items: center;
  padding: 14px 24px;
  background: rgba(17, 24, 39, 0.94);
  backdrop-filter: blur(10px);
  color: white;
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.25);
}

.story-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #9ca3af;
}

.story-kicker i { color: #fbbf24; margin-right: 4px; }
.story-count { font-size: 1.1rem; font-weight: 700; color: white; letter-spacing: 0; }

.story-text { min-width: 0; }

.story-title {
  margin: 0 0 2px;
  font-size: 1.05rem;
  font-weight: 700;
}

.story-caption {
  margin: 0;
  font-size: 0.86rem;
  line-height: 1.45;
  color: #e5e7eb;
}

.story-nav { display: flex; gap: 8px; }

.story-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.story-btn.primary { background: #1d4ed8; border-color: #1d4ed8; }
.story-btn:disabled { opacity: 0.35; cursor: default; }

.story-dots { display: flex; gap: 5px; }

.story-dot {
  width: 8px;
  height: 8px;
  padding: 0;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.3);
  cursor: pointer;
}

.story-dot.active { background: #fbbf24; }

@media (max-width: 900px) {
  .story { grid-template-columns: 1fr; gap: 8px; }
}
</style>
