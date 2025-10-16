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
              <label for="bed-filter" class="filter-label">🛏️ Beds</label>
              <select id="bed-filter" v-model="selectedBeds" @change="updateBedFilter" class="filter-select">
                <option :value="0">Any</option>
                <option v-for="n in bedOptions" :key="n" :value="n">{{ n }}</option>
              </select>
            </div>

            <div class="filter-group">
              <label for="bath-filter" class="filter-label">🛁 Baths</label>
              <select id="bath-filter" v-model="selectedBaths" @change="updateBathFilter" class="filter-select">
                <option :value="0">Any</option>
                <option v-for="n in bathOptions" :key="n" :value="n">{{ n }}</option>
              </select>
            </div>
          </div>

          <!-- Location Row -->
          <div class="filter-row">
            <div class="filter-group">
              <label for="location-filter" class="filter-label">🏘️  Neighborhood</label>
              <select id="location-filter" v-model="selectedLocation" @change="updateLocationFilter" class="filter-select">
                <option value="">Any neighborhood</option>
                <option v-for="neighborhood in availableNeighborhoods" :key="neighborhood" :value="neighborhood">
                  {{ neighborhood }}
                </option>
              </select>
            </div>
          </div>

          <!-- Commute Section -->
          <div class="commute-section">
            <div class="commute-header">
              <h4 class="commute-title">🚶 Commute</h4>
            </div>

            <div class="filter-row-commute">
              <div class="filter-group">
                <label for="destination-filter" class="filter-label">Destination</label>
                <select id="destination-filter" v-model="selectedDestination" @change="autoApplyCommuteFilter" class="filter-select">
                  <option value="">Any</option>
                  <option value="urishall">Uris Hall</option>
                  <option value="agriculturequad">Ag Quad</option>
                  <option value="artsquad">Arts Quad</option>
                  <option value="engineeringquad">Eng Quad</option>
                </select>
              </div>

              <div class="filter-group">
                <label for="commute-time-filter" class="filter-label">Max time</label>
                <select id="commute-time-filter" v-model="selectedCommuteTime" @change="autoApplyCommuteFilter" class="filter-select">
                  <option value="">Any</option>
                  <!-- <option value="10">10 min</option> -->
                  <option value="15">15 min</option>
                  <option value="20">20 min</option>
                  <option value="25">25 min</option>
                  <option value="30">30 min</option>
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
            <label for="bed-filter" class="filter-label">📍 Points of Interest</label>
            <div class="poi-buttons">
              <button 
                @click="togglePOI('groceries')" 
                :class="['poi-btn', { active: activePOI === 'groceries' }]"
              >
                <i class="fa-solid fa-shopping-basket"></i>
                Groceries
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
              <div class="suggestion-details">{{ suggestion.available_bedrooms }} bed • ${{ suggestion.rent }}</div>
            </div>
          </div>
        </div>
      </div>

      <div id="map"></div>

      <!-- Legend -->
      <div class="legend">
        <h4>Price Difference Legend</h4>
        <div class="gradient-legend">
          <div class="gradient-bar"></div>
          <div class="gradient-labels">
            <span class="label-start">Overpriced</span>
            <span class="label-middle">Fair Price</span>
            <span class="label-end">Underpriced</span>
          </div>
        </div>
        <div class="legend-disclaimer">
          Colors show how actual rent compares to predicted rent
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { fetchListings, fetchListing, fetchListingsMinimal, fetchTopTenListings, fetchBottomTenListings, fetchClusters, fetchHeatMap, fetchBedFilter, fetchBathFilter, fetchWalkFilter, fetchTransitFilter, fetchPetsFilter, fetchRentListings, fetchRoomToRentListings, fetchSharedListings } from "@/services/fetch";
import NavBar from "@/components/NavBar.vue";
import RentalSidebar from "@/components/RentalSidebar.vue";
import { RadioGroup, RadioGroupLabel, RadioGroupOption } from "@headlessui/vue";
import "leaflet.heat";
import "@fortawesome/fontawesome-svg-core/styles.css";

