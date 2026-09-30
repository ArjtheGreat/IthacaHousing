<template>
  <NavBar />
  <div class="preview-root">
    <div id="preview-map"></div>

    <SmartSearchBar :query="typedQuery" :state="searchState" :chips="chips" :changed-chip="changedChip" :shifted="!!selected" />

    <transition name="panel">
      <TopOptionsPanel
        v-if="showResults"
        :results="ranked"
        :total="matchCount"
        :selected-id="selected?.listingid"
        @select="select"
      />
    </transition>

    <transition name="panel">
      <ListingDetailPanel v-if="selected" :listing="selected" :quad="criteria.quad" @close="selected = null" />
    </transition>

    <transition name="panel">
      <FilterAlert v-if="showAlert" :criteria="criteria" :suggestion="suggestion" @relax="relaxed = true" />
    </transition>

    <!-- The research legend from today's /rent, shown once so the caption can say where it goes. -->
    <transition name="panel">
      <div v-if="frame.id === 'analytics'" class="legend legend-moving">
        <div class="legend-ribbon"><i class="fa-solid fa-arrow-right"></i> Moves to Analytics</div>
        <div class="legend-header"><h4>Price Differential</h4></div>
        <div class="gradient-bar"></div>
        <div class="gradient-labels"><span>Higher</span><span>Fair Price</span><span>Lower</span></div>
        <div class="legend-disclaimer">Colors show how actual rent compares to fair rent.</div>
      </div>
    </transition>

    <div v-if="!selected" class="map-key">
      <span><i class="fa-solid fa-cogs"></i> Campus quads</span>
      <span><i class="fa-solid fa-bus"></i> TCAT stops</span>
      <span><span class="key-dot"></span> Listings, colored by fair-rent value</span>
    </div>

    <StoryControls :frames="frames" :index="step" @go="go" />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '@fortawesome/fontawesome-svg-core/styles.css';
import NavBar from '@/components/NavBar.vue';
import SmartSearchBar, { type SearchState } from './SmartSearchBar.vue';
import TopOptionsPanel from './TopOptionsPanel.vue';
import ListingDetailPanel from './ListingDetailPanel.vue';
import FilterAlert from './FilterAlert.vue';
import StoryControls from './StoryControls.vue';
import { frames } from './story';
import {
  busStops, chipsFor, listings, matchListings, persona, rankListings, relaxSuggestion, tooStrictCriteria,
  type Criteria, type RankedListing,
} from './data';
import { colorForScore, groupIntoComplexes, getColor } from '@/utils/complexes';
import { compactMarkerSvg } from '@/utils/complexMarker';
import boundaryText from '@/assets/cornell_main_boundary.geojson?raw';

// ---- Story state -------------------------------------------------------------------------

const step = ref(0);
const frame = computed(() => frames[step.value]);

const typedQuery = ref('');
const searchState = ref<SearchState>('idle');
const selected = ref<RankedListing | null>(null);
/** Set when Peter accepts the alert's suggestion in the no-results frame. */
const relaxed = ref(false);

const criteria = computed<Criteria>(() => {
  if (frame.value.id !== 'no-results') return persona.criteria;
  const s = relaxSuggestion(tooStrictCriteria);
  return relaxed.value && s ? { ...tooStrictCriteria, maxWalk: s.maxWalk } : tooStrictCriteria;
});

const chips = computed(() => chipsFor(criteria.value));
const changedChip = computed(() => (frame.value.id === 'no-results' ? chips.value[2].label : undefined));
const ranked = computed(() => rankListings(criteria.value));
const matchCount = computed(() => matchListings(criteria.value).length);
const suggestion = computed(() => relaxSuggestion(criteria.value));

const showResults = computed(() =>
  ['results', 'detail'].includes(frame.value.id) || (frame.value.id === 'no-results' && relaxed.value));
const showAlert = computed(() => frame.value.id === 'no-results' && !relaxed.value);

function go(index: number) {
  step.value = Math.max(0, Math.min(frames.length - 1, index));
}

function select(listing: RankedListing) {
  selected.value = listing;
  map?.flyTo([listing.latitude, listing.longitude], Math.max(map.getZoom(), 16), { duration: 0.6 });
}

// ---- Typing animation --------------------------------------------------------------------

