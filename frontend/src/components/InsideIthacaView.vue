<template>
  <NavBar />
  <div class="inside-ithaca-container">
    <!-- Header -->
    <div class="header">
      <h1>Inside Ithaca</h1>
      <p>Explore rental hotspots and market trends across Ithaca</p>
    </div>

    <!-- Two Column Layout -->
    <div class="content-grid">
      <!-- Left Half: Explore Ithaca -->
      <div class="explore-section">
        <h2>Explore Ithaca</h2>
        <div class="filter-container">
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
        
        <!-- Map -->
        <div class="map-container">
          <div id="explore-map" class="explore-map"></div>
        </div>
      </div>

      <!-- Right Half: Breaking Down the Rental Market -->
      <div class="market-analysis-section">
        <h2>Breaking Down the Rental Market</h2>
        <div class="placeholder-content">
          <p>Market analysis content will be added here...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import { RadioGroup, RadioGroupLabel, RadioGroupOption } from "@headlessui/vue";
import { fetchClusters, fetchHeatMap, fetchListingsMinimal } from '@/services/fetch';
import NavBar from "@/components/NavBar.vue";

// Map and data variables
const exploreMap = ref(null);
const activeFilter = ref('');
const allListings = ref([]);
const clusteredListings = ref([]);
const heatmapData = ref(null);
const heatmapLayer = ref(null);
const markers = ref([]);

// Filter functions (defined before filterOptions)
const showClusters = () => {
  if (clusteredListings.value && clusteredListings.value.length > 0) {
    plotClustersOnMap();
  } else {
    console.warn('No cluster data available yet');
    // Optionally reload cluster data
    loadClusters();
  }
};

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
    }).addTo(exploreMap.value);
  }
};

// Filter options (moved from MapView)
const filterOptions = [
  { value: "heatmap", label: "Market Hotspots", action: plotHeatmap },
  { value: "cluster", label: "Rental Neighborhoods", action: showClusters },
];

onMounted(async () => {
  await initializeMap();
  await loadData();
});

onBeforeUnmount(() => {
  if (exploreMap.value) {
    exploreMap.value.remove();
  }
});

async function initializeMap() {
  exploreMap.value = L.map('explore-map', {
    center: [42.455, -76.48],
    zoom: 13,
    maxZoom: 20,
  });

  const JAWG_API_KEY = import.meta.env.VITE_JAWG_API_KEY;
  const tileLayer = L.tileLayer(`https://tile.jawg.io/f67529a2-5ea7-4b7a-81a7-c5147a45b5f0/{z}/{x}/{y}{r}.png?access-token=${JAWG_API_KEY}`, {
    attribution: '<a href="https://jawg.io" target="_blank">&copy; Jawg Maps</a> &copy; OpenStreetMap contributors',
    minZoom: 0,
    maxZoom: 22,
    accessToken: JAWG_API_KEY
  });

  tileLayer.addTo(exploreMap.value);
}

async function loadData() {
  try {
    // Load all the data we need
    const [listings, clusters, heatmap] = await Promise.all([
      fetchListingsMinimal(),
      fetchClusters(),
      fetchHeatMap()
    ]);
    
    allListings.value = listings;
    clusteredListings.value = clusters;
    heatmapData.value = heatmap;
    
    console.log('Data loaded:', {
      listings: listings.length,
      clusters: clusters.length,
      heatmap: heatmap ? heatmap.length : 0
    });
  } catch (error) {
    console.error('Error loading data:', error);
  }
}

async function loadClusters() {
  try {
    const clusters = await fetchClusters();
    clusteredListings.value = clusters;
    console.log('Clusters loaded:', clusters.length);
    plotClustersOnMap();
  } catch (error) {
    console.error('Error loading clusters:', error);
  }
}

// Filter functions already defined above

const switchFilter = (newFilter) => {
  markers.value.forEach(marker => exploreMap.value.removeLayer(marker)); 
  markers.value = [];

  if (heatmapLayer.value) {
    exploreMap.value.removeLayer(heatmapLayer.value); 
    heatmapLayer.value = null;
  }

  activeFilter.value = newFilter;
};

