<template>
  <NavBar />
  <div class="overflow-auto box-border m-0 p-0">
    <!-- Loading Spinner -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p class="loading-text">{{ loadingMessage }}</p>
    </div>
    <div class="filter-container">
      <!-- Tab Navigation -->
      <div class="tab-header">
        <button
          class="tab-button"
          :class="{ active: activeTab === 'Explore Ithaca' }"
          @click="changeTab('Explore Ithaca')"
        >
          Explore Ithaca
        </button>
        <button
          class="tab-button"
          :class="{ active: activeTab === 'Personal Taste' }"
          @click="changeTab('Personal Taste')"
        >
          Personal Taste
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Explore Ithaca Tab -->
        <div v-if="activeTab === 'Explore Ithaca'">
          <RadioGroup v-model="activeFilter">
            <RadioGroupLabel class="filter-title">Explore Ithaca</RadioGroupLabel>
            <div class="radio-options">
              <RadioGroupOption 
                as="template" 
                v-for="option in filterOptions" 
                :key="option.value" 
                :value="option.value" 
                v-slot="{ checked }"
              >
                <button 
                  class="filter-button"
                  :class="{ active: checked }"
                  @click="option.action"
                >
                  <span class="filter-label">{{ option.label }}</span>
                  <span v-if="checked" class="checkmark">
                    <svg class="icon" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="12" fill="white" fill-opacity="0.2"/>
                      <path d="M7 13l3 3 7-7" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </span>
                </button>
              </RadioGroupOption>
            </div>
          </RadioGroup>
        </div>

        <!-- Personal Taste Tab -->
        <div v-if="activeTab === 'Personal Taste'">
          <h3 class="filter-title">Personal Taste</h3>
          <div class="personal-filters">
            <label for="bed-filter" class="filter-label">Beds</label>
            <select id="bed-filter" v-model="selectedBeds" @change="updateBedFilter" class="filter-select">
              <option :value="0">N/A Beds</option>
              <option v-for="n in bedOptions" :key="n" :value="n">{{ n }} Beds</option>
            </select>

            <label for="bath-filter" class="filter-label">Baths</label>
            <select id="bath-filter" v-model="selectedBaths" @change="updateBathFilter" class="filter-select">
              <option :value="0">N/A Baths</option>
              <option v-for="n in bathOptions" :key="n" :value="n">{{ n }} Baths</option>
            </select>

            <div class="icon-buttons">
              <button 
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
              </button>
              <button 
                @click="togglePets" 
                :class="['icon-button', { active: activeFilters.pets !== null }]"
              >
                🐶 Pets
              </button>
            </div>
            <!-- <div class="icon-buttons">
              <button 
                @click="toggleRoomToRent" 
                :class="['icon-button', { active: activeFilters.roomtorent !== null }]"
              >
                🚶‍♂️ Room
              </button>
              <button 
                @click="toggleRent" 
                :class="['icon-button', { active: activeFilters.rent !== null }]"
              >
                🚌 Full
              </button>
              <button 
                @click="toggleShared" 
                :class="['icon-button', { active: activeFilters.shared !== null }]"
              >
                🐶 Shared
              </button>
            </div> -->
          </div>
        </div>
      </div>
    </div>

    <!-- Map Container -->
    <div class="relative flex z-[0] border-b-2 border-black overflow-hidden">
      <RentalSidebar class="rental-sidebar" @close="closePopup" @zoom="zoomToListing" :listing="selectedListing" v-if="isSidebarVisible" />

      <div id="map"></div>

      <!-- Legend -->
      <div class="legend">
        <h4>Price Difference Legend</h4>
        <ul>
          <li><span style="background: #006400;"></span> Very Underpriced</li>
          <li><span style="background: #008000;"></span> Underpriced</li>
          <li><span style="background: #32CD32;"></span> Slightly Underpriced</li>
          <li><span style="background: #90EE90;"></span> Barely Underpriced</li>
          <li><span style="background: #FFA07A;"></span> Barely Overpriced</li>
          <li><span style="background: #FF6347;"></span> Slightly Overpriced</li>
          <li><span style="background: #FF0000;"></span> Overpriced</li>
          <li><span style="background: #8B0000;"></span> Very Overpriced</li>
        </ul>
        <p class="disclaimer">Note: These estimates are based on a statistical model and should be taken with a grain of salt. They’re meant to inform, not replace, your own research and judgment.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { fetchListings, fetchTopTenListings, fetchBottomTenListings, fetchClusters, fetchHeatMap, fetchBedFilter, fetchBathFilter, fetchWalkFilter, fetchTransitFilter, fetchPetsFilter, fetchRentListings, fetchRoomToRentListings, fetchSharedListings } from "@/services/fetch";
import NavBar from "@/components/NavBar.vue";
import RentalSidebar from "@/components/RentalSidebar.vue";
import { RadioGroup, RadioGroupLabel, RadioGroupOption } from "@headlessui/vue";
import "leaflet.heat";

const map = ref(null); // Holds the ref for the map
const isSidebarVisible = ref(false); // Toggle state for whether the Rental Sidebar is visible or not
const selectedListing = ref(null); // Holds the prop state for the selected listing to pass to RentalSidebar
const markers = ref([]); // Store all markers
const allListings = ref([]); // Store all listings
const topTenListings = ref([]); // Store top 10 listings
const bottomTenListings = ref([]); // Store bottom 10 listings
const clusteredListings = ref([]); // Store Clustered Listings
const heatmapData = ref(null); // Stores the Heatmap Data
const heatmapLayer = ref(null); // Stores the Heatmap Layer
const activeTab = ref("Explore Ithaca"); // Default tab
let activeFilter = ref(null); // Tracks which filter is selected

