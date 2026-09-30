<template>
  <aside class="detail-panel">
    <div class="popup-header">
      <div class="popup-title-row">
        <h3 class="popup-title">{{ titleCase(listing.listingaddress) }}, Ithaca</h3>
        <button class="close-btn" type="button" @click="$emit('close')">✖</button>
      </div>
    </div>

    <!-- Stage 1 of "show the actual listing": link out. -->
    <div class="listing-actions">
      <a class="listing-link" href="#" @click.prevent>
        <i class="fa-solid fa-arrow-up-right-from-square"></i>
        View original listing
      </a>
      <div class="listing-stage2">
        <i class="fa-solid fa-flag"></i>
        <span><strong>Stage 2:</strong> this becomes our own listing page, with photos, contact and an apply link.</span>
      </div>
    </div>

    <div class="photo-placeholder">
      <i class="fa-solid fa-image"></i>
      <span>Photos from the listing</span>
    </div>

    <div class="rent-main-card">
      <h4 class="rent-comparison-title">Fair Rent Comparison</h4>
      <div class="rent-comparison-grid">
        <div class="rent-column">
          <span class="column-label">Actual Rent</span>
          <div class="rent-amount-large">${{ fmt(listing.rent_per_person) }}</div>
          <div class="rent-label-small">per person</div>
        </div>
        <div class="rent-column">
          <span class="column-label">Fair Rent Estimation</span>
          <div class="rent-amount-large">${{ fmt(listing.predictedrent) }}</div>
          <div class="rent-label-small">per person</div>
          <div class="difference-badge" :class="percent >= 0 ? 'badge-underpriced' : 'badge-overpriced'">
            {{ Math.abs(percent).toFixed(1) }}% {{ percent >= 0 ? 'Underpriced' : 'Overpriced' }}
          </div>
        </div>
      </div>
    </div>

    <div class="details-grid">
      <div class="detail-card">
        <i class="fa-solid fa-bed detail-icon"></i>
        <div class="detail-number">{{ listing.available_bedrooms }} Bedrooms</div>
      </div>
      <div class="detail-card">
        <i class="fa-solid fa-person-walking detail-icon"></i>
        <div class="detail-number">{{ Math.round(listing.walk) }} min to {{ QUAD_LABEL[quad] }}</div>
      </div>
    </div>

    <div class="commute-list">
      <strong>Getting to class</strong>
      <div class="commute-row"><span><i class="fa-solid fa-cogs"></i> Eng Quad</span><span>{{ mins(listing.walk_time_engineeringquad) }} walk · {{ mins(listing.bike_time_engineeringquad) }} bike</span></div>
      <div class="commute-row"><span><i class="fa-solid fa-book"></i> Arts Quad</span><span>{{ mins(listing.walk_time_artsquad) }} walk</span></div>
      <div class="commute-row"><span><i class="fa-solid fa-seedling"></i> Ag Quad</span><span>{{ mins(listing.walk_time_agriculturequad) }} walk</span></div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { QUAD_LABEL, type Quad, type RankedListing } from './data';
import { titleCase } from '@/utils/complexes';

const props = defineProps<{ listing: RankedListing; quad: Quad }>();
defineEmits<{ (e: 'close'): void }>();

const percent = computed(() => {
  const { rent_per_person: rent, predictedrent: fair } = props.listing;
  return rent && fair ? ((fair - rent) / rent) * 100 : 0;
});

const fmt = (n: number | null) => (n ?? 0).toFixed(2);
const mins = (n: number | null) => (n === null ? '—' : `${Math.round(n)} min`);
</script>

<style scoped>
.detail-panel {
  position: absolute;
  top: 82px;
  right: 20px;
  bottom: 124px;
  width: 440px;
  padding: 16px 20px 24px;
  overflow-y: auto;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 999;
  color: #111;
}

.popup-header {
  border-bottom: 2px solid #e5e7eb;
  padding: 8px 0;
  margin-bottom: 12px;
}

.popup-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.popup-title {
  font-size: 1.15rem;
  font-weight: 700;
  margin: 0 0 4px;
  color: #111;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  color: #888;
}

.listing-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.listing-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: #1d4ed8;
  color: white;
  font-weight: 600;
  text-decoration: none;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(29, 78, 216, 0.3);
}

.listing-stage2 {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 8px 10px;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  font-size: 0.78rem;
  color: #6b7280;
}

.listing-stage2 i { color: #d97706; margin-top: 3px; }

.photo-placeholder {
  height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-bottom: 12px;
  border-radius: 12px;
  background: repeating-linear-gradient(45deg, #f1f5f9, #f1f5f9 10px, #f8fafc 10px, #f8fafc 20px);
  color: #94a3b8;
  font-size: 0.85rem;
}

.photo-placeholder i { font-size: 1.6rem; }

.rent-main-card { padding: 8px 0; }

.rent-comparison-title {
  font-size: 1.1rem;
  font-weight: 600;
  text-align: center;
  margin: 0 0 12px;
  letter-spacing: 0.025em;
}

.rent-comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.rent-column {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.column-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

.rent-amount-large {
  font-size: 1.8rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 4px;
}

.rent-label-small { font-size: 0.75rem; color: #6b7280; }

.difference-badge {
  display: inline-flex;
  margin-top: 10px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.badge-underpriced { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); color: #16a34a; border: 1px solid #bbf7d0; }
.badge-overpriced { background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); color: #dc2626; border: 1px solid #fecaca; }

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 12px 0;
}

.detail-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-icon { color: #1d4ed8; font-size: 1.1rem; }
.detail-number { font-weight: 600; font-size: 0.9rem; }

.commute-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.85rem;
}

.commute-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #f1f5f9;
  color: #374151;
}

.commute-row i { color: #d97706; width: 18px; }
</style>