const addMarkers = (listings, filtered) => {
  markers.value.forEach(marker => exploreMap.value.removeLayer(marker)); 
  markers.value = []; 

  if (heatmapLayer.value) {
    exploreMap.value.removeLayer(heatmapLayer.value); 
  }

  listings.forEach(listing => {
    // Validate coordinates - skip if invalid
    if (!listing.latitude || !listing.longitude || 
        isNaN(listing.latitude) || isNaN(listing.longitude) ||
        listing.latitude === null || listing.longitude === null) {
      console.warn('Skipping listing with invalid coordinates:', listing);
      return;
    }

    const color = getColor(listing.rent_per_person, listing.predictedrent);

    const marker = L.circleMarker([listing.latitude, listing.longitude], {
      color,
      fillColor: color,
      fillOpacity: 0.85,
      radius: 10,
      weight: 2,
      opacity: 1,
      className: 'modern-dot'
    }).addTo(exploreMap.value);

    markers.value.push(marker); 
  });
};

const plotClustersOnMap = () => {
  if (!exploreMap.value) return;

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
    return Math.max(0.3, Math.min(0.9, opacity));
  };

  clusteredListings.value.forEach((cluster, index) => {
    // Validate coordinates - skip if invalid
    if (!cluster.latitude || !cluster.longitude || 
        isNaN(cluster.latitude) || isNaN(cluster.longitude) ||
        cluster.latitude === null || cluster.longitude === null) {
      console.warn('Skipping cluster with invalid coordinates:', cluster);
      return;
    }

    const colorIndex = index % clusterColors.length;
    const color = clusterColors[colorIndex];
    const opacity = getOpacityFromPrice(cluster.rentamount_scaled || 0);

    console.log(cluster, index)
    const circle = L.circleMarker([cluster.latitude, cluster.longitude], {
      radius: 8,
      fillColor: color,
      color: color,
      weight: 2,
      opacity: 1,
      fillOpacity: opacity
    }).addTo(exploreMap.value);

    circle.bindPopup(`
      <div style="text-align: center; min-width: 120px;">
        <strong>Rental Hotspot</strong><br>
        Listings: ${cluster.count}<br>
        Avg Rent: $${cluster.avg_rent?.toFixed(2) || 'N/A'}<br>
        Area: ${cluster.radius}m radius
      </div>
    `);

    markers.value.push(circle);
  });
};

const getColor = (rentPerPerson, predictedRent) => {
  if (!rentPerPerson || !predictedRent) return '#6b7280';
  
  const difference = rentPerPerson - predictedRent;
  const percentDiff = (difference / predictedRent) * 100;
  
  if (percentDiff <= -10) return '#10b981'; // Green - significantly underpriced
  if (percentDiff <= -5) return '#34d399';  // Light green - underpriced
  if (percentDiff <= 5) return '#fbbf24';   // Yellow - fair price
  if (percentDiff <= 10) return '#f59e0b';  // Orange - overpriced
  return '#ef4444'; // Red - significantly overpriced
};
</script>

<style scoped>
.inside-ithaca-container {
  margin-top: 50px;
  min-width: 100vw;
  background: #f8fafc;
  padding: 2rem;
}

.header {
  text-align: center;
  margin-bottom: 3rem;
}

.header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.header p {
  font-size: 1.1rem;
  color: #6b7280;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  align-items: start;
}

.explore-section,
.market-analysis-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  height: fit-content;
}

.explore-section h2,
.market-analysis-section h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.placeholder-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: #f8fafc;
  border-radius: 8px;
  border: 2px dashed #d1d5db;
}

.placeholder-content p {
  color: #6b7280;
  font-size: 1.1rem;
  text-align: center;
}

.filter-container {
  margin-bottom: 1.5rem;
}

.filter-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 1rem;
}

.radio-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
}

.filter-button:hover {
  border-color: #9ca3af;
  background: #f9fafb;
}

.filter-button.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

.filter-label {
  font-weight: 500;
}

.checkmark {
  display: flex;
  align-items: center;
}

.checkmark .icon {
  width: 16px;
  height: 16px;
}

.map-container {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.explore-map {
  height: 500px;
  width: 100%;
}

@media (max-width: 768px) {
  .inside-ithaca-container {
    padding: 1rem;
  }
  
  .header h1 {
    font-size: 2rem;
  }
  
  .content-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .explore-map {
    height: 400px;
  }
  
  .placeholder-content {
    min-height: 300px;
  }
}
</style>