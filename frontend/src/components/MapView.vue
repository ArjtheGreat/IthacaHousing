<template>
  <NavBar />
  <div class="overflow-auto box-border m-0 p-0">
    <!-- Loading Spinner -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p class="loading-text">{{ loadingMessage }}</p>
    </div>
    <!-- Desktop Recommendation Popup -->
    <div v-if="showDesktopRecommendation" class="desktop-recommendation-popup">
      <div class="popup-content">
        <div class="popup-header">
          <h3>📱 Mobile Experience</h3>
          <button @click="showDesktopRecommendation = false" class="close-btn">×</button>
        </div>
        <div class="popup-body">
          <p><strong>We strongly recommend using desktop</strong> for the best experience with Ithaca Insights.</p>
          <p>The desktop version provides:</p>
          <ul>
            <li>Full filter panel with all options</li>
            <li>Better map interaction and navigation</li>
            <li>Detailed listing information</li>
            <li>Enhanced data visualization</li>
          </ul>
        </div>
        <div class="popup-footer">
          <button @click="showDesktopRecommendation = false" class="continue-btn">
            Continue on Mobile
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Filter Toggle Button -->
    <button v-if="isMobile" @click="toggleMobileFilters" class="mobile-filter-toggle" :class="{ active: showMobileFilters }">
      <i class="fa-solid fa-filter"></i>
      <span>{{ hasAnyActiveFilters ? filteredListings.length : 'Filters' }}</span>
    </button>

    <!-- Personal Taste Filters -->
    <div class="personal-filters-container" :class="{ 'mobile-hidden': isMobile && !showMobileFilters }">
      <!-- Main Personal Preferences Card -->
      <div class="main-preferences-card">
        <div class="card-header">
          <h3 class="card-title">Personal Preferences</h3>
          <span v-if="hasAnyActiveFilters" class="filter-badge">{{ filteredListings.length }} results</span>
        </div>
        
        <div class="card-content">
          <!-- Beds and Baths Row -->
          <div class="filter-row">
            <div class="filter-group">
              <label for="bed-filter" class="filter-label">Beds</label>
              <select id="bed-filter" v-model="selectedBeds" @change="updateBedFilter" class="filter-select">
                <option :value="0">Any</option>
                <option v-for="n in bedOptions" :key="n" :value="n">{{ n }}</option>
              </select>
            </div>

            <div class="filter-group">
              <label for="bath-filter" class="filter-label">Baths</label>
              <select id="bath-filter" v-model="selectedBaths" @change="updateBathFilter" class="filter-select">
                <option :value="0">Any</option>
                <option v-for="n in bathOptions" :key="n" :value="n">{{ n }}</option>
              </select>
            </div>
          </div>

          <!-- Budget Row -->
          <div class="filter-row">
            <div class="filter-group">
              <label for="budget-filter" class="filter-label">Budget</label>
              <select id="budget-filter" v-model="selectedBudget" @change="updateBudgetFilter" class="filter-select">
                <option :value="0">Any</option>
                <option v-for="n in BUDGET_OPTIONS" :key="n" :value="n">{{ budgetLabel(n) }}</option>
              </select>
            </div>
          </div>

          <!-- Location Row -->
          <!-- <div class="filter-row">
            <div class="filter-group">
              <label for="location-filter" class="filter-label">🏘️  Neighborhood</label>
              <select id="location-filter" v-model="selectedLocation" @change="updateLocationFilter" class="filter-select">
                <option value="">Any neighborhood</option>
                <option v-for="neighborhood in availableNeighborhoods" :key="neighborhood" :value="neighborhood">
                  {{ neighborhood }}
                </option>
              </select>
            </div>
          </div> -->

          <!-- Commute Section -->
          <div class="commute-section">
            <div class="commute-header">
              <h4 class="commute-title">Commute</h4>
            </div>

            <div class="filter-row-commute">
              <div class="filter-group">
                <label for="destination-filter" class="filter-label">Destination</label>
                <select id="destination-filter" v-model="selectedDestination" @change="autoApplyCommuteFilter" class="filter-select">
                  <option value="">Any</option>
                  <!-- <option value="urishall">Uris Hall</option> -->
                  <option value="agriculturequad">Ag Quad</option>
                  <option value="artsquad">Arts Quad</option>
                  <option value="engineeringquad">Eng Quad</option>
                </select>
              </div>

              <div class="filter-group">
                <label for="commute-time-filter" class="filter-label">Max time</label>
                <select id="commute-time-filter" v-model="selectedCommuteTime" @change="autoApplyCommuteFilter" class="filter-select">
                  <option value="">Any</option>
                  <option v-for="t in commuteTimeOptions" :key="t" :value="String(t)">{{ t }} min</option>
                </select>
              </div>

              <div class="filter-group">
                <label for="transit-mode-filter" class="filter-label">Mode</label>
                <select id="transit-mode-filter" v-model="selectedTransitMode" @change="autoApplyCommuteFilter" class="filter-select">
                  <option value="">Any</option>
                  <option value="walk">Walking</option>
                  <option value="walk">TCAT</option>
                  <option value="drive">Drive</option>
                  <option value="bike">Bike</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Points of Interest Section -->
          <div class="filter-section">
            <label for="bed-filter" class="filter-label">Points of Interest</label>
            <div class="poi-buttons">
              <button 
                @click="togglePOI('groceries')" 
                :class="['poi-btn', { active: activePOI === 'groceries' }]"
              >
                <i class="fa-solid fa-shopping-basket"></i>
                Groceries
              </button>
              <button 
                @click="togglePOI('neighborhoods')" 
                :class="['poi-btn', { active: activePOI === 'neighborhoods' }]"
              >
                <i class="fa-solid fa-map"></i>
                Neighborhoods
              </button>
              <!-- <button 
                @click="togglePOI('shopping')" 
                :class="['poi-btn', { active: activePOI === 'shopping' }]"
              >
                <i class="fa-solid fa-shopping-bag"></i>
                Shopping
              </button> -->
              <!-- <button 
                @click="togglePOI('attractions')" 
                :class="['poi-btn', { active: activePOI === 'attractions' }]"
              >
                <i class="fa-solid fa-landmark"></i>
                Attractions
              </button> -->
            </div>
          </div>

          <!-- Reset Button -->
          <div class="reset-section">
            <button @click="resetAllFilters" class="reset-btn">Reset All Filters</button>
          </div>
        </div>
      </div>

      <div class="icon-buttons">
          <!-- <button 
            @click="toggleWalk" 
            :class="['icon-button', { active: activeFilters.walk !== null }]"
          >
            🚶‍♂️ Walk
          </button>
          <button 
            @click="toggleTransit" 
            :class="['icon-button', { active: activeFilters.transit !== null }]"
          >
            🚌 TCAT
          </button> -->
          <!-- <button 
            @click="togglePets" 
            :class="['icon-button', { active: activeFilters.pets !== null }]"
          >
            🐶 Pets
          </button> -->
        </div>
    </div>

    <!-- Filter alerts: a filter failed to load, or nothing matches the active filters.
         Outside the map container so they stack above the filter panel. -->
    <div v-if="filterError || showNoResults" class="filter-alerts">
      <FilterAlert v-if="filterError" kind="error" :filter-key="filterError" @dismiss="filterError = null" />
      <FilterAlert v-if="showNoResults" kind="empty" :suggestion="relaxHint" @relax="applyRelax" @reset="resetAllFilters" />
    </div>

    <!-- Map Container -->
    <div class="relative flex z-[0] border-b-2 border-black overflow-hidden">
      <RentalSidebar class="rental-sidebar" @close="closePopup" @zoom="zoomToListing" @select-listing="selectListingFromSidebar" :listing="selectedListing" v-if="isSidebarVisible" />

      <!-- Address Search Bar -->
      <div class="search-container">
        <div class="search-bar-wrapper">
          <input
            v-model="searchQuery"
            @input="handleSearchInput"
            @focus="showSuggestions = true"
            @blur="hideSuggestions"
            type="text"
            placeholder="Search addresses..."
            class="search-input"
          />
          <div v-if="showSuggestions && searchSuggestions.length > 0" class="suggestions-dropdown">
            <div
              v-for="(suggestion, index) in searchSuggestions"
              :key="index"
              @click="selectSuggestion(suggestion)"
              class="suggestion-item"
              :class="{ highlighted: index === highlightedIndex }"
            >
              <div class="suggestion-address">{{ suggestion.address }}</div>
              <div class="suggestion-details">{{ suggestion.details }}</div>
            </div>
          </div>
        </div>
      </div>

      <div id="map"></div>

      <!-- Legend -->
      <div class="legend">
        <div class="legend-header">
          <h4>{{ priceDisplayMode === 'differential' ? 'Price Differential' : 'Raw Price' }}</h4>
          <button @click="togglePriceDisplayMode" class="price-mode-toggle">
            {{ priceDisplayMode === 'differential' ? 'Show Raw Prices' : 'Show Differential' }}
          </button>
        </div>
        <div class="gradient-legend">
          <div class="gradient-bar" :style="{ background: priceDisplayMode === 'differential' 
            ? 'linear-gradient(to right, #d73027, #fee08b, #1a9850)' 
            : 'linear-gradient(to right, #10b981 0%, #10b981 5%, #bfdbfe 5%, #1e3a8a 95%, #ef4444 95%, #ef4444 100%)' }"></div>
          <div class="gradient-labels">
            <span class="label-start">{{ priceDisplayMode === 'differential' ? 'Higher' : 'Low Outlier' }}</span>
            <span class="label-middle">{{ priceDisplayMode === 'differential' ? 'Fair Price' : 'Normal Range' }}</span>
            <span class="label-end">{{ priceDisplayMode === 'differential' ? 'Lower' : 'High Outlier' }}</span>
          </div>
        </div>
        <div class="legend-disclaimer">
          {{ priceDisplayMode === 'differential' 
            ? 'Colors show how actual rent compares to fair rent.' 
            : 'Green = very cheap (bottom 5%), Blue = normal range, Red = very expensive (top 5%)' }}
          <!-- <br/>
          <div class="disclaimer-disclaimer">
            Estimates for research purposes only.
          </div> -->
        </div>
      </div> 
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, markRaw, toRaw } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { fetchListings, fetchListing, fetchListingsMinimal, fetchTopTenListings, fetchBottomTenListings, fetchClusters, fetchHeatMap, fetchBedFilter, fetchBathFilter, fetchWalkFilter, fetchTransitFilter, fetchPetsFilter, fetchRentListings, fetchRoomToRentListings, fetchSharedListings } from "@/services/fetch";
import NavBar from "@/components/NavBar.vue";
import RentalSidebar from "@/components/RentalSidebar.vue";
import FilterAlert from "@/components/FilterAlert.vue";
import { RadioGroup, RadioGroupLabel, RadioGroupOption } from "@headlessui/vue";
import "leaflet.heat";
import { groupIntoComplexes, getColor, interpolateColor, valueScore, colorForScore, bucketForScore, sortByValue, BUCKET_COLORS } from "@/utils/complexes";
import { complexMarkerSvg, compactMarkerSvg, complexPopupHtml } from "@/utils/complexMarker";
import { mergeActiveFilters, relaxSuggestion } from "@/utils/filters";
import { filterByBudget, budgetLabel, BUDGET_OPTIONS } from "@/utils/budget";
import "@/assets/complexes.css";
// "?url" makes the build ship the file; a raw /src/... path only exists on the dev server
import cornellBoundaryUrl from "@/assets/cornell_main_boundary.geojson?url";
import "@fortawesome/fontawesome-svg-core/styles.css";