const map = ref(null); // Holds the ref for the map
const isSidebarVisible = ref(false); // Toggle state for whether the Rental Sidebar is visible or not
const selectedListing = ref(null); // Holds the prop state for the selected listing to pass to RentalSidebar
const selectedMarker = ref(null); // Holds the currently selected marker for highlighting
const markers = ref([]); // Store all markers
const dispersedListings = ref([]); // Store dispersed listings for search matching
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

const activeFilters = ref({ beds: null, baths: null, location: null, walk: null, transit: null, pets: null, roomtorent: null, rent: null, shared: null, commute: null }); // Holds Bath and Bed Data for Dynamic Filtering
const filteredListings = ref([]); // Keeps track of the filtered listings
const selectedBeds = ref(0); // Number of Selected Beds
const bedOptions = [1, 2, 3, 4, 5]; // Adjust based on available data
const selectedBaths = ref(0); // Number of Selected Baths
const bathOptions = [1, 1.5, 2, 2.5, 3]; // Adjust based on available data
const selectedLocation = ref(''); // Selected Location
const selectedDestination = ref(''); // Selected Destination for commute filter
const selectedCommuteTime = ref(''); // Selected Max Commute Time
const selectedTransitMode = ref(''); // Selected Transit Mode (walk/bike/drive)
const showCommuteDrawer = ref(false); // Controls visibility of commute filter drawer (legacy)
const showCommutePanel = ref(false); // Controls visibility of new commute panel

// Points of Interest variables
const activePOI = ref(null); // Tracks which POI is currently displayed

// Mobile functionality variables
const isMobile = ref(false); // Tracks if user is on mobile
const showMobileFilters = ref(false); // Controls mobile filter visibility
const showDesktopRecommendation = ref(false); // Controls desktop recommendation popup
const poiMarkers = ref([]); // Stores POI markers on the map
const poiData = ref({ groceries: [], shopping: [], attractions: [] }); // Stores loaded POI data

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
  "Texting your ex-girlfriend you miss her",
  "Powered by Maitrix Labs",
];


/**
 * Gets the color of the dot based on price
 * @param rent - Actual rent
 * @param predicted - Predicted rent
 */
function getColor(rent, predicted) {
    const percent_change = (predicted - rent) / rent;
    
    // Clamp percent_change to a narrower range for more dramatic colors (-0.2 to 0.2)
    const clamped = Math.max(-0.2, Math.min(0.2, percent_change));
    
    // Normalize to 0-1 range (0 = very overpriced, 1 = very underpriced)
    const normalized = (clamped + 0.2) / 0.4;
    
    // Interpolate between the three colors
    // Red (#d73027) -> Yellow (#fee08b) -> Green (#1a9850)
    if (normalized <= 0.5) {
        // Interpolate between red and yellow
        const t = normalized * 2; // 0 to 1
        return interpolateColor('#d73027', '#fee08b', t);
    } else {
        // Interpolate between yellow and green
        const t = (normalized - 0.5) * 2; // 0 to 1
        return interpolateColor('#fee08b', '#1a9850', t);
    }
}

// Helper function to interpolate between two hex colors
function interpolateColor(color1, color2, factor) {
    const hex1 = color1.replace('#', '');
    const hex2 = color2.replace('#', '');
    
    const r1 = parseInt(hex1.substr(0, 2), 16);
    const g1 = parseInt(hex1.substr(2, 2), 16);
    const b1 = parseInt(hex1.substr(4, 2), 16);
    
    const r2 = parseInt(hex2.substr(0, 2), 16);
    const g2 = parseInt(hex2.substr(2, 2), 16);
    const b2 = parseInt(hex2.substr(4, 2), 16);
    
    const r = Math.round(r1 + (r2 - r1) * factor);
    const g = Math.round(g1 + (g2 - g1) * factor);
    const b = Math.round(b1 + (b2 - b1) * factor);
    
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
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
    selectedMarker.value = null;
}

/**
 * Highlights the selected marker
 */
