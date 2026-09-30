<template>
  <aside class="top-options">
    <div class="top-options-header">
      <h3 class="top-options-title">Top options for you</h3>
      <span class="filter-badge">{{ total }} results</span>
    </div>

    <ol class="top-options-list">
      <li
        v-for="r in results"
        :key="r.listingid"
        class="option-row"
        :class="{ selected: r.listingid === selectedId, featured: r.featured }"
        @click="$emit('select', r)"
      >
        <span class="option-rank" :style="{ background: colorFor(r) }">{{ r.rank }}</span>
        <div class="option-body">
          <div class="option-top">
            <span class="option-address">{{ titleCase(r.listingaddress) }}</span>
            <span v-if="r.featured" class="option-featured"><i class="fa-solid fa-star"></i> Featured</span>
          </div>
          <div class="option-meta">
            <span class="option-rent">${{ Math.round(r.rent_per_person ?? 0) }}<small>/person</small></span>
            <span class="option-dot">·</span>
            <span>{{ r.available_bedrooms }} bed</span>
            <span class="option-dot">·</span>
            <span><i class="fa-solid fa-person-walking"></i> {{ Math.round(r.walk) }} min</span>
          </div>
          <div class="option-reason">
            <span class="option-badge" :class="badgeClass(r)">{{ badgeText(r) }}</span>
            <span class="option-why">{{ r.reason }}</span>
          </div>
        </div>
        <i class="fa-solid fa-chevron-right option-chevron"></i>
      </li>
    </ol>
  </aside>
</template>

<script setup lang="ts">
import type { RankedListing } from './data';
import { getColor, titleCase } from '@/utils/complexes';

defineProps<{
  results: RankedListing[];
  total: number;
  selectedId?: string;
}>();

defineEmits<{ (e: 'select', listing: RankedListing): void }>();

function colorFor(r: RankedListing): string {
  return getColor(r.rent_per_person, r.predictedrent);
}

function badgeClass(r: RankedListing): string {
  if (r.percent === null) return 'none';
  if (r.percent > 3) return 'under';
  if (r.percent < -3) return 'over';
  return 'fair';
}

function badgeText(r: RankedListing): string {
  const c = badgeClass(r);
  return c === 'under' ? 'Underpriced' : c === 'over' ? 'Overpriced' : c === 'fair' ? 'Fair price' : 'No estimate';
}
</script>

<style scoped>
.top-options {
  position: absolute;
  top: 82px;
  left: 20px;
  z-index: 1000;
  width: 360px;
  max-height: calc(100vh - 290px);
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: black;
  overflow: hidden;
}

.top-options-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #e2e8f0;
}

.top-options-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #000;
  margin: 0;
}

.filter-badge {
  background: #10b981;
  color: white;
  border-radius: 12px;
  padding: 4px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
}

.top-options-list {
  list-style: none;
  margin: 0;
  padding: 6px 0;
  overflow-y: auto;
}

.option-row {
  display: grid;
  grid-template-columns: 30px 1fr 14px;
  gap: 12px;
  align-items: center;
  padding: 10px 16px 10px 20px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background 0.15s ease;
}

.option-row:hover { background: #f8fafc; }
.option-row.selected { background: #eff6ff; border-left-color: #1d4ed8; }
.option-row.featured { background: linear-gradient(90deg, #fffbeb 0%, #ffffff 60%); }
.option-row.featured.selected { background: #eff6ff; }

.option-rank {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 700;
  color: #111;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.option-body { min-width: 0; }

.option-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}

.option-address {
  font-weight: 600;
  font-size: 0.95rem;
  color: #111;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.option-featured {
  font-size: 0.68rem;
  font-weight: 700;
  color: #b45309;
  background: #fef3c7;
  border-radius: 999px;
  padding: 2px 8px;
  white-space: nowrap;
}

.option-meta {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 0.82rem;
  color: #374151;
  margin-top: 2px;
}

.option-rent { font-weight: 700; color: #111; }
.option-rent small { font-weight: 400; color: #6b7280; margin-left: 1px; }
.option-dot { color: #9ca3af; }

.option-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 4px;
  font-size: 0.75rem;
  color: #6b7280;
}

.option-badge {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 999px;
  white-space: nowrap;
}
.option-badge.under { background: #dcfce7; color: #16a34a; }
.option-badge.over { background: #fee2e2; color: #dc2626; }
.option-badge.fair { background: #f1f5f9; color: #111; }
.option-badge.none { background: #f1f5f9; color: #6b7280; }

.option-why { line-height: 1.3; }

.option-chevron { color: #cbd5e1; font-size: 0.7rem; }
</style>