const map = ref(null); // Holds the ref for the map
const isSidebarVisible = ref(false); // Toggle state for whether the Rental Sidebar is visible or not
const selectedListing = ref(null); // Holds the prop state for the selected listing to pass to RentalSidebar
const selectedMarker = ref(null); // Holds the currently selected marker for highlighting
const markers = ref([]); // Store all markers
const complexes = ref([]); // Buildings currently on the map (one per address), used for search matching
const COMPLEX_FULL_ZOOM = 17; // Below this zoom, building markers shrink to plain dots
let markerEntries = []; // { complex, marker, paint } for every listing marker on the map
let entryByListingId = new Map(); // listingid -> its marker entry
let selectedEntry = null; // Entry whose marker is currently highlighted
let isCompactZoom = true; // Whether markers are drawn in their zoomed-out form
const cornellBoundaryLayer = ref(null); // Store the Cornell boundary layer
const allListings = ref([]); // Store all listings
const topTenListings = ref([]); // Store top 10 listings
const bottomTenListings = ref([]); // Store bottom 10 listings
const clusteredListings = ref([]); // Store Clustered Listings
const heatmapData = ref(null); // Stores the Heatmap Data
const heatmapLayer = ref(null); // Stores the Heatmap Layer
const isochronicLayer = ref(null); // Stores the isochronic map layer
// Tab functionality moved to InsideIthacaView
let activeFilter = ref(null); // Tracks which filter is selected

const activeFilters = ref({ beds: null, baths: null, location: null, walk: null, transit: null, pets: null, roomtorent: null, rent: null, shared: null, commute: null, budget: null }); // Holds Bath and Bed Data for Dynamic Filtering
const filteredListings = ref([]); // Keeps track of the filtered listings
const filterError = ref(null); // Key of the filter whose data failed to load, shown as an alert
const selectedBeds = ref(0); // Number of Selected Beds
const bedOptions = [1, 2, 3, 4, 5]; // Adjust based on available data
const selectedBaths = ref(0); // Number of Selected Baths
const bathOptions = [1, 1.5, 2, 2.5, 3]; // Adjust based on available data
const selectedBudget = ref(0); // Max rent per person per month (0 = Any)
const selectedLocation = ref(''); // Selected Location
const selectedDestination = ref(''); // Selected Destination for commute filter
const selectedCommuteTime = ref(''); // Selected Max Commute Time
const commuteTimeOptions = [15, 20, 25, 30]; // Max commute minutes in the dropdown; also the notches the no-results alert tries
const selectedTransitMode = ref(''); // Selected Transit Mode (walk/bike/drive)
const showCommuteDrawer = ref(false); // Controls visibility of commute filter drawer (legacy)
const showCommutePanel = ref(false); // Controls visibility of new commute panel

// Points of Interest variables
const activePOI = ref(null); // Tracks which POI is currently displayed

// Price display mode: 'differential' or 'raw'
const priceDisplayMode = ref('differential'); // 'differential' or 'raw'

// Mobile functionality variables
const isMobile = ref(false); // Tracks if user is on mobile
const showMobileFilters = ref(false); // Controls mobile filter visibility
const showDesktopRecommendation = ref(false); // Controls desktop recommendation popup
const poiMarkers = ref([]); // Stores POI markers on the map
const poiData = ref({ groceries: [], shopping: [], attractions: [] }); // Stores loaded POI data
const neighborhoodsLayer = ref(null); // Stores the neighborhoods GeoJSON layer

// Search functionality
const searchQuery = ref('');
const searchSuggestions = ref([]);
const showSuggestions = ref(false);
const highlightedIndex = ref(-1);
const currentRoute = ref(null);

const isLoading = ref(true); // Add loading state

// Computed property to check if any filters are active
const hasAnyActiveFilters = computed(() => {
  return Object.values(activeFilters.value).some(filter => filter !== null);
});

// Filters are on but no listing passes all of them
const showNoResults = computed(() => {
  return !isLoading.value && hasAnyActiveFilters.value && filteredListings.value.length === 0;
});

// Smallest change that brings listings back, offered in the no-results alert
const relaxHint = computed(() => {
  if (!showNoResults.value) return null;
  const currentMax = parseFloat(selectedCommuteTime.value);
  const commuteStep = {
    key: 'commute',
    options: commuteTimeOptions.filter(t => t > currentMax),
    listingsAt: commuteMatches,
  };
  return relaxSuggestion(allListings.value, activeFilters.value, [commuteStep]);
});

// Computed property to get unique neighborhoods from listings
const availableNeighborhoods = computed(() => {
  if (!allListings.value || allListings.value.length === 0) {
    return [];
  }
  
  // Get unique neighborhoods, filter out null/undefined/empty/NaN values
  const neighborhoods = allListings.value
    .map(listing => listing.neighborhood)
    .filter(neighborhood => {
      if (!neighborhood) return false;
      if (typeof neighborhood !== 'string') return false;
      if (neighborhood.trim() === '') return false;
      if (neighborhood.toLowerCase() === 'nan') return false;
      if (neighborhood === 'NaN') return false;
      return true;
    })
    .filter((value, index, self) => self.indexOf(value) === index) // Remove duplicates
    .sort(); // Sort alphabetically
  
  console.log('Available neighborhoods:', neighborhoods)
  return neighborhoods;
});

// Funny Loading Messages Logic
let messageIndex = 0;
let messageInterval;

const loadingMessage = ref("Loading data...");

const messages = [
  "Scraping rental secrets...",
  "Drawing overpriced dots...",
  "Checking if Collegetown is still a mess...",
  "Calculating who’s paying too much...",
  "Locating affordable housing (404 not found)...",
  "Scanning for deals in the wild...",
  "Counting beds, baths and beyond...",
  "Powered by Maitrix Labs",
];


/**
 * Gets the color of the dot based on raw price (rent_per_person) with outlier highlighting
 * @param rent - Actual rent per person
 * @param minRent - Minimum rent in the dataset
 * @param maxRent - Maximum rent in the dataset
 * @param p5 - 5th percentile (low outlier threshold)
 * @param p95 - 95th percentile (high outlier threshold)
 */
function getColorByRawPrice(rent, minRent, maxRent, p5, p95) {
    if (!rent || isNaN(rent) || maxRent === minRent) {
        return '#93c5fd'; // Default light blue for invalid values
    }
    
    // Identify outliers
    if (rent <= p5) {
        // Low outlier (very cheap) - Green
        return '#10b981'; // Emerald green
    } else if (rent >= p95) {
        // High outlier (very expensive) - Red/Orange
        return '#ef4444'; // Red
    } else {
        // Normal range - Blue gradient from light to dark
        // Normalize to 0-1 range within the normal range (p5 to p95)
        const normalized = (rent - p5) / (p95 - p5);
        // Smooth gradient from light blue to dark blue
        return interpolateColor('#bfdbfe', '#1e3a8a', normalized);
    }
}

// Tab functionality moved to InsideIthacaView

/**
 * Clears all marker highlights
 */