function highlightSelectedMarker(listing) {
    // Clear ALL highlights first
    clearAllHighlights();

    // Use displayLat/displayLng if available, otherwise fall back to latitude/longitude
    const lat = listing.displayLat || listing.latitude;
    const lng = listing.displayLng || listing.longitude;

    // Find and highlight the new marker (with small tolerance for floating point precision)
    const marker = markers.value.find(m => {
        const markerLat = m.getLatLng().lat;
        const markerLng = m.getLatLng().lng;
        const latDiff = Math.abs(markerLat - lat);
        const lngDiff = Math.abs(markerLng - lng);
        return latDiff < 0.0001 && lngDiff < 0.0001; // Very small tolerance
    });

    console.log('Looking for marker at:', lat, lng);
    console.log('Available markers:', markers.value.length);

    
    if (marker) {
        selectedMarker.value = marker;
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
}

/**
 * Group listings by exact coordinates and apply dispersion offset
 */
function groupListingsByLocation(listings) {
    const locationGroups = {};
    
    listings.forEach(listing => {
        const key = `${listing.latitude},${listing.longitude}`;
        if (!locationGroups[key]) {
            locationGroups[key] = [];
        }
        locationGroups[key].push(listing);
    });
    
    // Apply offset to listings at the same location
    const dispersedListings = [];
    Object.values(locationGroups).forEach(group => {
        if (group.length === 1) {
            // Single listing, no offset needed
            dispersedListings.push({
                ...group[0],
                displayLat: group[0].latitude,
                displayLng: group[0].longitude
            });
        } else {
            // Multiple listings at same location - create circular dispersion
            const radius = 0.00005; // ~11 meters offset
            group.forEach((listing, index) => {
                const angle = (2 * Math.PI * index) / group.length;
                const offsetLat = Math.cos(angle) * radius;
                const offsetLng = Math.sin(angle) * radius;
                
                dispersedListings.push({
                    ...listing,
                    displayLat: listing.latitude + offsetLat,
                    displayLng: listing.longitude + offsetLng,
                    isGrouped: true,
                    groupSize: group.length
                });
            });
        }
    });
    
    return dispersedListings;
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
 * Add markers to the map
 * Only filters markers CURRENTLY on map using .some 
 */
function addMarkers(listings, filtered) {
    markers.value.forEach(marker => map.value.removeLayer(marker)); 
    markers.value = []; 

    if (heatmapLayer.value) {
      map.value.removeLayer(heatmapLayer.value); 
    }

    // Apply dispersion to overlapping listings
    const dispersed = groupListingsByLocation(listings);
    dispersedListings.value = dispersed; // Store for search matching

    dispersed.forEach(listing => {
        const color = getColor(listing.rent_per_person, listing.predictedrent);

        const marker = L.circleMarker([listing.displayLat, listing.displayLng], {
          color,
          fillColor: color,                // dynamic fill based on pricing
          fillOpacity: 0.85,               // more saturated look
          radius: listing.isGrouped ? 8 : 10, // Slightly smaller for grouped
          weight: 2,                       // thin border
          opacity: 1,                      // full circle border visibility
          className: 'modern-dot'          // for custom CSS glow
        }).addTo(map.value);


        marker.on("click", async () => {
            // Load full listing data when clicked
            const fullListing = await fetchListing(listing.listingid);
            if (fullListing) {
                selectedListing.value = fullListing;
                highlightSelectedMarker(listing);
                currentRoute.value = plotRoute(fullListing).addTo(map.value);
                // displayIsochronicMap(fullListing); // Display isochronic map
                isSidebarVisible.value = true;
            }
        });

        markers.value.push(marker); 
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
  const suggestions = dispersedListings.value
    .map(listing => ({
      ...listing,
      score: Math.max(
        fuzzyMatch(query, listing.listingaddress || ''),
        fuzzyMatch(query, listing.listingcity || ''),
        fuzzyMatch(query, `${listing.listingaddress} ${listing.listingcity}` || '')
      )
    }))
    .filter(listing => listing.score > 0.3)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map(listing => ({
      address: `${listing.listingaddress}, ${listing.listingcity}`,
      bedrooms: listing.available_bedrooms || 'N/A',
      rent: listing.rent_per_person || listing.rentamount || 'N/A',
      listing: listing
    }));
  
  searchSuggestions.value = suggestions;
  highlightedIndex.value = -1;
};

const selectSuggestion = async (suggestion) => {
  showSuggestions.value = false;
  
  // Center map on the selected listing (without zooming)
  if (suggestion.listing && suggestion.listing.latitude && suggestion.listing.longitude) {
    map.value.setView([suggestion.listing.latitude, suggestion.listing.longitude], map.value.getZoom());
    
    // Load full listing data when selected from search
    const fullListing = await fetchListing(suggestion.listing.listingid);
    if (fullListing) {
      selectedListing.value = fullListing;
      highlightSelectedMarker(suggestion.listing);
      currentRoute.value = plotRoute(fullListing).addTo(map.value);
      // displayIsochronicMap(fullListing); // Display isochronic map
      isSidebarVisible.value = true;
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
      const response = await fetch('/src/assets/cornell_main_boundary.geojson');
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
 * Updates the Bed Filter based on the number of beds
 */
const updateBedFilter = async () => {
  const bedData = await fetchBedFilter(selectedBeds.value);
  activeFilters.value.beds = bedData; 
  mergeFilters();
};


/**
 * Updates the Bed Filter based on the number of beds
 */
const updateBathFilter = async () => {
  const bathFilterInput = selectedBaths.value*2
  const bathData = await fetchBathFilter(bathFilterInput);
  activeFilters.value.baths = bathData; 
  mergeFilters(bathData, true);
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
    const walkData = await fetchWalkFilter();
    activeFilters.value.walk = walkData; 
    mergeFilters(walkData, true);
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
    const transit = await fetchTransitFilter();
    activeFilters.value.transit = transit; 
    mergeFilters(transit, true);
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
    const petsData = await fetchPetsFilter();
    activeFilters.value.pets = petsData; 
    mergeFilters(petsData, true);
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

  // Build the column name based on transit mode and destination
  const columnName = `${selectedTransitMode.value}_time_${selectedDestination.value}`;
  const maxTime = parseFloat(selectedCommuteTime.value);

  // Filter listings based on the selected criteria
  const filtered = allListings.value.filter(listing => {
    const travelTime = listing[columnName];
    return travelTime !== null && travelTime !== undefined && travelTime < maxTime;
  });

  console.log(`Commute filter applied: ${columnName} < ${maxTime} minutes`);
  console.log(`Found ${filtered.length} listings matching criteria`);

  activeFilters.value.commute = filtered;
  mergeFilters();
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
    clearPOIMarkers();
    activePOI.value = null;
    return;
  }

  // Load data if not already loaded
  await loadPOIData(type);

  // Clear existing POI markers
  clearPOIMarkers();

  // Set active POI type
  activePOI.value = type;

  // Add new markers
  displayPOIMarkers(type);
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

const resetAllFilters = () => {
  selectedBeds.value = 0;
  selectedBaths.value = 0;
  selectedLocation.value = '';
  selectedDestination.value = '';
  selectedCommuteTime.value = '';
  selectedTransitMode.value = '';
  
  // Clear POI
  clearPOIMarkers();
  activePOI.value = null;
  
  // Clear all active filters
  activeFilters.value = { beds: null, baths: null, location: null, walk: null, transit: null, pets: null, roomtorent: null, rent: null, shared: null, commute: null };
  
  // Close panels
  showCommuteDrawer.value = false;
  showCommutePanel.value = false;
  
  mergeFilters();
};

/**
 * Toggles Room to Rent Filter
 */
 const toggleRoomToRent = async () => {
  if (!activeFilters.value.roomtorent) {
    const roomData = await fetchRoomToRentListings();
    activeFilters.value.roomtorent = roomData;
    mergeFilters(roomData, true);
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
    const rentData = await fetchRentListings();
    activeFilters.value.rent = rentData;
    mergeFilters(rentData, true);
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
    const sharedData = await fetchSharedListings();
    activeFilters.value.shared = sharedData;
    mergeFilters(sharedData, true);
  } else {
    activeFilters.value.shared = null;
    mergeFilters();
  }
};


/**
 * Merges Bed and Bath Filters
 */
function mergeFilters() {
  let mergedListings = allListings.value; 

  // Merge Beds
  if (activeFilters.value.beds) {
    mergedListings = mergedListings.filter(listing =>
      activeFilters.value.beds.some(bedListing =>
        bedListing.latitude === listing.latitude && bedListing.longitude === listing.longitude
      )
    );
  }

  // Merge Baths
  if (activeFilters.value.baths) {
    mergedListings = mergedListings.filter(listing =>
      activeFilters.value.baths.some(bathListing =>
        bathListing.latitude === listing.latitude && bathListing.longitude === listing.longitude
      )
    );
  }

  // Merge Location
  if (activeFilters.value.location) {
    mergedListings = mergedListings.filter(listing =>
      activeFilters.value.location.some(locationListing =>
        locationListing.latitude === listing.latitude && locationListing.longitude === listing.longitude
      )
    );
  }

  // Merge Walks
  if (activeFilters.value.walk) {
    mergedListings = mergedListings.filter(listing =>
      activeFilters.value.walk.some(walkListing =>
        walkListing.latitude === listing.latitude && walkListing.longitude === listing.longitude
      )
    );
  }

  // Merge Transit
  if (activeFilters.value.transit) {
    mergedListings = mergedListings.filter(listing =>
      activeFilters.value.transit.some(transitListing =>
        transitListing.latitude === listing.latitude && transitListing.longitude === listing.longitude
      )
    );
  }

  // Merge Pets
  if (activeFilters.value.pets) {
    mergedListings = mergedListings.filter(listing =>
      activeFilters.value.pets.some(petsListing =>
        petsListing.latitude === listing.latitude && petsListing.longitude === listing.longitude
      )
    );
  }

  // Merge Commute Filter
  if (activeFilters.value.commute) {
    mergedListings = mergedListings.filter(listing =>
      activeFilters.value.commute.some(commuteListing =>
        commuteListing.latitude === listing.latitude && commuteListing.longitude === listing.longitude
      )
    );
  }
  
  // Merge Rooms to Rent
  if (activeFilters.value.roomtorent) {
    mergedListings = mergedListings.filter(listing =>
      activeFilters.value.roomtorent.some(roomListing =>
        roomListing.latitude === listing.latitude && roomListing.longitude === listing.longitude
      )
    );
  }

  // Merge Rent
  if (activeFilters.value.rent) {
    mergedListings = mergedListings.filter(listing =>
      activeFilters.value.rent.some(rentListing =>
        rentListing.latitude === listing.latitude && rentListing.longitude === listing.longitude
      )
    );
  }

  // Merge Shared
  if (activeFilters.value.shared) {
    mergedListings = mergedListings.filter(listing =>
      activeFilters.value.shared.some(sharedListing =>
        sharedListing.latitude === listing.latitude && sharedListing.longitude === listing.longitude
      )
    );
  }

  // Add to map
  filteredListings.value = mergedListings;
  addMarkers(filteredListings.value);
}

// Filter options moved to InsideIthacaView


/**
 * Handles switching between different filters without resetting to all markers
 */
 const switchFilter = (newFilter, newListings = null) => {
    markers.value.forEach(marker => map.value.removeLayer(marker)); 

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
    // Load full listing data
    const fullListing = await fetchListing(listing.listingid);
    if (fullListing) {
        selectedListing.value = fullListing;
        highlightSelectedMarker(listing);
        currentRoute.value = plotRoute(fullListing).addTo(map.value);
        // displayIsochronicMap(fullListing); // Display isochronic map
        isSidebarVisible.value = true;
    }
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
  padding: 20px;
  border: 1px solid #e2e8f0;
  color: black;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  font-size: 1.1rem;
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
  gap: 12px;
  margin-bottom: 16px;
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
  font-size: 1rem;
  color: #444;
  font-weight: 500;
  text-align: left;
}

.filter-select {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #ccc;
  background: #f8f8f8;
  color: #333;
  font-size: 1rem;
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
  margin: 20px 0;
  border-top: 2px solid #f3f4f6;
  padding-top: 20px;
}

.commute-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.commute-title {
  font-size: 1rem;
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
  gap: 16px;
}

/* Reset Section */


/* POI Buttons */
.poi-buttons {
  display: flex;
  flex-direction: row;
  gap: 12px;
}

.poi-btn {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: white;
  color: #4b5563;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.poi-btn i {
  font-size: 1.1rem;
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
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border-color: #f59e0b;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

.poi-btn.active:nth-child(3) {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border-color: #8b5cf6;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.reset-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 2px solid #f3f4f6;
  display: flex;
  justify-content: center;
}

.reset-btn {
  padding: 12px 24px;
  background: #f8fafc;
  color: #64748b;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.875rem;
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
}

</style>
