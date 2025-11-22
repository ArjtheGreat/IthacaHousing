<template>
  <NavBar />
  <div class="inside-ithaca-container">
    <!-- Header -->
    <div class="header">
      <h1>Inside Ithaca</h1>
      <p>Explore rental hotspots and market trends across Ithaca</p>
    </div>

    <!-- 2x2 Grid Layout -->
    <div class="content-grid">
      <!-- Top Left: Map -->
      <div class="explore-section">
        <h2>Spatial Trends Panel</h2>
        <div class="filter-container">
          <RadioGroup v-model="activeFilter">
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
          
          <!-- Legend for neighborhoods view -->
          <div v-if="activeFilter === 'neighborhoods'" class="map-legend">
            <h4>Median Rent by Neighborhood</h4>
            <div class="legend-items">
              <div class="legend-item">
                <div class="legend-color" style="background: #1e40af;"></div>
                <span>Low</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #3b82f6;"></div>
                <span>Medium-Low</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #8b5cf6;"></div>
                <span>Medium</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #f59e0b;"></div>
                <span>High</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background: #dc2626;"></div>
                <span>Very High</span>
              </div>
            </div>
          </div>
         </div>
         
          <!-- Moran's I -->
          <div v-if="pipelineMetrics" class="metric-card">
             <h3>🔍 Spatial Autocorrelation</h3>
             <div class="metric-item">
               <span class="metric-label">Average Moran's I</span>
               <span class="metric-value">{{ (pipelineMetrics.spatial_patterns?.average_moran_i || 0).toFixed(3) }}</span>
             </div>
             <div class="moran-description">
               <small>{{ getMoranInterpretation(pipelineMetrics.spatial_patterns?.average_moran_i || 0) }}</small>
             </div>
           </div>
           
      </div>
      

      <!-- Top Right: Descriptive Statistics -->
      <div class="stats-section">
        <h2>Income Panel</h2>
        
        <div v-if="pipelineMetrics" class="metrics-container">
          <!-- Mean Rent Time Series -->
          <div class="metric-card">
            <h3>📈 Mean Rent Trend</h3>
            <div v-if="meanRentTimeSeries.length > 0" class="time-series-container">
              <div class="chart-container">
                <canvas ref="meanRentChart" class="time-series-chart"></canvas>
              </div>
              <div class="current-value">
                <span class="metric-label">Current Mean Rent</span>
                <span class="metric-value">${{ Math.round(pipelineMetrics.spatial_patterns?.mean_rent || 0) }}</span>
              </div>
            </div>
          </div>
          <!-- Market Pricing -->
          <div class="metric-card">
            <h3>💰 Market Pricing</h3>
            <div class="pricing-split">
              <div class="pricing-item overpriced">
                <span class="pricing-label">Overpriced</span>
                <span class="pricing-value">{{ Math.round(pipelineMetrics.overpricing?.percent_overpriced || 0) }}%</span>
              </div>
              <div class="pricing-item underpriced">
                <span class="pricing-label">Underpriced</span>
                <span class="pricing-value">{{ Math.round((100 - (pipelineMetrics.overpricing?.percent_overpriced || 0))) }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-else-if="loadingMetrics" class="loading-metrics">
          <p>Loading market analysis...</p>
        </div>

        <!-- Error State -->
        <div v-else class="error-metrics">
          <p>Unable to load market analysis</p>
        </div>
      </div>

      <!-- Bottom Left: Model Information -->
      <div class="model-section">
        <h2>Model Performance Panel</h2>
        
        <div v-if="pipelineMetrics" class="metrics-container">
          <!-- Best Model -->
          <div class="metric-card">
            <h3>🏆 Best Model</h3>
            <div class="model-info">
              <span class="model-name">{{ pipelineMetrics.model_performance?.best_model || 'N/A' }}</span>
              <div class="model-metrics">
                <div class="model-metric">
                  <span class="metric-label">R²</span>
                  <span class="metric-value">{{ ((pipelineMetrics.model_performance?.best_model_metrics?.R2 || 0) * 100).toFixed(1) }}%</span>
                </div>
                <div class="model-metric">
                  <span class="metric-label">RMSE</span>
                  <span class="metric-value">{{ (pipelineMetrics.model_performance?.best_model_metrics?.RMSE || 0).toFixed(3) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Feature Importance -->
          <div v-if="topFeatures.length > 0" class="metric-card">
            <h3>🎯 Key Features</h3>
            <div class="feature-list">
              <div v-for="(feature, index) in topFeatures" :key="index" class="feature-item">
                <span class="feature-name">{{ feature.name }}</span>
                <div class="feature-bar">
                  <div class="feature-bar-fill" :style="{ width: `${feature.importance * 100}%` }"></div>
                </div>
                <span class="feature-value">{{ (feature.importance * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Right: Landlords -->
      <div class="landlords-section">
        <h2>Risk Panel</h2>
        
        <div v-if="pipelineMetrics" class="metrics-container">
          <!-- Top Overpriced Landlords -->
          <div v-if="topOverpricedLandlords.length > 0" class="metric-card">
            <h3>🔴 Most Overpriced</h3>
            <div class="landlord-list">
              <div v-for="(landlord, index) in topOverpricedLandlords" :key="index" class="landlord-item">
                <span class="landlord-name">{{ landlord.name }}</span>
                <span class="landlord-price">+${{ Math.round(landlord.price) }}</span>
              </div>
            </div>
          </div>

          <!-- Top Underpriced Landlords -->
          <div v-if="topUnderpricedLandlords.length > 0" class="metric-card">
            <h3>🟢 Most Underpriced</h3>
            <div class="landlord-list">
              <div v-for="(landlord, index) in topUnderpricedLandlords" :key="index" class="landlord-item underpriced">
                <span class="landlord-name">{{ landlord.name }}</span>
                <span class="landlord-price">-${{ Math.round(landlord.price) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loadingMetrics && !pipelineMetrics" class="loading-overlay">
      <p>Loading dashboard...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import { RadioGroup, RadioGroupLabel, RadioGroupOption } from "@headlessui/vue";
import { fetchClusters, fetchHeatMap, fetchListings, fetchListingsMinimal, fetchPipelineMetrics } from '@/services/fetch';
import NavBar from "@/components/NavBar.vue";
import Chart from 'chart.js/auto';

// Map and data variables
const exploreMap = ref(null);
const activeFilter = ref('');
const allListings = ref([]);
const clusteredListings = ref([]);
const heatmapData = ref(null);
const heatmapLayer = ref(null);
const markers = ref([]);
const neighborhoodData = ref([]);
const neighborhoodsLayer = ref(null);
const currentNeighborhoodLayer = ref(null);
const baseNeighborhoodLayer = ref(null); // Always-visible base outlines

// Pipeline metrics variables
const pipelineMetrics = ref(null);
const loadingMetrics = ref(false);
const meanRentChart = ref(null);
const chartInstance = ref(null);

// Computed properties for processed metrics
const topOverpricedLandlords = computed(() => {
  if (!pipelineMetrics.value?.landlord_behavior) return [];
  
  const landlords = Object.entries(pipelineMetrics.value.landlord_behavior)
    .filter(([name, price]) => {
      // Filter out empty strings, empty objects, and non-overpriced landlords
      const cleanName = name.replace(/[\[\]'"]/g, '').trim();
      return cleanName && cleanName !== 'nan' && cleanName !== '{}' && price > 0;
    })
    .map(([name, price]) => ({
      name: name.replace(/[\[\]'"]/g, '').trim(),
      price: price
    }))
    .sort((a, b) => b.price - a.price)
    .slice(0, 3);
    
  return landlords;
});

const topUnderpricedLandlords = computed(() => {
  if (!pipelineMetrics.value?.landlord_behavior) return [];
  
  console.log('🔍 Debug: landlord_behavior data:', pipelineMetrics.value.landlord_behavior);
  
  const landlords = Object.entries(pipelineMetrics.value.landlord_behavior)
    .filter(([name, price]) => {
      // Filter out empty strings, empty objects, and non-underpriced landlords
      const cleanName = name.replace(/[\[\]'"]/g, '').trim();
      return cleanName && cleanName !== 'nan' && cleanName !== '{}' && price < 0;
    })
    .map(([name, price]) => ({
      name: name.replace(/[\[\]'"]/g, '').trim(),
      price: Math.abs(price) // Make price positive for display
    }))
    .sort((a, b) => b.price - a.price)
    .slice(0, 3);
    
  console.log('🔍 Debug: filtered underpriced landlords:', landlords);
  return landlords;
});

const topFeatures = computed(() => {
  if (!pipelineMetrics.value?.feature_importance?.all_features) return [];
  
  return pipelineMetrics.value.feature_importance.all_features
    .slice(0, 5)
    .map(feature => ({
      name: feature.feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      importance: feature.importance
    }));
});

const meanRentTimeSeries = computed(() => {
  return pipelineMetrics.value?.spatial_patterns?.mean_rent_time_series || [];
});

// Helper function to interpret Moran's I values
const getMoranInterpretation = (moranI) => {
  if (moranI > 0.3) return "Strong positive spatial autocorrelation";
  if (moranI > 0.1) return "Moderate positive spatial autocorrelation";
  if (moranI > -0.1) return "Weak spatial autocorrelation";
  if (moranI > -0.3) return "Moderate negative spatial autocorrelation";
  return "Strong negative spatial autocorrelation";
};

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
    if (heatmapLayer.value) {
      exploreMap.value.removeLayer(heatmapLayer.value);
      heatmapLayer.value = null;
    }
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

// Calculate neighborhood statistics
const calculateNeighborhoodStats = () => {
  if (!allListings.value || allListings.value.length === 0) {
    console.warn('No listings data available');
    return [];
  }

  // Group listings by neighborhood
  const neighborhoods = {};
  
  allListings.value.forEach(listing => {
    const neighborhood = listing.neighborhood || 'Unknown';
    if (!neighborhoods[neighborhood]) {
      neighborhoods[neighborhood] = {
        name: neighborhood,
        listings: [],
        avgRent: 0,
        medianRent: 0,
        count: 0
      };
    }
    
    const rent = listing.rent_per_person || listing.rentamount || 0;
    if (rent > 0) {
      neighborhoods[neighborhood].listings.push(rent);
      neighborhoods[neighborhood].count++;
    }
  });

  // Calculate statistics for each neighborhood
  const neighborhoodList = Object.values(neighborhoods).map(neighborhood => {
    const rents = neighborhood.listings.filter(r => r > 0).sort((a, b) => a - b);
    
    neighborhood.avgRent = rents.length > 0 
      ? rents.reduce((sum, r) => sum + r, 0) / rents.length 
      : 0;
    
    neighborhood.medianRent = rents.length > 0
      ? rents[Math.floor(rents.length / 2)]
      : 0;
    
    return neighborhood;
  }).filter(n => n.count > 0);

  return neighborhoodList;
};

const showNeighborhoodsByRent = () => {
  if (activeFilter.value === "neighborhoods") {
    // Toggle off: remove colored layer, keep base outlines
    activeFilter.value = "";
    if (currentNeighborhoodLayer.value) {
      exploreMap.value.removeLayer(currentNeighborhoodLayer.value);
      currentNeighborhoodLayer.value = null;
    }
    return;
  }

  if (!allListings.value || allListings.value.length === 0) {
    console.warn('No listings data available');
    return;
  }

  if (!neighborhoodsLayer.value) {
    console.warn('Neighborhoods GeoJSON not loaded yet');
    return;
  }

  const neighborhoods = calculateNeighborhoodStats();
  neighborhoodData.value = neighborhoods;
  
  if (neighborhoods.length === 0) {
    console.warn('No neighborhoods found with rent data');
    return;
  }

  // Remove existing markers and heatmap
  switchFilter('neighborhoods');
  
  // Remove existing colored layer if it exists (base outlines stay)
  if (currentNeighborhoodLayer.value) {
    exploreMap.value.removeLayer(currentNeighborhoodLayer.value);
  }
  
  // Calculate rent range for color coding
  const rents = neighborhoods.map(n => n.medianRent).filter(r => r > 0);
  const minRent = Math.min(...rents);
  const maxRent = Math.max(...rents);
  
  // Create a map of neighborhood names to rent data
  const neighborhoodRentMap = {};
  neighborhoods.forEach(neighborhood => {
    neighborhoodRentMap[neighborhood.name] = neighborhood;
  });
  
  // Create the colored choropleth layer (on top of base outlines)
  currentNeighborhoodLayer.value = L.geoJSON(neighborhoodsLayer.value, {
    style: function(feature) {
      const neighborhoodName = feature.properties.name;
      const rentData = neighborhoodRentMap[neighborhoodName];
      
      if (!rentData || rentData.medianRent === 0) {
        return {
          color: '#6b7280',
          weight: 2,
          opacity: 0.8,
          fillColor: '#6b7280',
          fillOpacity: 0.1
        };
      }
      
      const color = getRentColor(rentData.medianRent, minRent, maxRent);
      return {
        color: color,
        weight: 2.5,
        opacity: 0.9,
        fillColor: color,
        fillOpacity: 0.6
      };
    },
    onEachFeature: function(feature, layer) {
      const neighborhoodName = feature.properties.name;
      const rentData = neighborhoodRentMap[neighborhoodName];
      
      if (rentData && rentData.medianRent > 0) {
        layer.bindPopup(`
          <div style="text-align: center; min-width: 150px;">
            <strong>${neighborhoodName}</strong><br>
            Listings: ${rentData.count}<br>
            Median Rent: $${rentData.medianRent.toFixed(2)}<br>
            Avg Rent: $${rentData.avgRent.toFixed(2)}
          </div>
        `);
      } else {
        layer.bindPopup(`
          <div style="text-align: center; min-width: 120px;">
            <strong>${neighborhoodName}</strong><br>
            <span style="color: #6b7280; font-size: 0.9em;">No rental data available</span>
          </div>
        `);
      }
    }
  }).addTo(exploreMap.value);
  
  console.log(`Displayed ${neighborhoods.length} neighborhoods as choropleth`);
};

const getRentColor = (rent, minRent, maxRent) => {
  if (maxRent === minRent) return '#3b82f6';
  
  const normalized = (rent - minRent) / (maxRent - minRent);
  
  // Color gradient from blue (low) to red (high)
  if (normalized < 0.2) return '#1e40af'; // Dark blue
  if (normalized < 0.4) return '#3b82f6'; // Blue
  if (normalized < 0.6) return '#8b5cf6'; // Purple
  if (normalized < 0.8) return '#f59e0b'; // Orange
  return '#dc2626'; // Red
};

const showOutlierListings = () => {
  if (activeFilter.value === "outliers") {
    activeFilter.value = "";
    markers.value.forEach(marker => exploreMap.value.removeLayer(marker));
    markers.value = [];
    return;
  }

  if (!allListings.value || allListings.value.length === 0) {
    console.warn('No listings data available');
    return;
  }

  if (!pipelineMetrics.value?.lisa_for_each_point) {
    console.warn('No LISA data available');
    return;
  }

  console.log(pipelineMetrics.value)
  let lisaData = pipelineMetrics.value.lisa_for_each_point;
  
  if (!Array.isArray(lisaData)) {
    if (lisaData && typeof lisaData === 'object') {
      lisaData = Object.values(lisaData);
    } else {
      console.warn('LISA data is not in expected format:', lisaData);
      return;
    }
  }  
  const outlierListingIds = lisaData
    .filter(item => item && (item.cluster_type === 'Low-High Outlier' || item.cluster_type === 'High-Low Outlier'))
    .map(item => item.listing_id);

  const outlierListings = allListings.value.filter((listing, index) => {
    return outlierListingIds.includes(index) || 
           outlierListingIds.includes(listing.listingid) ||
           outlierListingIds.includes(listing.listingId);
  });

  const outlierIdSet = new Set(
    outlierListingIds
      .filter(id => id !== null && id !== undefined)
      .map(id => String(id))
  );

  const nonOutlierListings = allListings.value.filter((listing, index) => {
    const identifiers = [
      index,
      listing.listingid,
      listing.listingId
    ].filter(id => id !== null && id !== undefined)
     .map(id => String(id));

    return !identifiers.some(id => outlierIdSet.has(id));
  });

  if (outlierListings.length === 0) {
    console.warn('No outlier listings found');
    return;
  }

  switchFilter('outliers');
  
  // Add muted markers for non-outlier listings to provide context
  nonOutlierListings.forEach(listing => {
    if (!listing.latitude || !listing.longitude || 
        isNaN(listing.latitude) || isNaN(listing.longitude)) {
      return;
    }

    const marker = L.circleMarker([listing.latitude, listing.longitude], {
      color: '#9ca3af',
      fillColor: '#9ca3af',
      fillOpacity: 0.4,
      radius: 5,
      weight: 1,
      opacity: 0.7,
      className: 'non-outlier-marker'
    }).addTo(exploreMap.value);

    markers.value.push(marker);
  });

  // Add markers for outlier listings
  outlierListings.forEach(listing => {
    if (!listing.latitude || !listing.longitude || 
        isNaN(listing.latitude) || isNaN(listing.longitude)) {
      return;
    }

    // Find the LISA data for this listing
    const lisaItem = lisaData.find(item => 
      item.listing_id === listing.listingid || 
      item.listing_id === listing.listingId ||
      item.listing_id === allListings.value.indexOf(listing)
    );

    // Color based on outlier type
    let color = '#f59e0b'; // Default orange
    if (lisaItem?.cluster_type === 'Low-High Outlier') {
      color = '#ef4444'; // Red - low value surrounded by high
    } else if (lisaItem?.cluster_type === 'High-Low Outlier') {
      color = '#3b82f6'; // Blue - high value surrounded by low
    }

    const marker = L.circleMarker([listing.latitude, listing.longitude], {
      color: color,
      fillColor: color,
      fillOpacity: 0.85,
      radius: 12,
      weight: 3,
      opacity: 1,
      className: 'outlier-marker'
    }).addTo(exploreMap.value);

    // Create popup content
    const popupContent = `
      <div style="text-align: left; min-width: 200px;">
        <strong>${lisaItem?.cluster_type || 'Outlier'}</strong><br>
        ${listing.listingaddress || 'N/A'}<br>
        Rent: $${(listing.rent_per_person || listing.rentamount || 0).toFixed(2)}<br>
        ${lisaItem ? `Moran's I: ${lisaItem.I.toFixed(3)}<br>p-value: ${lisaItem.p_value.toFixed(3)}` : ''}
      </div>
    `;
    marker.bindPopup(popupContent);
    markers.value.push(marker);
  });

  console.log(`Displayed ${outlierListings.length} outlier listings with ${nonOutlierListings.length} contextual listings`);
};

// Filter options (moved from MapView)
const filterOptions = [
  { value: "heatmap", label: "Market Hotspots", action: plotHeatmap },
  { value: "neighborhoods", label: "By Median Rent", action: showNeighborhoodsByRent },
  { value: "outliers", label: "Outlier Listings", action: showOutlierListings },
];

onMounted(async () => {
  await initializeMap();
  await loadData();
});

onBeforeUnmount(() => {
  if (exploreMap.value) {
    exploreMap.value.remove();
  }
  if (chartInstance.value) {
    chartInstance.value.destroy();
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
  
  // Add Ithaca neighborhoods GeoJSON layer
  await loadNeighborhoodsLayer();
}

async function loadNeighborhoodsLayer() {
  try {
    const response = await fetch('/maps/IthacaN_Cleaned.geojson');
    const geojsonData = await response.json();
    
    // Store the GeoJSON data for later use
    neighborhoodsLayer.value = geojsonData;
    
    // Always add base neighborhood outlines (no fill, just boundaries)
    if (exploreMap.value && neighborhoodsLayer.value) {
      baseNeighborhoodLayer.value = L.geoJSON(neighborhoodsLayer.value, {
        style: {
          color: '#6b7280',
          weight: 1.5,
          opacity: 0.6,
          fillColor: 'transparent',
          fillOpacity: 0
        },
        onEachFeature: function(feature, layer) {
          const neighborhoodName = feature.properties.name;
          layer.bindPopup(`
            <div style="text-align: center; min-width: 120px;">
              <strong>${neighborhoodName}</strong><br>
              <span style="color: #6b7280; font-size: 0.9em;">Click "By Median Rent" for pricing data</span>
            </div>
          `);
        }
      }).addTo(exploreMap.value);
      
      console.log('✅ Base neighborhood outlines added to map');
    }
    
  } catch (error) {
    console.error('Error loading neighborhoods GeoJSON:', error);
  }
}

async function loadPipelineMetrics() {
  try {
    loadingMetrics.value = true;
    const metrics = await fetchPipelineMetrics();
    if (metrics) {
      pipelineMetrics.value = metrics;
      // Create chart after metrics are loaded
      await nextTick();
      createMeanRentChart();
    }
  } catch (error) {
    console.error("Error loading pipeline metrics:", error);
  } finally {
    loadingMetrics.value = false;
  }
}

function createMeanRentChart() {
  if (!meanRentChart.value || !meanRentTimeSeries.value.length) return;
  
  // Destroy existing chart if it exists
  if (chartInstance.value) {
    chartInstance.value.destroy();
  }
  
  const ctx = meanRentChart.value.getContext('2d');
  
  // Sort data by date
  const sortedData = [...meanRentTimeSeries.value].sort((a, b) => new Date(a.date) - new Date(b.date));
  
  chartInstance.value = new Chart(ctx, {
    type: 'line',
    data: {
      labels: sortedData.map(item => new Date(item.date).toLocaleDateString()),
      datasets: [{
        label: 'Mean Rent ($)',
        data: sortedData.map(item => item.mean_rent),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Date'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Mean Rent ($)'
          },
          ticks: {
            callback: function(value) {
              return '$' + value.toFixed(0);
            }
          }
        }
      },
      elements: {
        point: {
          hoverBackgroundColor: '#1d4ed8'
        }
      }
    }
  });
}

async function loadData() {
  try {
    // Load all the data we need
    // For neighborhoods view, we need full listings data with neighborhood field
    const [listings, clusters, heatmap, metrics] = await Promise.all([
      fetchListingsMinimal(), // Use full listings for neighborhood data
      fetchClusters(),
      fetchHeatMap(),
      loadPipelineMetrics()
    ]);
    
    allListings.value = listings;
    clusteredListings.value = clusters;
    heatmapData.value = heatmap;
    
    console.log('Data loaded:', {
      listings: listings.length,
      clusters: clusters.length,
      heatmap: heatmap ? heatmap.length : 0,
      neighborhoods: new Set(listings.map(l => l.neighborhood).filter(n => n)).size
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

  // Remove colored choropleth layer when switching filters (base outlines stay)
  if (currentNeighborhoodLayer.value) {
    exploreMap.value.removeLayer(currentNeighborhoodLayer.value);
    currentNeighborhoodLayer.value = null;
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
  margin-top: 2%;
  width: 100vw;
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center; 
  gap: 60px;
  padding-bottom: 4rem;
}

.header {
  text-align: center;
  padding: 2rem 2rem 2rem;
  background: #061559;
  color: white;
  width: 100%;
}

.header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.header p {
  font-size: 1.1rem;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 2rem;
  align-items: start;
  width: 80%;
}

.explore-section,
.stats-section,
.model-section,
.landlords-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  height: fit-content;
}

.explore-section h2,
.stats-section h2,
.model-section h2,
.landlords-section h2 {
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
  position: relative;
}

.explore-map {
  height: 500px;
}

.map-legend {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 180px;
}

.map-legend h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.75rem;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
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

/* Pipeline Metrics Styles */
.metrics-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.metric-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.metric-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.metric-row {
  display: flex;
  gap: 2rem;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.metric-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
}

/* Landlord List Styles */
.landlord-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.landlord-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 4px solid #ef4444;
}

.landlord-item.underpriced {
  border-left-color: #10b981;
}

.landlord-name {
  font-weight: 500;
  color: #1f2937;
}

.landlord-price {
  font-weight: 700;
  color: #dc2626;
}

.landlord-item.underpriced .landlord-price {
  color: #059669;
}

/* Pricing Split Styles */
.pricing-split {
  display: flex;
  gap: 1rem;
}

.pricing-item {
  flex: 1;
  text-align: center;
  padding: 1rem;
  border-radius: 8px;
}

.pricing-item.overpriced {
  background: #fef2f2;
  border: 2px solid #fecaca;
}

.pricing-item.underpriced {
  background: #f0fdf4;
  border: 2px solid #bbf7d0;
}

.pricing-label {
  display: block;
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.pricing-value {
  font-size: 1.5rem;
  font-weight: 700;
}

.pricing-item.overpriced .pricing-value {
  color: #dc2626;
}

.pricing-item.underpriced .pricing-value {
  color: #16a34a;
}

/* Model Info Styles */
.model-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.model-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
}

.model-metrics {
  display: flex;
  gap: 2rem;
}

.model-metric {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

/* Feature Importance Styles */
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.feature-name {
  min-width: 150px;
  font-size: 0.875rem;
  color: #1f2937;
  font-weight: 500;
}

.feature-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.feature-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.feature-value {
  min-width: 50px;
  text-align: right;
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
}

/* Time Series Chart Styles */
.time-series-container {
  margin-bottom: 1.5rem;
}

.time-series-container h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 1rem;
}

.chart-container {
  position: relative;
  height: 200px;
  margin-bottom: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
}

.time-series-chart {
  width: 100% !important;
  height: 100% !important;
}

.current-value {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f3f4f6;
  border-radius: 6px;
}

/* Moran's I Styles */
.moran-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.moran-description {
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
}

/* Loading and Error States */
.loading-metrics,
.error-metrics {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.error-metrics {
  color: #dc2626;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  font-size: 1.2rem;
  color: #6b7280;
}

@media (max-width: 768px) {
  .metric-row {
    flex-direction: column;
    gap: 1rem;
  }
  
  .pricing-split {
    flex-direction: column;
  }
  
  .model-metrics {
    flex-direction: column;
    gap: 1rem;
  }
  
  .feature-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .feature-name {
    min-width: auto;
  }
  
  .feature-bar {
    width: 100%;
  }
  
  .chart-container {
    height: 150px;
  }
  
  .current-value {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
}
</style>