function clearAllHighlights() {
    markers.value.forEach(marker => {
        if (marker.options.originalRadius) {
            marker.setStyle({
                weight: 2,
                radius: marker.options.originalRadius,
                color: marker.options.originalColor || marker.options.fillColor,
                fillColor: marker.options.fillColor
            });
        }
    });
    selectedEntry?.marker.getElement?.()?.classList.remove('complex-selected');
    selectedEntry = null;
    selectedMarker.value = null;
}

/**
 * Highlights the marker that holds the selected listing (its own dot, or its building's marker)
 */
function highlightSelectedMarker(listing) {
    // Clear ALL highlights first
    clearAllHighlights();

    const entry = entryByListingId.get(String(listing?.listingid));
    if (!entry) return; // Listing is not on the map (e.g. hidden by filters)

    selectedEntry = entry;
    selectedMarker.value = entry.marker;

    if (entry.complex.count > 1) {
        entry.marker.getElement()?.classList.add('complex-selected');
        return;
    }

    const marker = entry.marker;
    // Store original properties if not already stored
    if (!marker.options.originalRadius) {
        marker.options.originalRadius = marker.options.radius;
        marker.options.originalColor = marker.options.color;
    }
    marker.setStyle({
        weight: 4,
        radius: marker.options.originalRadius + 5,
        color: '#124a10',
        fillColor: marker.options.fillColor
    });
}

/**
 * Rent statistics used by raw price mode (for outlier detection)
 */
function getRawPriceStats(listings) {
    const rentValues = listings
        .map(listing => listing.rent_per_person)
        .filter(rent => rent && !isNaN(rent))
        .sort((a, b) => a - b);

    if (rentValues.length === 0) {
        // Fallback if no valid rents found
        return { minRent: 0, maxRent: 1000, p5: 0, p95: 1000 };
    }
    const minRent = rentValues[0];
    const maxRent = rentValues[rentValues.length - 1];
    // Calculate 5th and 95th percentiles for outlier detection
    const p5Index = Math.floor(rentValues.length * 0.05);
    const p95Index = Math.ceil(rentValues.length * 0.95) - 1;
    return { minRent, maxRent, p5: rentValues[p5Index] || minRent, p95: rentValues[p95Index] || maxRent };
}

/**
 * Color of a single listing in the current price display mode
 */
function listingColor(listing, stats) {
    if (priceDisplayMode.value === 'raw') {
        return getColorByRawPrice(listing.rent_per_person, stats.minRent, stats.maxRent, stats.p5, stats.p95);
    }
    return getColor(listing.rent_per_person, listing.predictedrent);
}

/**
 * Center color and ring segments for a building marker in the current price display mode
 */
function complexPaint(complex, stats) {
    if (priceDisplayMode.value === 'raw') {
        const priced = complex.units.filter(unit => unit.rent_per_person > 0);
        return {
            center: getColorByRawPrice(complex.medianRent, stats.minRent, stats.maxRent, stats.p5, stats.p95),
            // Same order of checks as getColorByRawPrice, so each unit lands in exactly one segment
            segments: [
                { color: '#10b981', count: priced.filter(unit => unit.rent_per_person <= stats.p5).length },
                { color: '#3b82f6', count: priced.filter(unit => unit.rent_per_person > stats.p5 && unit.rent_per_person < stats.p95).length },
                { color: '#ef4444', count: priced.filter(unit => unit.rent_per_person > stats.p5 && unit.rent_per_person >= stats.p95).length },
            ],
        };
    }
    return {
        center: colorForScore(complex.medianScore),
        segments: ['under', 'fair', 'over'].map(bucket => ({ color: BUCKET_COLORS[bucket], count: complex.buckets[bucket] })),
    };
}

/**
 * Leaflet icon for a building: count badge when zoomed in, small dot when zoomed out
 */
function complexIcon(entry) {
    const { complex, paint } = entry;
    const art = isCompactZoom
        ? compactMarkerSvg(complex.count, paint.center, complex.address)
        : complexMarkerSvg(complex.count, paint, complex.address);
    return L.divIcon({
        html: art.html,
        className: entry === selectedEntry ? 'complex-icon complex-selected' : 'complex-icon',
        iconSize: [art.size, art.size],
        popupAnchor: [0, -art.size / 2 + 4],
    });
}

const formatRent = (rent) => (rent > 0 ? `$${Math.round(rent).toLocaleString('en-US')}` : '—');

/**
 * Popup list for a building: one row per unit, best value first
 * @param entry - Marker entry for the building
 * @param stats - Raw price statistics for the listings on the map
 * @param totalUnits - Units at this building when nothing is filtered out
 */
function buildComplexPopup(entry, stats, totalUnits) {
    const { complex } = entry;
    const rows = sortByValue(complex.units).map(unit => {
        const score = valueScore(unit);
        return {
            id: unit.listingid,
            beds: unit.available_bedrooms == null ? 'N/A' : unit.available_bedrooms > 0 ? `${Number(unit.available_bedrooms)} bd` : 'Studio',
            rent: formatRent(unit.rent_per_person),
            color: listingColor(unit, stats),
            badge: score === null ? 'n/a' : `${(Math.abs(score) * 100).toFixed(1)}%`,
            badgeClass: score === null ? 'none' : bucketForScore(score),
        };
    });
    const range = complex.minRent === null ? '' : ` · ${formatRent(complex.minRent)}–${formatRent(complex.maxRent)}`;
    return complexPopupHtml({
        address: complex.address,
        summary: `${complex.count} units${range}`,
        note: totalUnits > complex.count ? `Showing ${complex.count} of ${totalUnits} units here` : undefined,
        rows,
    });
}

/**
 * Opens the sidebar for a listing and highlights its marker
 */
async function openListing(listing) {
    // Load full listing data when clicked
    const fullListing = await fetchListing(listing.listingid);
    if (fullListing) {
        selectedListing.value = fullListing;
        highlightSelectedMarker(listing);
        currentRoute.value = plotRoute(fullListing).addTo(map.value);
        // displayIsochronicMap(fullListing); // Display isochronic map
        isSidebarVisible.value = true;
    }
}

/**
 * Switches listing markers between their zoomed-in and zoomed-out forms
 */
function applyZoomMode() {
    const compact = map.value.getZoom() < COMPLEX_FULL_ZOOM;
    if (compact === isCompactZoom) return;
    isCompactZoom = compact;

    markerEntries.forEach(entry => {
        if (entry.complex.count > 1) {
            entry.marker.setIcon(complexIcon(entry));
            return;
        }
        const radius = isCompactZoom ? 6 : 10;
        if (entry.marker.options.originalRadius) entry.marker.options.originalRadius = radius;
        entry.marker.setRadius(entry === selectedEntry ? radius + 5 : radius);
    });
}

/**
 * Display isochronic map for a listing
 * @param {Object} listing - The listing with iso15 data
 */
function displayIsochronicMap(listing) {
    // Remove existing isochronic layer
    if (isochronicLayer.value) {
        map.value.removeLayer(isochronicLayer.value);
        isochronicLayer.value = null;
    }

    // Check if listing has isochronic data
    if (!listing.iso15) {
        console.log('No isochronic data available for this listing');
        return;
    }

    try {
        // Parse the GeoJSON
        const geoJsonData = JSON.parse(listing.iso15);
        
        // Create the isochronic polygon layer
        isochronicLayer.value = L.geoJSON(geoJsonData, {
            style: {
                color: '#3b82f6', // Blue color
                weight: 2,
                opacity: 0.8,
                fillColor: '#3b82f6',
                fillOpacity: 0.2
            }
        }).addTo(map.value);

        // Fit map to show the isochronic area
        // if (geoJsonData.features && geoJsonData.features.length > 0) {
        //     map.value.fitBounds(isochronicLayer.value.getBounds(), { padding: [20, 20] });
        // }

        console.log('Isochronic map displayed for listing:', listing.listingid);
    } catch (error) {
        console.error('Error parsing isochronic data:', error);
    }
}

/**
 * Hide the isochronic map
 */
function hideIsochronicMap() {
    if (isochronicLayer.value) {
        map.value.removeLayer(isochronicLayer.value);
        isochronicLayer.value = null;
        console.log('Isochronic map hidden');
    }
}

/**
 * Add quad icons to the map
 */
function addQuadIcons() {
  // Define quad locations and icons
  const quads = [
    {
      name: "Ag Quad",
      coordinates: [42.448796, -76.478018],
      icon: "fas fa-seedling", // Agriculture icon
      size: 20
    },
    {
      name: "Arts Quad", 
      coordinates: [42.448966, -76.484175],
      icon: "fas fa-book", // Book icon
      size: 20
    },
    {
      name: "Eng Quad",
      coordinates: [42.444668, -76.482570], 
      icon: "fas fa-cogs", // Engineering/gears icon
      size: 20
    }
  ];

  quads.forEach(quad => {
    // Create a subtle quad icon that blends with the map
    const quadIcon = L.divIcon({
      html: `<div style="
        font-size: ${quad.size}px; 
        text-align: center; 
        line-height: 1;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 50%;
        padding: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15);
        border: 1px solid rgba(217, 119, 6, 0.6);
        color: #d97706;
        display: flex;
        align-items: center;
        justify-content: center;
        width: ${quad.size + 12}px;
        height: ${quad.size + 12}px;
        opacity: 0.9;
      "><i class="${quad.icon}"></i></div>`,
      className: 'quad-icon',
      iconSize: [quad.size + 24, quad.size + 24],
      iconAnchor: [(quad.size + 24) / 2, (quad.size + 24) / 2]
    });

    // Add marker to map
    const marker = L.marker(quad.coordinates, { icon: quadIcon }).addTo(map.value);
    
    // Add popup with quad name
    marker.bindPopup(quad.name, {
      className: 'quad-popup'
    });
  });
}