let animationToken = 0;

function typeQuery() {
  const token = ++animationToken;
  typedQuery.value = '';
  searchState.value = 'typing';
  const text = persona.query;
  let i = 0;
  const tick = () => {
    if (token !== animationToken) return;
    typedQuery.value = text.slice(0, ++i);
    if (i < text.length) {
      setTimeout(tick, 28);
    } else {
      searchState.value = 'thinking';
      setTimeout(() => { if (token === animationToken) searchState.value = 'parsed'; }, 900);
    }
  };
  setTimeout(tick, 400);
}

// ---- Map ---------------------------------------------------------------------------------

let map: L.Map | null = null;
const listingLayer = L.layerGroup();
const rankLayer = L.layerGroup();

const HOME_VIEW: { center: L.LatLngExpression; zoom: number } = { center: [42.4435, -76.4865], zoom: 15 };

function buildMap() {
  map = L.map('preview-map', { ...HOME_VIEW, maxZoom: 20, zoomControl: false });
  L.control.zoom({ position: 'bottomleft' }).addTo(map);

  const key = import.meta.env.VITE_JAWG_API_KEY;
  const tiles = key
    ? L.tileLayer(`https://tile.jawg.io/f67529a2-5ea7-4b7a-81a7-c5147a45b5f0/{z}/{x}/{y}{r}.png?access-token=${key}`, {
        attribution: '<a href="https://jawg.io" target="_blank">&copy; Jawg Maps</a> &copy; OpenStreetMap contributors',
        maxZoom: 22,
      })
    : L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        maxZoom: 20,
      });
  tiles.addTo(map);

  L.geoJSON(JSON.parse(boundaryText), {
    style: { color: '#d97706', weight: 3, opacity: 0.8, fillOpacity: 0 },
  }).addTo(map);

  addQuadIcons();
  addBusStops();
  addListingDots();
  listingLayer.addTo(map);
  rankLayer.addTo(map);
}

/** Same quad markers as MapView.vue. */
function addQuadIcons() {
  const quads: { name: string; coordinates: L.LatLngExpression; icon: string }[] = [
    { name: 'Ag Quad', coordinates: [42.448796, -76.478018], icon: 'fas fa-seedling' },
    { name: 'Arts Quad', coordinates: [42.448966, -76.484175], icon: 'fas fa-book' },
    { name: 'Eng Quad', coordinates: [42.444668, -76.48257], icon: 'fas fa-cogs' },
  ];
  for (const quad of quads) {
    const icon = L.divIcon({
      html: `<div class="quad-marker"><i class="${quad.icon}"></i></div>`,
      className: 'quad-icon',
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
    L.marker(quad.coordinates, { icon }).bindTooltip(quad.name, { direction: 'top', offset: [0, -14] }).addTo(map!);
  }
}

/** Always visible, so there is no "points of interest" toggle to find. */
function addBusStops() {
  for (const stop of busStops) {
    const icon = L.divIcon({
      html: '<div class="bus-marker"><i class="fas fa-bus"></i></div>',
      className: 'bus-icon',
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    });
    L.marker([stop.lat, stop.lng], { icon }).bindTooltip(`TCAT · ${stop.name}`, { direction: 'top', offset: [0, -8] }).addTo(map!);
  }
}

/** One dot per building, colored by typical fair-rent value, exactly like the zoomed-out /rent map. */
function addListingDots() {
  for (const complex of groupIntoComplexes(listings)) {
    const art = compactMarkerSvg(complex.count, colorForScore(complex.medianScore), complex.address);
    const icon = L.divIcon({ html: art.html, className: 'complex-icon', iconSize: [art.size, art.size] });
    L.marker([complex.lat, complex.lng], { icon, interactive: false }).addTo(listingLayer);
  }
}

function drawRankedMarkers() {
  rankLayer.clearLayers();
  if (!showResults.value) return;
  for (const r of ranked.value) {
    const color = getColor(r.rent_per_person, r.predictedrent);
    const isSelected = r.listingid === selected.value?.listingid;
    const icon = L.divIcon({
      html: `<div class="rank-marker${isSelected ? ' selected' : ''}" style="background:${color}">${r.rank}</div>`,
      className: 'rank-icon',
      iconSize: [30, 30],
      iconAnchor: [15, 15],
    });
    L.marker([r.latitude, r.longitude], { icon, zIndexOffset: 1000 - r.rank })
      .bindTooltip(`#${r.rank} · ${r.reason}`, { direction: 'top', offset: [0, -12] })
      .on('click', () => select(r))
      .addTo(rankLayer);
  }
}

function fitRanked() {
  if (!map || ranked.value.length === 0) return;
  const bounds = L.latLngBounds(ranked.value.map(r => [r.latitude, r.longitude] as L.LatLngTuple));
  map.flyToBounds(bounds, { paddingTopLeft: [400, 180], paddingBottomRight: [60, 140], duration: 0.8 });
}

// ---- Frame transitions -------------------------------------------------------------------

watch(step, () => {
  animationToken++;
  selected.value = null;
  relaxed.value = false;
  const id = frame.value.id;

  if (id === 'start') {
    typedQuery.value = '';
    searchState.value = 'idle';
    map?.flyTo(HOME_VIEW.center, HOME_VIEW.zoom, { duration: 0.8 });
  } else if (id === 'search') {
    typeQuery();
    map?.flyTo(HOME_VIEW.center, HOME_VIEW.zoom, { duration: 0.8 });
  } else {
    typedQuery.value = persona.query;
    searchState.value = 'parsed';
    if (id === 'results') fitRanked();
    if (id === 'detail') {
      const top = ranked.value[0];
      if (top) select(top);
    }
    if (id === 'no-results' || id === 'analytics') map?.flyTo(HOME_VIEW.center, HOME_VIEW.zoom, { duration: 0.8 });
  }
});

watch([ranked, selected, showResults], () => {
  drawRankedMarkers();
  document.getElementById('preview-map')?.classList.toggle('dimmed', showAlert.value);
});

watch(relaxed, r => { if (r) fitRanked(); });

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowRight') go(step.value + 1);
  if (e.key === 'ArrowLeft') go(step.value - 1);
}

onMounted(() => {
  buildMap();
  window.addEventListener('keydown', onKey);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey);
  map?.remove();
});
</script>