const activeFilters = ref({ beds: null, baths: null, walk: null, transit: null, pets: null, roomtorent: null, rent: null, shared: null }); // Holds Bath and Bed Data for Dynamic Filtering
const filteredListings = ref([]); // Keeps track of the filtered listings
const selectedBeds = ref(0); // Number of Selected Beds
const bedOptions = [1, 2, 3, 4, 5]; // Adjust based on available data
const selectedBaths = ref(0); // Number of Selected Beds
const bathOptions = [1, 1.5, 2, 2.5, 3]; // Adjust based on available data
const currentRoute = ref(null);

const isLoading = ref(true); // Add loading state

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
  "Visit cornelldatajournal.org!",
];


/**
 * Gets the color of the dot based on price
 * @param rent - Actual rent
 * @param predicted - Predicted rent
 */
function getColor(rent, predicted) {
    const percent_change = (predicted - rent) / rent;
    if (percent_change >= 0.30) return "#006400"; // Dark Green (Very Underpriced)
    if (percent_change >= 0.20) return "#008000"; // Green (Underpriced)
    if (percent_change >= 0.10) return "#32CD32";  // Lime Green (Slightly Underpriced)
    if (percent_change > 0) return "#90EE90";     // Light Green (Barely Underpriced)

    if (percent_change <= -0.30) return "#8B0000"; // Dark Red (Very Overpriced)
    if (percent_change <= -0.20) return "#FF0000"; // Red (Overpriced)
    if (percent_change <= -0.10) return "#FF6347";  // Tomato (Slightly Overpriced)
    if (percent_change < 0) return "#FFA07A";    // Light Salmon (Barely Overpriced)

    return "gray"; // Neutral (Fairly Priced)
}

function changeTab(tab) {
  activeFilters.value = { beds: null, baths: null, walk: null, transit: null, pets: null, roomtorent: null, rent: null, shared: null };
  activeTab.value = tab
  activeFilter.value = "";
  addMarkers(allListings.value, false);
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
    const dispersedListings = groupListingsByLocation(listings);

    dispersedListings.forEach(listing => {
        const color = getColor(listing.rentamountadjusted, listing.predictedrent);

        const marker = L.circleMarker([listing.displayLat, listing.displayLng], {
          color,
          fillColor: color,                // dynamic fill based on pricing
          fillOpacity: 0.85,               // more saturated look
          radius: listing.isGrouped ? 8 : 10, // Slightly smaller for grouped
          weight: 2,                       // thin border
          opacity: 1,                      // full circle border visibility
          className: 'modern-dot'          // for custom CSS glow
        }).addTo(map.value);


        marker.on("click", () => {
            selectedListing.value = listing;
            currentRoute.value = plotRoute(listing).addTo(map.value);
            isSidebarVisible.value = true;
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
    const coordsText = wkt
      .replace('LINESTRING (', '')
      .replace(')', '')
      .trim();

    const coords = coordsText.split(',').map(pair => {
      const [lng, lat] = pair.trim().split(' ').map(Number);
      return [lat, lng]; 
    });

    return coords;
  }

  const currentPolyline = L.polyline(parseWKTLineString(listing.walk_routes), {
    color: 'orange',
    weight: 4,
    opacity: 0.7
  })

  return currentPolyline;
}
/**
 * Lifecycle Hook on Mount
 * Fetches Data from API and initializes Map
 */
 onMounted(async () => {
  messageInterval = setInterval(() => {
    messageIndex = (messageIndex + 1) % messages.length;
    loadingMessage.value = messages[messageIndex];
  }, 2500);

  try {
    map.value = L.map("map", {
      center: [42.455, -76.48],
      zoom: 14,
      maxZoom: 20,
    });

    const JAWG_API_KEY = import.meta.env.VITE_JAWG_API_KEY;
    const tileLayer = L.tileLayer(`https://tile.jawg.io/f67529a2-5ea7-4b7a-81a7-c5147a45b5f0/{z}/{x}/{y}{r}.png?access-token=${JAWG_API_KEY}`, {
      attribution: '<a href="https://jawg.io" target="_blank">&copy; Jawg Maps</a> &copy; OpenStreetMap contributors',
      minZoom: 0,
      maxZoom: 22,
      accessToken: JAWG_API_KEY
    });
    tileLayer.addTo(map.value);

    const [listings, top, bottom, clusters, heat] = await Promise.all([
      fetchListings(),
      fetchTopTenListings(),
      fetchBottomTenListings(),
      fetchClusters(),
      fetchHeatMap()
    ]);

    // Store values and add to map
    allListings.value = listings;
    topTenListings.value = top;
    bottomTenListings.value = bottom;
    clusteredListings.value = clusters;
    heatmapData.value = heat;

    addMarkers(listings, false);

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

/**
 * Define Options For Filter
 */
const filterOptions = [
    { value: "topTen", label: "Best Bang For Your Buck", action: showTopTenListings },
    { value: "bottomTen", label: "Avoid These Listings", action: showBottomTenListings },
    { value: "heatmap", label: "Market Hotspots", action: plotHeatmap },
    { value: "cluster", label: "Rental Neighborhoods", action: showClusters },
];


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
  font-size: 1.6rem;
  color: #333;
  font-weight: bold;
  margin-bottom: 12px;
}


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
}

</style>