/**
 * Forgets the listing markers. Call whenever they are taken off the map.
 */
function resetMarkerEntries() {
    markerEntries = [];
    entryByListingId = new Map();
    selectedEntry = null;
}

/**
 * Add markers to the map: one per building.
 * A building with a single listing keeps the plain dot; a building with several gets a
 * count marker whose popup lists the units.
 */
function addMarkers(listings, filtered) {
    // Leaflet must work with the real map and markers, not Vue's reactive proxies: a popup opened
    // through a proxy is never fully removed and its zoom handler later throws.
    const rawMap = toRaw(map.value);
    markers.value.forEach(marker => rawMap.removeLayer(toRaw(marker))); 
    markers.value = []; 
    resetMarkerEntries();

    if (heatmapLayer.value) {
      map.value.removeLayer(heatmapLayer.value); 
    }

    const grouped = groupIntoComplexes(listings);
    complexes.value = grouped; // Store for search matching
    isCompactZoom = map.value.getZoom() < COMPLEX_FULL_ZOOM;

    const stats = getRawPriceStats(listings);

    // Units per building when nothing is filtered out, so a popup can say "Showing 8 of 22 units here".
    // Keyed by listing, because a building's id can change with which of its units are present.
    const totalUnitsByListingId = new Map();
    if (listings.length < allListings.value.length) {
        groupIntoComplexes(toRaw(allListings.value)).forEach(complex => {
            complex.units.forEach(unit => totalUnitsByListingId.set(String(unit.listingid), complex.count));
        });
    }

    grouped.forEach(complex => {
        const entry = { complex, marker: null, paint: null };

        if (complex.count === 1) {
            const listing = complex.units[0];
            const color = listingColor(listing, stats);
            entry.marker = L.circleMarker([complex.lat, complex.lng], {
              color,
              fillColor: color,                // dynamic fill based on pricing
              fillOpacity: 0.85,               // more saturated look
              radius: isCompactZoom ? 6 : 10,
              weight: 2,                       // thin border
              opacity: 1,                      // full circle border visibility
              className: 'modern-dot'          // for custom CSS glow
            }).addTo(rawMap);
            entry.marker.on("click", () => openListing(listing));
        } else {
            entry.paint = complexPaint(complex, stats);
            entry.marker = L.marker([complex.lat, complex.lng], {
                icon: complexIcon(entry),
                riseOnHover: true,
            }).addTo(rawMap);

            entry.marker.bindPopup(() => buildComplexPopup(entry, stats, totalUnitsByListingId.get(String(complex.units[0].listingid)) ?? complex.count), {
                className: 'complex-popup-wrap',
                maxWidth: 300,
                autoPanPaddingTopLeft: [20, 130], // keep clear of the navbar and search bar
            });
            entry.marker.on('popupopen', (event) => {
                // Assigned (not added) so reopening the popup never stacks handlers
                event.popup.getElement().onclick = (click) => {
                    const row = click.target.closest('[data-listing-id]');
                    const listing = row && complex.units.find(unit => String(unit.listingid) === row.dataset.listingId);
                    if (!listing) return;
                    row.parentElement.querySelectorAll('.active').forEach(el => el.classList.remove('active'));
                    row.classList.add('active');
                    if (isMobile.value) entry.marker.closePopup(); // the sidebar covers the map on mobile
                    openListing(listing);
                };
            });
        }

        complex.units.forEach(unit => entryByListingId.set(String(unit.listingid), entry));
        markerEntries.push(entry);
        markers.value.push(markRaw(entry.marker)); 
    });
}

/**
 * Plots Route for listing
 */
function plotRoute(listing) {
  currentRoute.value?.remove()
  /**
   * WKT Shapely to Lat, Lng Coords  
   * @param wkt 
   */
  function parseWKTLineString(wkt) {
    // Check if wkt is null, undefined, or empty
    if (!wkt || typeof wkt !== 'string') {
      console.warn('Invalid WKT data:', wkt);
      return [];
    }

    try {
      const coordsText = wkt
        .replace('LINESTRING (', '')
        .replace(')', '')
        .trim();

      const coords = coordsText.split(',').map(pair => {
        const [lng, lat] = pair.trim().split(' ').map(Number);
        return [lat, lng]; 
      });

      return coords;
    } catch (error) {
      console.error('Error parsing WKT:', error, 'WKT data:', wkt);
      return [];
    }
  }

  const routeCoords = parseWKTLineString(listing.walk_routes);
  if (routeCoords.length > 0) {
    const currentPolyline = L.polyline(routeCoords, {
      color: 'orange',
      weight: 4,
      opacity: 0.7
    });
    return currentPolyline;
  } else {
    console.warn('No valid route data for listing:', listing.id || listing.listingaddress);
    return L.polyline([], { color: 'transparent', weight: 0 });
  }
}

// Compute Levenshtein distance between two strings
function levenshtein(a, b) {
  const matrix = Array.from({ length: a.length + 1 }, () =>
    Array(b.length + 1).fill(0)
  );

  for (let i = 0; i <= a.length; i++) matrix[i][0] = i;
  for (let j = 0; j <= b.length; j++) matrix[0][j] = j;

  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,       // deletion
        matrix[i][j - 1] + 1,       // insertion
        matrix[i - 1][j - 1] + cost // substitution
      );
    }
  }
  return matrix[a.length][b.length];
}

// Fuzzy match using normalized Levenshtein similarity
function fuzzyMatch(query, text) {
  if (!query || !text) return 0;

  const queryLower = query.toLowerCase();
  const textLower = text.toLowerCase();

  // Exact substring match gets 1.0
  if (textLower.includes(queryLower)) {
    return 1.0;
  }

  const distance = levenshtein(queryLower, textLower);
  const maxLen = Math.max(queryLower.length, textLower.length);

  return 1 - distance / maxLen;
}


const handleSearchInput = () => {
  if (searchQuery.value.length < 2) {
    searchSuggestions.value = [];
    return;
  }
  
  const query = searchQuery.value.toLowerCase();
  const suggestions = complexes.value
    .map(complex => {
      const listing = complex.units[0];
      return {
        complex,
        score: Math.max(
          fuzzyMatch(query, listing.listingaddress || ''),
          fuzzyMatch(query, listing.listingcity || ''),
          fuzzyMatch(query, `${listing.listingaddress} ${listing.listingcity}` || '')
        )
      };
    })
    .filter(match => match.score > 0.3)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map(({ complex }) => {
      const listing = complex.units[0];
      const range = complex.minRent === null
        ? 'N/A'
        : complex.minRent === complex.maxRent ? formatRent(complex.minRent) : `${formatRent(complex.minRent)}–${formatRent(complex.maxRent)}`;
      return {
        address: `${listing.listingaddress}, ${listing.listingcity}`,
        details: complex.count > 1
          ? `${complex.count} units • ${range}`
          : `${listing.available_bedrooms || 'N/A'} bed • ${range}`,
        complex,
        listing
      };
    });
  
  searchSuggestions.value = suggestions;
  highlightedIndex.value = -1;
};

const selectSuggestion = async (suggestion) => {
  showSuggestions.value = false;
  
  // Center map on the selected listing (without zooming)
  if (suggestion.listing && suggestion.listing.latitude && suggestion.listing.longitude) {
    map.value.setView([suggestion.complex.lat, suggestion.complex.lng], map.value.getZoom());
    
    const entry = entryByListingId.get(String(suggestion.listing.listingid));
    if (suggestion.complex.count > 1 && entry) {
      // A building with several units: show its unit list
      entry.marker.openPopup();
    } else {
      // A single listing, or the listing markers are hidden (cluster / heatmap view)
      // Load full listing data when selected from search
      await openListing(suggestion.listing);
    }

    // clear Text
    searchQuery.value = ""
  }
};

const hideSuggestions = () => {
  // Delay hiding to allow for click events
  setTimeout(() => {
    showSuggestions.value = false;
  }, 200);
};

/**
 * Mobile functionality functions
 */
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768;
};

const toggleMobileFilters = () => {
  showMobileFilters.value = !showMobileFilters.value;
};

// Listen for window resize to update mobile state
window.addEventListener('resize', checkMobile);