<style>
/* Leaflet owns the marker DOM, so these rules are global. */
.quad-marker {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #d97706;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(217, 119, 6, 0.6);
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.bus-marker {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: white;
  background: #2563eb;
  border: 2px solid white;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.rank-marker {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 700;
  color: #111;
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
  cursor: pointer;
}

.rank-marker.selected {
  outline: 3px solid #1d4ed8;
  outline-offset: 1px;
}

#preview-map.dimmed .complex-icon { opacity: 0.25; }

/* Keep Leaflet's bottom controls and attribution above the caption strip. */
#preview-map .leaflet-bottom { bottom: 104px; }
</style>

<style scoped>
.preview-root {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

#preview-map {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.map-key {
  position: absolute;
  bottom: 124px;
  right: 60px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 0.75rem;
  color: #444;
}

.map-key i { color: #d97706; width: 16px; }
.map-key .fa-bus { color: #2563eb; }

.key-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin: 0 3px;
  border-radius: 50%;
  background: linear-gradient(90deg, #1a9850, #fee08b, #d73027);
}

.legend {
  position: absolute;
  bottom: 210px;
  left: 20px;
  z-index: 1000;
  width: 280px;
  padding: 10px 15px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  color: #444;
  line-height: 1.5;
}

.legend-moving {
  opacity: 0.85;
  outline: 2px dashed #d97706;
  outline-offset: 4px;
}

.legend-ribbon {
  display: inline-block;
  margin-bottom: 6px;
  padding: 2px 8px;
  background: #d97706;
  color: white;
  font-size: 0.72rem;
  font-weight: 700;
  border-radius: 999px;
}

.legend-header h4 { margin: 0; font-size: 0.95rem; color: #111; }

.gradient-bar {
  height: 10px;
  margin: 6px 0 4px;
  border-radius: 4px;
  background: linear-gradient(to right, #d73027, #fee08b, #1a9850);
}

.gradient-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
}

.legend-disclaimer { font-size: 0.7rem; color: #6b7280; }

.panel-enter-active, .panel-leave-active { transition: all 0.3s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; transform: translateY(8px); }
</style>