/**
 * Lifecycle Hook on Mount
 * Fetches Data from API and initializes Map
 */
 onMounted(async () => {
  const startTime = performance.now();
  console.log('🚀 Map initialization started');

  // Mobile detection
  checkMobile();
  if (isMobile.value) {
    showDesktopRecommendation.value = true;
  }

  messageInterval = setInterval(() => {
    messageIndex = (messageIndex + 1) % messages.length;
    loadingMessage.value = messages[messageIndex];
  }, 2500);

  try {
    const mapInitStart = performance.now();
    map.value = L.map("map", {
      center: [42.455, -76.48],
      zoom: 14,
      maxZoom: 20,
    });
    map.value.on('zoomend', applyZoomMode);
    console.log(`🗺️ Map created: ${(performance.now() - mapInitStart).toFixed(2)}ms`);

    const tileStart = performance.now();
    const JAWG_API_KEY = import.meta.env.VITE_JAWG_API_KEY;
    const tileLayer = L.tileLayer(`https://tile.jawg.io/f67529a2-5ea7-4b7a-81a7-c5147a45b5f0/{z}/{x}/{y}{r}.png?access-token=${JAWG_API_KEY}`, {
      attribution: '<a href="https://jawg.io" target="_blank">&copy; Jawg Maps</a> &copy; OpenStreetMap contributors',
      minZoom: 0,
      maxZoom: 22,
      accessToken: JAWG_API_KEY
    });
    tileLayer.addTo(map.value);
    console.log(`🗺️ Tile layer added: ${(performance.now() - tileStart).toFixed(2)}ms`);

    // Add Cornell boundary layer
    const boundaryStart = performance.now();
    try {
      const response = await fetch(cornellBoundaryUrl);
      const cornellBoundary = await response.json();
      
      cornellBoundaryLayer.value = L.geoJSON(cornellBoundary, {
        style: {
          color: '#d97706', // Orange color
          weight: 3,
          opacity: 0.8,
          fillColor: 'transparent',
          fillOpacity: 0
        }
      }).addTo(map.value);
      console.log(`🏛️ Cornell boundary added: ${(performance.now() - boundaryStart).toFixed(2)}ms`);
    } catch (error) {
      console.error('Failed to load Cornell boundary:', error);
    }

    // Add quad icons
    addQuadIcons();

    const fetchStart = performance.now();
    console.log('📡 Starting API calls...');
    
    // Individual timing for each API call
    const listingsStart = performance.now();
    const listings = await fetchListingsMinimal();
    console.log(`📊 fetchListingsMinimal: ${(performance.now() - listingsStart).toFixed(2)}ms`);
    
    const topStart = performance.now();
    const top = await fetchTopTenListings();
    console.log(`📊 fetchTopTenListings: ${(performance.now() - topStart).toFixed(2)}ms`);
    
    const bottomStart = performance.now();
    const bottom = await fetchBottomTenListings();
    console.log(`📊 fetchBottomTenListings: ${(performance.now() - bottomStart).toFixed(2)}ms`);
    
    const clustersStart = performance.now();
    const clusters = await fetchClusters();
    console.log(`📊 fetchClusters: ${(performance.now() - clustersStart).toFixed(2)}ms`);
    
    const heatStart = performance.now();
    const heat = await fetchHeatMap();
    console.log(`📊 fetchHeatMap: ${(performance.now() - heatStart).toFixed(2)}ms`);
    
    console.log(`📡 All API calls completed: ${(performance.now() - fetchStart).toFixed(2)}ms`);
    console.log(`📊 Data received:`, {
      listings: listings?.length || 0,
      top: top?.length || 0,
      bottom: bottom?.length || 0,
      clusters: clusters?.length || 0,
      heat: heat?.length || 0
    });

    allListings.value = listings;
    topTenListings.value = top;
    bottomTenListings.value = bottom;
    clusteredListings.value = clusters;
    heatmapData.value = heat;

    const markersStart = performance.now();
    addMarkers(listings, false);
    console.log(`📍 Markers added: ${(performance.now() - markersStart).toFixed(2)}ms`);

    const totalTime = performance.now() - startTime;
    console.log(`✅ Map fully loaded in: ${totalTime.toFixed(2)}ms`);

  } catch (error) {
    console.error("Error loading data:", error);
  } finally {
    isLoading.value = false;
  }
});

/**
 * Stop Sending Corny Message
 */
onBeforeUnmount(() => {
  clearInterval(messageInterval);
});

/**
 * Toggle between all listings and top 10 listings
 */
 const showTopTenListings = () => {
    if (activeFilter.value === "topTen") {
        activeFilter.value = "";
        addMarkers(allListings.value, false);
    } else {
        switchFilter("topTen", topTenListings.value);
    }
};

/**
 * Toggle between all listings and bottom 10 listings
 */
 const showBottomTenListings = () => {
    if (activeFilter.value === "bottomTen") {
        activeFilter.value = "";
        addMarkers(allListings.value, false);
    } else {
        switchFilter("bottomTen", bottomTenListings.value);
    }
};

/**
 * Toggle between all listings and clusters
 */
 const showClusters = () => {
    if (activeFilter.value === "cluster") {
        activeFilter.value = "";
        addMarkers(allListings.value, false);
    } else {
        switchFilter("cluster");
        plotClustersOnMap();
    }
};

/**
 * Toggle between price differential and raw price display
 */
const togglePriceDisplayMode = () => {
    priceDisplayMode.value = priceDisplayMode.value === 'differential' ? 'raw' : 'differential';
    // Refresh markers with new color scheme
    if (activeFilter.value === "" || activeFilter.value === null) {
        addMarkers(allListings.value, false);
    } else if (activeFilter.value === "topTen") {
        addMarkers(topTenListings.value, false);
    } else if (activeFilter.value === "bottomTen") {
        addMarkers(bottomTenListings.value, false);
    } else if (activeFilter.value === "cluster") {
        plotClustersOnMap();
    } else {
        // For filtered listings, use merged filters
        mergeFilters();
    }
};

/**
 * Heatmap
 */
const plotHeatmap = () => {
  if (activeFilter.value === "heatmap") {
      activeFilter.value = "";
      addMarkers(allListings.value, false);
  } else {
      switchFilter("heatmap");
      heatmapLayer.value = L.heatLayer(heatmapData.value, {
          radius: 40, 
          blur: 10,   
          maxZoom: 17,
          minOpacity: 0.3, 
          maxOpacity: 0.9  
      }).addTo(map.value);
  }
};

/**
 * Resets the dropdown behind a filter so the controls match activeFilters.
 * Filters without an entry here (toggles, new filters) have no control state to reset.
 */
const filterControlResets = {
  beds: () => { selectedBeds.value = 0; },
  baths: () => { selectedBaths.value = 0; },
  location: () => { selectedLocation.value = ''; },
  commute: () => { selectedCommuteTime.value = ''; },
  budget: () => { selectedBudget.value = 0; },
};

/**
 * Stores fetched filter data, or, if the fetch failed (null), leaves the filter off and says so
 */
const applyFetchedFilter = (key, data) => {
  if (data === null) {
    activeFilters.value[key] = null;
    filterControlResets[key]?.();
    filterError.value = key;
  } else {
    activeFilters.value[key] = data;
    if (filterError.value === key) filterError.value = null;
  }
  mergeFilters();
};

/**
 * Applies the no-results alert's suggestion, updating the dropdowns so the controls stay in sync
 */
const applyRelax = () => {
  const suggestion = relaxHint.value;
  if (!suggestion) return;

  if (suggestion.kind === 'step') {
    // The only step filter is the commute max time
    selectedCommuteTime.value = String(suggestion.value);
    applyCommuteFilter();
  } else {
    filterControlResets[suggestion.key]?.();
    activeFilters.value[suggestion.key] = null;
    mergeFilters();
  }
};

/**
 * Updates the Bed Filter based on the number of beds
 */
const updateBedFilter = async () => {
  if (!selectedBeds.value) {
    // "Any" is no filter at all; no need to ask the API
    activeFilters.value.beds = null;
    mergeFilters();
    return;
  }
  const beds = selectedBeds.value;
  const bedData = await fetchBedFilter(beds);
  if (beds !== selectedBeds.value) return; // A newer choice replaced this one while it loaded
  applyFetchedFilter('beds', bedData);
};


/**
 * Updates the Bath Filter based on the number of baths
 */
const updateBathFilter = async () => {
  if (!selectedBaths.value) {
    activeFilters.value.baths = null;
    mergeFilters();
    return;
  }
  const baths = selectedBaths.value;
  const bathData = await fetchBathFilter(baths*2);
  if (baths !== selectedBaths.value) return; // A newer choice replaced this one while it loaded
  applyFetchedFilter('baths', bathData);
};

/**
 * Updates the Budget Filter (max rent per person). Filters allListings on the
 * client, so it works without a per-filter API endpoint.
 */
const updateBudgetFilter = () => {
  activeFilters.value.budget = selectedBudget.value
    ? filterByBudget(allListings.value, selectedBudget.value)
    : null;
  mergeFilters();
};

const updateLocationFilter = async () => {
  if (!selectedLocation.value || selectedLocation.value === '') {
    // Clear location filter
    activeFilters.value.location = null;
    mergeFilters();
    return;
  }

  // Filter listings by neighborhood
  const locationListings = allListings.value.filter(listing => 
    listing.neighborhood && listing.neighborhood.toLowerCase() === selectedLocation.value.toLowerCase()
  );

  activeFilters.value.location = locationListings;
  mergeFilters(locationListings, true);
};


/**
 * Toggles Walkability Filter based on walking time
 * */
const toggleWalk = async () => {
  if(!activeFilters.value.walk) {
    applyFetchedFilter('walk', await fetchWalkFilter());
  }
  else {
    activeFilters.value.walk = null; 
    mergeFilters();
  }
};

/**
 * Toggles Walkability Filter based on walking time
 * */
 const toggleTransit = async () => {
  if(!activeFilters.value.transit) {
    applyFetchedFilter('transit', await fetchTransitFilter());
  }
  else {
    activeFilters.value.transit = null; 
    mergeFilters();
  }
};

/**
 * Toggles Walkability Filter based on walking time
 * */
 const togglePets = async () => {
  if(!activeFilters.value.pets) {
    applyFetchedFilter('pets', await fetchPetsFilter());
  }
  else {
    activeFilters.value.pets = null; 
    mergeFilters();
  }
};

/**
 * Toggle the commute filter drawer (legacy)
 */
const toggleCommuteDrawer = () => {
  showCommuteDrawer.value = !showCommuteDrawer.value;
};

/**
 * Toggle the new commute panel
 */
const toggleCommutePanel = () => {
  showCommutePanel.value = !showCommutePanel.value;
};

/**
 * Auto-apply commute filter when all three fields are filled, or clear if any is "Any"
 */
const autoApplyCommuteFilter = () => {
  // If any field is set to "Any" (empty value), clear the commute filter
  if (!selectedDestination.value || !selectedCommuteTime.value || !selectedTransitMode.value) {
    // Clear the filter but don't reset the dropdown values
    activeFilters.value.commute = null;
    mergeFilters();
    return;
  }
  
  // If all three fields are filled, apply the filter
  if (selectedDestination.value && selectedCommuteTime.value && selectedTransitMode.value) {
    applyCommuteFilter();
  }
};

/**
 * Apply Commute Filter based on destination, time, and transit mode
 */
const applyCommuteFilter = () => {
  if (!selectedDestination.value || !selectedCommuteTime.value || !selectedTransitMode.value) {
    return;
  }

  const filtered = commuteMatches(parseFloat(selectedCommuteTime.value));
  console.log(`Found ${filtered.length} listings matching criteria`);

  activeFilters.value.commute = filtered;
  mergeFilters();
};

/**
 * Listings within maxTime minutes of the selected destination by the selected mode
 */
const commuteMatches = (maxTime) => {
  // Build the column name based on transit mode and destination
  const columnName = `${selectedTransitMode.value}_time_${selectedDestination.value}`;

  return allListings.value.filter(listing => {
    const travelTime = listing[columnName];
    return travelTime !== null && travelTime !== undefined && travelTime < maxTime;
  });
};

/**
 * Clear Commute Filter
 */
const clearCommuteFilter = () => {
  activeFilters.value.commute = null;
  selectedDestination.value = '';
  selectedCommuteTime.value = '';
  selectedTransitMode.value = '';
  showCommuteDrawer.value = false; // Close drawer when clearing
  showCommutePanel.value = false; // Close panel when clearing
  mergeFilters();
};

/**
 * Apply all filters (placeholder for now)
 */
const applyAllFilters = () => {
  // This can be expanded to apply all filters at once if needed
  console.log('All filters applied');
};

/**
 * Reset all filters
 */

/**
 * Load POI data from CSV files
 */
const loadPOIData = async (type) => {
  if (poiData.value[type].length > 0) {
    // Data already loaded
    return;
  }

  const fileMap = {
    groceries: '/maps/Groceries_ConvinienceStores.csv',
    shopping: '/maps/Shopping.csv',
    attractions: '/maps/Attractions.csv'
  };

  try {
    const response = await fetch(fileMap[type]);
    const text = await response.text();
    
    // Parse CSV manually (simple parser)
    const lines = text.split('\n');
    const headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim());
    
    const data = [];
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue;
      
      // Simple CSV parsing (handles quoted fields)
      const values = [];
      let currentValue = '';
      let insideQuotes = false;
      
      for (let char of lines[i]) {
        if (char === '"') {
          insideQuotes = !insideQuotes;
        } else if (char === ',' && !insideQuotes) {
          values.push(currentValue.trim());
          currentValue = '';
        } else {
          currentValue += char;
        }
      }
      values.push(currentValue.trim());
      
      // Create object from headers and values
      const obj = {};
      headers.forEach((header, index) => {
        obj[header] = values[index];
      });
      
      data.push(obj);
    }
    
    poiData.value[type] = data;
  } catch (error) {
    console.error(`Error loading ${type} POI data:`, error);
  }
};

/**
 * Toggle POI display on map
 */
const togglePOI = async (type) => {
  // If clicking the same type, clear it
  if (activePOI.value === type) {
    if (type === 'neighborhoods') {
      clearNeighborhoodsLayer();
    } else {
      clearPOIMarkers();
    }
    activePOI.value = null;
    return;
  }

  // Clear existing POI markers and neighborhoods layer
  clearPOIMarkers();
  clearNeighborhoodsLayer();

  // Set active POI type
  activePOI.value = type;

  // Handle neighborhoods differently
  if (type === 'neighborhoods') {
    await loadNeighborhoodsLayer();
  } else {
    // Load data if not already loaded
    await loadPOIData(type);
    // Add new markers
    displayPOIMarkers(type);
  }
};

/**
 * Display POI markers on the map
 */
const displayPOIMarkers = (type) => {
  const data = poiData.value[type];
  
  // Icon styles for different POI types
  const iconMap = {
    groceries: { icon: 'fa-shopping-cart', color: '#10b981' },
    shopping: { icon: 'fa-shopping-bag', color: '#f59e0b' },
  };

  const { icon, color } = iconMap[type];

  data.forEach(poi => {
    const lat = parseFloat(poi['location/lat']);
    const lng = parseFloat(poi['location/lng']);
    
    if (isNaN(lat) || isNaN(lng)) return;

    // Create custom icon
    const poiIcon = L.divIcon({
      html: `<div style="background-color: ${color}; opacity: 0.7; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(255,255,255,0.6); box-shadow: 0 1px 2px rgba(0,0,0,0.2);">
        <i class="fa-solid ${icon}" style="color: white; font-size: 10px;"></i>
      </div>`,
      className: 'poi-marker',
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });

    const marker = L.marker([lat, lng], { icon: poiIcon }).addTo(map.value);
    
    // Add popup with POI info
    const popupContent = `
      <div style="min-width: 200px;">
        <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">${poi.title}</h3>
        ${poi.street ? `<p style="margin: 4px 0; font-size: 12px;"><i class="fa-solid fa-location-dot" style="color: ${color}; width: 16px;"></i> ${poi.street}</p>` : ''}
        ${poi.categoryName ? `<p style="margin: 4px 0; font-size: 12px;"><i class="fa-solid fa-tag" style="color: ${color}; width: 16px;"></i> ${poi.categoryName}</p>` : ''}
        ${poi.totalScore ? `<p style="margin: 4px 0; font-size: 12px;"><i class="fa-solid fa-star" style="color: #fbbf24; width: 16px;"></i> ${poi.totalScore} (${poi.reviewsCount} reviews)</p>` : ''}
      </div>
    `;
    
    marker.bindPopup(popupContent);
    poiMarkers.value.push(marker);
  });

  console.log(`Displayed ${poiMarkers.value.length} ${type} markers on the map`);
};

/**
 * Clear all POI markers from the map
 */
const clearPOIMarkers = () => {
  poiMarkers.value.forEach(marker => {
    map.value.removeLayer(marker);
  });
  poiMarkers.value = [];
};

/**
 * Load and display neighborhoods GeoJSON layer
 */
const loadNeighborhoodsLayer = async () => {
  try {
    const response = await fetch('/maps/IthacaN_Cleaned.geojson');
    const geojsonData = await response.json();
    
    // Define colors for different neighborhoods
    const neighborhoodColors = {
      'Collegetown': '#3b82f6',
      'Fall Creek': '#8b5cf6', 
      'North Side': '#f59e0b',
      'Downtown': '#10b981',
      'South Side': '#ef4444',
      'South Hill': '#06b6d4',
      'Belle Sherman': '#84cc16'
    };
    
    neighborhoodsLayer.value = L.geoJSON(geojsonData, {
      style: function(feature) {
        const neighborhoodName = feature.properties.name;
        return {
          color: neighborhoodColors[neighborhoodName] || '#6b7280',
          weight: 2,
          opacity: 0.8,
          fillColor: neighborhoodColors[neighborhoodName] || '#6b7280',
          fillOpacity: 0.2
        };
      },
      onEachFeature: function(feature, layer) {
        const neighborhoodName = feature.properties.name;
        layer.bindPopup(`
          <div style="text-align: center; min-width: 120px;">
            <strong>${neighborhoodName}</strong><br>
            <span style="color: #6b7280; font-size: 0.9em;">Ithaca Neighborhood</span>
          </div>
        `);
      }
    }).addTo(map.value);
    
    console.log('Neighborhoods layer loaded and displayed');
  } catch (error) {
    console.error('Error loading neighborhoods GeoJSON:', error);
  }
};

/**
 * Clear neighborhoods layer from the map
 */
const clearNeighborhoodsLayer = () => {
  if (neighborhoodsLayer.value) {
    map.value.removeLayer(neighborhoodsLayer.value);
    neighborhoodsLayer.value = null;
  }
};

const resetAllFilters = () => {
  selectedBeds.value = 0;
  selectedBaths.value = 0;
  selectedBudget.value = 0;
  selectedLocation.value = '';
  selectedDestination.value = '';
  selectedCommuteTime.value = '';
  selectedTransitMode.value = '';
  
  // Clear POI
  clearPOIMarkers();
  clearNeighborhoodsLayer();
  activePOI.value = null;
  
  // Clear all active filters
  activeFilters.value = { beds: null, baths: null, location: null, walk: null, transit: null, pets: null, roomtorent: null, rent: null, shared: null, commute: null, budget: null };
  
  // Close panels
  showCommuteDrawer.value = false;
  showCommutePanel.value = false;
  filterError.value = null;
  
  mergeFilters();
};

/**
 * Toggles Room to Rent Filter
 */
 const toggleRoomToRent = async () => {
  if (!activeFilters.value.roomtorent) {
    applyFetchedFilter('roomtorent', await fetchRoomToRentListings());
  } else {
    activeFilters.value.roomtorent = null;
    mergeFilters();
  }
};


/**
 * Toggles Rent Filter
 */
 const toggleRent = async () => {
  if (!activeFilters.value.rent) {
    applyFetchedFilter('rent', await fetchRentListings());
  } else {
    activeFilters.value.rent = null;
    mergeFilters();
  }
};

/**
 * Toggles Shared Filter
 */
 const toggleShared = async () => {
  if (!activeFilters.value.shared) {
    applyFetchedFilter('shared', await fetchSharedListings());
  } else {
    activeFilters.value.shared = null;
    mergeFilters();
  }
};


/**
 * Merges every active filter (whatever keys activeFilters has) and redraws the map
 */
function mergeFilters() {
  filteredListings.value = mergeActiveFilters(allListings.value, activeFilters.value);
  addMarkers(filteredListings.value);
}

// Filter options moved to InsideIthacaView


/**
 * Handles switching between different filters without resetting to all markers
 */
 const switchFilter = (newFilter, newListings = null) => {
    markers.value.forEach(marker => map.value.removeLayer(marker)); 
    resetMarkerEntries();

    if (heatmapLayer.value) {
      map.value.removeLayer(heatmapLayer.value); 
    }

    activeFilter.value = newFilter;

    if (newListings) {
        addMarkers(newListings, false);
    } else if (newFilter === "cluster") {
        plotClustersOnMap();
    }
};

/**
 * Plot Clusters on Leaflet Map with Price-Based Opacity
 */
 const plotClustersOnMap = () => {
  if (!map.value) return;
  markers.value.forEach(marker => map.value.removeLayer(marker));
  resetMarkerEntries();

  const clusterColors = [
    "#D73027", // Deep Red (Expensive Urban Core)
    "#FC8D59", // Warm Coral (Mixed Residential-Commercial)
    "#FEE08B", // Yellow (Moderate Suburban)
    "#91CF60", // Soft Green (Affordable Residential)
    "#1A9850", // Deep Green (Outskirts, Lower Prices)
    "#74ADD1", // Soft Blue (Student Areas, Mid Prices)
    "#4575B4", // Strong Blue (Distant Residential)
    "#313695"  // Deep Purple (Luxury or Isolated Areas)
];

  const prices = clusteredListings.value.map(l => l.rentamount_scaled).filter(p => p !== undefined && p !== null);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);

  const getOpacityFromPrice = (price) => {
    const opacity = 0.5 + 0.5 * ((price - minPrice) / (maxPrice - minPrice)); 
    return opacity
  };

  clusteredListings.value.forEach((listing) => {
    const clusterIndex = listing.hierarchal_cluster % clusterColors.length;
    const fillOpacity = getOpacityFromPrice(listing.rentamountadjusted_scaled);

    const marker = L.circleMarker([listing.latitude, listing.longitude], {
      color: clusterColors[clusterIndex],
      fillColor: clusterColors[clusterIndex],
      fillOpacity: fillOpacity,
      radius: 8,
    }).addTo(map.value);
    markers.value.push(marker);
  });
};

/**
 * Closes Rental Sidebar
 */
const closePopup = () => {
    isSidebarVisible.value = false;
    currentRoute.value?.remove();
    
    // Hide isochronic map
    hideIsochronicMap();
    
    // Clear all marker highlights
    clearAllHighlights();
    document.querySelectorAll('.complex-popup-row.active').forEach(row => row.classList.remove('active'));
};

/**
 * Zooms to Location
 * Emitted Function to Rental Sidebar
 * @param lat - Latitude
 * @param lng - Longitude
*/
const zoomToListing = (coords) => {
    map.value.setView([coords.lat, coords.lng], 16);
};

/**
 * Selects a listing from the sidebar (e.g., when clicking "View More" on similar listings)
 * @param listing - The listing to select
 */
const selectListingFromSidebar = async (listing) => {
    await openListing(listing);
};

/**
 * Toggle Menu
 */
// const menuOpen = ref(true);
const toggleMenu = () => (menuOpen.value = !menuOpen.value);
</script>

<style scoped>
/* MAP */
#map {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
}

/* SEARCH BAR */
.search-container {
  position: absolute;
  top: 70px;
  right: 20px;
  z-index: 10;
  width: 350px;
  border: black solid 1px;
}

.search-bar-wrapper {
  position: relative;
}

.search-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #ddd;
  font-size: 16px;
  background: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  outline: none;
}

.search-input:focus {
  box-shadow: 0 2px 15px rgba(80, 124, 182, 0.2);
}

.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-height: 300px;
  overflow-y: auto;
  z-index: 1001;
  margin-top: 4px;
}

.suggestion-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s ease;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover,
.suggestion-item.highlighted {
  background-color: #f8f9fa;
}

.suggestion-address {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.suggestion-details {
  font-size: 14px;
  color: #666;
}

.rental-sidebar {
  position: absolute;
  top: 0%; 
  right: 0;
  width: 600px;
  height: calc(100vh);
  overflow-y: auto;
  background: white;
  box-shadow: -3px 0 15px rgba(0, 0, 0, 0.2);
  z-index: 999; 
  border-left: 1px solid #ddd;
}

/* FILTER ALERTS */
.filter-alerts {
  position: absolute;
  top: 70px;
  left: 50%;
  transform: translateX(-50%);
  width: min(520px, calc(100vw - 760px)); /* Between the filter panel and the search bar */
  z-index: 1002;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none; /* Only the alerts themselves take clicks, not the gap around them */
}

/* Not enough room beside the search bar: drop below it, right of the filter panel */
@media (min-width: 769px) and (max-width: 1280px) {
  .filter-alerts {
    top: 130px;
    left: 360px;
    right: 20px;
    width: auto;
    transform: none;
  }
}

/* FILTER BUTTON */
.personal-filters-container {
  position: absolute;
  top: 100px;
  left: 20px;
  z-index: 1000;
  width: 320px;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 16px;
  border: 1px solid #e2e8f0;
  color: black;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #000000;
  margin: 0;
  white-space: nowrap;
  flex-shrink: 0;
}

.filter-container {
  position: absolute;
  top: 100px;
  left: 20px;
  z-index: 1000;
  width: 320px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  text-align: center;
  visibility: visible;
}

.filter-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #000000;
  margin-bottom: 16px;
  text-align: left;
}

.filter-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.filter-group {
  flex: 1;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.filter-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #000000;
  margin-bottom: 0;
}

.filter-select {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  background: #ffffff;
  color: #000000;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-select:hover {
  border-color: #cbd5e1;
  background: #ffffff;
}

.filter-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  background: #ffffff;
}

.icon-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}

.icon-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  color: #000000;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-button:hover {
  border-color: #cbd5e1;
  background: #ffffff;
}

.icon-button.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

/* Duplicate filter-title removed */


/* Tab Navigation */
.tab-header {
  display: flex;
  justify-content: space-between;
}

.tab-button {
  flex: 1;
  padding: 10px;
  font-weight: bold;
  border: none;
  background: rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  color: black;
  border-radius: 8px 8px 0 0;
}

.tab-button.active {
  background: #507cb6;
  color: white;
}

/* Tab Content */
.tab-content {
  background: white;
  color: black;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

/* Radio Buttons */
.radio-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  color: black;
  padding: 12px 15px;
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
  text-align: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.filter-button:hover {
  background: #e0e0e0;
}

.filter-button.active {
  background: #507cb6;
  color: white;
  border: 2px solid #0f5dc7;
}

.filter-button.active .filter-label {
  color: white;
}


.checkmark .icon {
  width: 16px;
  height: 16px;
}

/* Personal Filters */
.personal-filters {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-label {
  font-size: 0.8rem;
  color: #444;
  font-weight: 500;
  text-align: left;
  margin-bottom: 4px;
}

.filter-select {
  width: 100%;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid #ccc;
  background: #f8f8f8;
  color: #333;
  font-size: 0.85rem;
  appearance: none;
  cursor: pointer;
  outline: none;
}

.icon-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
}

.icon-button {
  flex: 1;
  margin: 0 4px;
  padding: 8px;
  background-color: #f4f4f4;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: 0.2s;
}

.icon-button.active {
  background-color: #507cb6; /* Blue highlight */
  color: white;
}




/* 🔵 LEGEND STYLING */
.legend {
  position: absolute;
  bottom: 30px;
  left: 30px;
  padding: 10px 15px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  color: #444;
  z-index: 1000;
  line-height: 1.5;
}

.legend h4 {
  margin: 0 0 8px;
  font-size: 0.95rem;
  color: #333;
}

.legend ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.legend ul li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #444;
  margin-bottom: 4px;
}

.legend ul li span {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1px solid #ddd;
}

.disclaimer {
  font-size: 0.6rem;
  color: #666;
  font-style: italic;
  line-height: 1.4;
  max-width: 200px;      
  white-space: normal;
  word-break: break-word;
  text-align: left;
  margin-top: 10px;
}

/* New gradient legend styles */
.gradient-legend {
  margin-bottom: 8px;
}

.gradient-bar {
  width: 100%;
  height: 20px;
  background: linear-gradient(to right, #d73027, #fee08b, #1a9850);
  border-radius: 10px;
  border: 1px solid #ccc;
  margin-bottom: 8px;
}

.gradient-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #666;
  position: relative;
}

.label-start, .label-end {
  font-weight: 600;
}

.label-middle {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  font-weight: 600;
  color: #333;
}

.legend-disclaimer {
  font-size: 0.65rem;
  color: #666;
  margin-top: 8px;
  line-height: 1.3;
  text-align: center;
}

.legend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}

.legend-header h4 {
  margin: 0;
  flex: 1;
}

.price-mode-toggle {
  padding: 4px 8px;
  font-size: 0.7rem;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.price-mode-toggle:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.price-mode-toggle:active {
  background: #d1d5db;
}

.disclaimer-disclaimer {
  font-size: 0.4rem;
  color: #666;
  word-wrap: break-word;
  white-space: normal;
  max-width: 100%;
  margin-top: 8px;
  line-height: 1.3;
  text-align: center;
}


.leaflet-popup-close-button {
  display: none;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 9999;
  width: 100%;
  height: 100%;
  backdrop-filter: blur(8px);
  background-color: rgba(255, 255, 255, 0.3); /* subtle frosted glass effect */
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  transition: opacity 0.3s ease-in-out;
}

.loading-text {
  margin-top: 16px;
  font-size: 1.1rem;
  font-weight: 500;
  color: #1e1e1e;
  font-family: 'Inter', sans-serif;
  text-align: center;
  opacity: 0.9;
  letter-spacing: 0.3px;
}

/* New sexy spinner */
.spinner {
  width: 48px;
  height: 48px;
  border: 5px solid transparent;
  border-top: 5px solid #0077ff;
  border-right: 5px solid #0077ff;
  border-radius: 50%;
  animation: spin 0.7s cubic-bezier(0.6, 0, 0.4, 1) infinite;
  box-shadow: 0 0 10px rgba(0, 119, 255, 0.3);
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Commute Filter Drawer Styles */
.commute-filter-trigger {
  margin: 12px 0;
  display: flex;
  justify-content: center;
}

.commute-trigger-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #f3f4f6;
  border: 2px solid #e5e7eb;
  border-radius: 25px;
  font-weight: 600;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.commute-trigger-btn:hover {
  background: #e5e7eb;
  border-color: #d1d5db;
  transform: translateY(-1px);
}

.commute-trigger-btn.active {
  background: #6366f1;
  border-color: #4f46e5;
  color: white;
}

.filter-badge {
  background: #ef4444;
  color: white;
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 0.75rem;
  font-weight: 700;
  min-width: 20px;
  text-align: center;
}

.commute-drawer {
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  margin: 12px 0;
  overflow: hidden;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.drawer-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.close-drawer-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-drawer-btn:hover {
  background: #e2e8f0;
  color: #475569;
}

.drawer-content {
  padding: 20px;
}

/* Commute Section */
.commute-section {
  margin: 12px 0;
  border-top: 1px solid #f3f4f6;
  padding-top: 12px;
}

.commute-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.commute-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-badge {
  background: #10b981;
  color: white;
  border-radius: 12px;
  padding: 4px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
  flex-shrink: 0;
}

.filter-row-commute {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

/* Reset Section */


/* POI Buttons */
.poi-buttons {
  display: flex;
  flex-direction: row;
  gap: 8px;
}

.poi-btn {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 10px;
  background: white;
  color: #4b5563;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.poi-btn i {
  font-size: 0.85rem;
}

.poi-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.poi-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.poi-btn.active:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
}

/* Specific POI button colors when active */
.poi-btn.active:nth-child(1) {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-color: #10b981;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.poi-btn.active:nth-child(2) {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.poi-btn.active:nth-child(3) {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border-color: #8b5cf6;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.reset-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
  display: flex;
  justify-content: center;
}

.reset-btn {
  padding: 6px 16px;
  background: #f8fafc;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #475569;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Hamburger Icon (Mobile only) */
.hamburger {
  display: none;
  flex-direction: column;
  cursor: pointer;
  gap: 4px;
}

@media (max-width: 768px) {
  .filter-container {
    position: absolute;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    width: 90vw;
    max-width: 420px;
    background: white;
    border-radius: 18px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
    z-index: 1001;
    animation: slideUp 0.4s ease-out;
    overflow: hidden;
    padding: 16px;
  }

  .tab-header {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 12px;
  }

  .tab-button {
    flex: 1;
    padding: 10px;
    font-weight: bold;
    border: none;
    background: #f1f1f1;
    cursor: pointer;
    border-radius: 8px;
    transition: all 0.3s ease;
    color: #333;
  }

  .tab-button.active {
    background: #507cb6;
    color: white;
  }

  .tab-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .rental-sidebar {
    position: fixed;
    top: 35%;
    left: 50%;
    transform: translateX(-50%);
    width: 95vw;
    max-height: 60vh;
    height: auto;
    border-radius: 16px 16px 0 0;
    border-left: none;
    border-right: none;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.2);
    z-index: 9999;
    overflow-y: auto;
    background: #ffffff;
    padding: 16px;
    padding-top: 0px;
    animation: slideUp 0.3s ease-in-out;
  }

  .legend {
    bottom: 20px;
    left: 10px;
    right: 10px;
    width: auto;
    max-width: 90vw;
    padding: 12px;
    font-size: 0.85rem;
  }

  .legend h4 {
    font-size: 1rem;
  }

  .legend ul li {
    font-size: 0.8rem;
  }

  .legend ul li span {
    width: 14px;
    height: 14px;
  }

  .disclaimer {
    font-size: 0.65rem;
    max-width: 100%;
    margin-top: 8px;
  }
  
  .disclaimer-disclaimer {
    font-size: 0.5rem;
    word-wrap: break-word;
    white-space: normal;
    max-width: 100%;
    line-height: 1.4;
  }

  @keyframes slideUp {
    from {
      transform: translate(-50%, 100%);
      opacity: 0;
    }
    to {
      transform: translate(-50%, 0%);
      opacity: 1;
    }
  }

  /* POI Buttons Mobile */
  .poi-buttons {
    flex-direction: row;
    gap: 8px;
  }

  .poi-btn {
    flex: 1;
    padding: 10px 12px;
    font-size: 0.85rem;
  }

  .poi-btn i {
    font-size: 1rem;
  }
}

/* Quad icon styling */
.quad-icon {
  background: transparent !important;
  border: none !important;
}

.quad-popup .leaflet-popup-content-wrapper {
  background: #d97706;
  color: white;
  border-radius: 8px;
  font-weight: 600;
  text-align: center;
}

.quad-popup .leaflet-popup-tip {
  background: #d97706;
}

/* Mobile-specific styles */
/* Ensure Leaflet popups appear above mobile filter toggle and improve mobile spacing */


.desktop-recommendation-popup {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.popup-content {
  background: white;
  border-radius: 16px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  animation: popupSlideIn 0.3s ease-out;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.popup-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.popup-body {
  padding: 20px 24px;
}

.popup-body p {
  margin: 0 0 16px 0;
  color: #374151;
  line-height: 1.5;
}

.popup-body p:last-of-type {
  margin-bottom: 12px;
}

.popup-body ul {
  margin: 0;
  padding-left: 20px;
  color: #4b5563;
}

.popup-body li {
  margin-bottom: 8px;
  line-height: 1.4;
}

.popup-footer {
  padding: 16px 24px 24px;
  border-top: 1px solid #e5e7eb;
}

.continue-btn {
  width: 100%;
  background: #507cb6;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.continue-btn:hover {
  background: #3d5a87;
}

.mobile-filter-toggle {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1001;
  background: #507cb6;
  color: white;
  border: none;
  border-radius: 50px;
  padding: 12px 20px;
  box-shadow: 0 4px 16px rgba(80, 124, 182, 0.4);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  animation: slideUp 0.4s ease-out;
}

.mobile-filter-toggle:hover {
  background: #3d5a87;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(80, 124, 182, 0.5);
}

.mobile-filter-toggle.active {
  background: #dc2626;
}

.mobile-filter-toggle i {
  font-size: 16px;
}

.mobile-filter-toggle span {
  font-size: 14px;
}

/* Hide filter container on mobile when not active */
.personal-filters-container.mobile-hidden {
  display: none;
}

/* Animation for popup */
@keyframes popupSlideIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Update existing mobile styles */
@media (max-width: 768px) {
  .personal-filters-container:not(.mobile-hidden) {
    position: fixed;
    bottom: 80px; /* Above the toggle button */
    left: 50%;
    transform: translateX(-50%);
    width: 90vw;
    max-width: 420px;
    background: white;
    border-radius: 18px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
    z-index: 1001;
    animation: slideUp 0.4s ease-out;
    overflow: hidden;
    padding: 16px;
    max-height: 80vh;
    overflow-y: auto;
  }
  
  /* Ensure map takes full space on mobile */
  #map {
    height: 100vh !important;
  }
  
  /* Adjust legend position on mobile */
  .legend {
    bottom: 120px; /* Above the filter toggle */
    right: 20px;
    left: 20px;
    width: auto;
    padding: 12px;
    font-size: 0.8rem;
  }

  /* Filter alerts: full width under the search bar, fixed so they stay above the open filter panel */
  .filter-alerts {
    position: fixed;
    top: 124px;
    left: 16px;
    right: 16px;
    width: auto;
    transform: none;
  }
}

</style>
