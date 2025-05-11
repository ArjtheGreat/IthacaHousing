<template>
  <NavBar />
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p class="loading-text">{{ loadingMessage }}</p>
    </div>
    <div class="filter-container">
        <div class="tab-header">
            <button
            class="tab-button"
            :class="{ active: activeTab === 'Land Use' }"
            @click="activeTab = 'Land Use'"
            >
            Land Use
            </button>
            <button
            class="tab-button"
            :class="{ active: activeTab === 'Places of Interest' }"
            @click="activeTab = 'Places of Interest'"
            >
            Places of Interest
            </button>
        </div>
        
            <div class="tab-content">
                <!-- Explore Ithaca Tab -->
                <RadioGroup v-model="activeFilter" v-if="activeTab === 'Land Use'">
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
                <RadioGroup v-model="activeFilterExpanded" v-if="activeTab === 'Places of Interest'">
                    <RadioGroupLabel class="filter-title"></RadioGroupLabel>
                    <div class="radio-options">
                        <RadioGroupOption 
                            as="template" 
                            v-for="option in filterOptionsExpanded" 
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
    </div>
    <button
    class="drawer-toggle"
    @click="isDrawerOpen = !isDrawerOpen"
  >
    🧽 Filters
  </button>
  <!-- Drawer Container -->
  <transition name="slide-up">
    <div
      class="filter-drawer"
      v-if="isDrawerOpen"
    >
      <div class="drawer-header">
        <span class="drawer-title">Filters</span>
        <button class="close-drawer" @click="isDrawerOpen = false">✕</button>
      </div>

      <div class="tab-header">
        <button
          class="tab-button"
          :class="{ active: activeTab === 'Land Use' }"
          @click="activeTab = 'Land Use'"
        >
          Land Use
        </button>
        <button
          class="tab-button"
          :class="{ active: activeTab === 'Places of Interest' }"
          @click="activeTab = 'Places of Interest'"
        >
          Places of Interest
        </button>
      </div>

      <div class="tab-content">
        <RadioGroup v-model="activeFilter" v-if="activeTab === 'Land Use'">
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
                    <circle cx="12" cy="12" r="12" fill="white" fill-opacity="0.2" />
                    <path
                      d="M7 13l3 3 7-7"
                      stroke="white"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </span>
              </button>
            </RadioGroupOption>
          </div>
        </RadioGroup>

        <RadioGroup
          v-model="activeFilterExpanded"
          v-if="activeTab === 'Places of Interest'"
        >
          <div class="radio-options">
            <RadioGroupOption
              as="template"
              v-for="option in filterOptionsExpanded"
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
                    <circle cx="12" cy="12" r="12" fill="white" fill-opacity="0.2" />
                    <path
                      d="M7 13l3 3 7-7"
                      stroke="white"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </span>
              </button>
            </RadioGroupOption>
          </div>
        </RadioGroup>
      </div>
    </div>
  </transition>
  <div id="map" style="height: 100vh; width: 100%">
      <div class="legend">
          <h4>Zoning Legend</h4>
          <ul>
          <li><span style="background: #1f77b4"></span> Residential</li>
          <li><span style="background: #ff7f0e"></span> Business</li>
          <li><span style="background: #2ca02c"></span> Industrial</li>
          <li><span style="background: #9467bd"></span> Government</li>
          <li><span style="background: #d62728"></span> Mixed Use</li>
          <li><span style="background: #8c564b"></span> Southwest</li>
          <li><span style="background: #7f7f7f"></span> Not Zoned</li>
          </ul>
      </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import L from 'leaflet';
import { fetchVacantLots, fetchLots } from '@/services/fetch';
import NavBar from "@/components/NavBar.vue";
import { RadioGroup, RadioGroupLabel, RadioGroupOption } from "@headlessui/vue";
import Papa from 'papaparse';

const map = ref(null); // Holds map
const activeTab = ref("Land Use")
const activeFilter = ref(""); // Default tab
const activeFilterExpanded = ref(""); // Default tab
const markerGroup = L.layerGroup();

const layerGroup = ref(null); // Holds Layers 
const isLoading = ref(true); // Add loading state
const loadingMessage = ref("Loading zoning data...");
const isDrawerOpen = ref(true);


/**
 * Define Colors for Zoning Map
 */
const zoningColorMap = {
    Residential: '#1f77b4',
    Business: '#ff7f0e',
    Industrial: '#2ca02c',
    Government: '#9467bd',
    'Mixed Use': '#d62728',
    Southwest: '#8c564b',
    'Not Zoned': '#7f7f7f'
};

/**
 * Lifecycle Hook for calling Zoning Data
 */
onMounted(async () => {
    
    map.value = L.map('map').setView([42.443, -76.501], 13);

    L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
        attribution: '&copy; OpenStreetMap contributors',
        subdomains:['mt0','mt1','mt2','mt3']
    }).addTo(map.value);
    plotVacantLots()
    activeFilter.value = "vacant"
});


/**
 * Define Options For Filter
 */
 const filterOptions = [
    { value: "vacant", label: "Underdeveloped Lots", action: plotVacantLots },
    { value: "all", label: "All Parcels", action: plotLots },
    { value: "flood", label: "Flood Zones", action: plotFloodMap },
];

/**
 * Define Options For Filter
 */
 const filterOptionsExpanded = [
    { value: "food", label: "Food and Beverage", action: plotFoodDrinks },
    { value: "attractions", label: "Attractions", action: plotAttractions },
    { value: "groceries", label: "Groceries", action: plotGroceries },
    { value: "shopping", label: "Shopping", action: plotShopping },
];


/**
 * Loads CSV
 * @param filePath 
 */
const loadCSV = async (filePath) => {
  const response = await fetch(filePath);
  const text = await response.text();

  return new Promise((resolve) => {
    Papa.parse(text, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => resolve(results.data)
    });
  });
};


/**
 * Plots Vacant Lots
 */
async function plotVacantLots() {
    if(activeFilter.value == "vacant") {
        activeFilter.value = ""
        layerGroup.value.clearLayers();
        return;
    }
    isLoading.value = true;
    if (layerGroup.value) {
        layerGroup.value.clearLayers();
    } else {
        layerGroup.value = L.layerGroup().addTo(map.value);
    }
    
    const data = await fetchVacantLots();
    data.forEach(feature => {
        if (feature.geometry && feature.geometry.coordinates) {
            const coords = feature.geometry.coordinates[0].map((pt) => [pt[1], pt[0]]);
            const zoning = feature.ZoningCategory || 'Not Zoned';
            const fillColor = zoningColorMap[zoning] || '#7f7f7f';

            const polygon = L.polygon(coords, {
                color: 'black',
                weight: 1,
                fillColor: fillColor,
                fillOpacity: 0.5
            })

            polygon.bindPopup(
                `<strong>ID:</strong> ${feature.OBJECTID}<br>
                <strong>Zoning:</strong> ${feature.ZoningCategory}<br>
                <strong>Value:</strong> $${Math.round(feature.ASMT).toLocaleString()} <br> 
                <strong>Value Per Acre:</strong> $${Math.round(feature.ValuePerAcre).toLocaleString()} <br>                
                <strong>Land-Value Ratio:</strong> ${(feature.RedevelopmentIndex).toFixed(3)}`
            );
            layerGroup.value.addLayer(polygon);
        }
    });

    isLoading.value = false;
}

/**
 * Plots All Ithaca Lots
 */
async function plotLots() {
    if(activeFilter.value == "all") {
        activeFilter.value = ""
        layerGroup.value.clearLayers();
        return;
    }
    isLoading.value = true;
    if (layerGroup.value) {
        layerGroup.value.clearLayers();
    } else {
        layerGroup.value = L.layerGroup().addTo(map.value);
    }

    const data = await fetchLots();
    data.forEach(feature => {
        if (feature.geometry && feature.geometry.coordinates) {
            const coords = feature.geometry.coordinates[0].map((pt) => [pt[1], pt[0]]);
            const zoning = feature.ZoningCategory || 'Not Zoned';
            const fillColor = zoningColorMap[zoning] || '#7f7f7f';

            const polygon = L.polygon(coords, {
                color: 'black',
                weight: 1,
                fillColor: fillColor,
                fillOpacity: 0.5
            })
            
            polygon.bindPopup(
                `<strong>ID:</strong> ${feature.OBJECTID}<br>
                <strong>Zoning:</strong> ${feature.ZoningCategory}<br>
                <strong>Value Per Acre:</strong> $${Math.round(feature.ValuePerAcre).toLocaleString()}`
            );
            layerGroup.value.addLayer(polygon);
        }
    });

    isLoading.value = false;
}

/**
 * Loading Flood Map
 */
async function plotFloodMap() {
    if(activeFilter.value == "flood") {
        activeFilter.value = ""
        layerGroup.value?.clearLayers();
        return;
    }
    isLoading.value = true;
    try {
        const response = await fetch("/maps/Flood_Zones.geojson");
        const geojson = await response.json();

        const floodLayer = L.geoJSON(geojson, {
        style: {
            color: '#0077b6',
            fillColor: '#00b4d8',
            fillOpacity: 0.3,
            weight: 1
        },
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`Flood Zone: ${feature.properties?.ZONE || "Unknown"}`);
        }
        });
        layerGroup.value?.addLayer(floodLayer)
        floodLayer.addTo(map.value);
    } catch (error) {
        console.error("Failed to load flood zones:", error);
    }
    isLoading.value = false;
}

/**
 * Attractions
 */
 async function plotAttractions() {
    if (activeFilterExpanded.value === "attractions") {
        activeFilterExpanded.value = "";
        markerGroup.clearLayers();
        return;
    }

    const data = await loadCSV("/maps/Attractions.csv");
    markerGroup.clearLayers();

    data.forEach((row) => {
        const lat = parseFloat(row["location/lat"]);
        const lng = parseFloat(row["location/lng"]);
        if (!isNaN(lat) && !isNaN(lng)) {
            // Build address
            const address = `${row.street}, ${row.city}, ${row.state}`;
            // Build hours table
            let hours = "";
            for (let i = 0; i < 7; i++) {
                const day = row[`openingHours/${i}/day`];
                const time = row[`openingHours/${i}/hours`];
                if (day && time) {
                    hours += `<tr><td>${day}</td><td>${time}</td></tr>`;
                }
            }

            const popupContent = `
                <div class="popup-content">
                    <h3 class="popup-title">${row.title}</h3>
                    <p class="popup-category">${row.categoryName || "Attraction"}</p>
                    <p class="popup-address">${address}</p>
                    <table class="popup-hours">${hours}</table>
                    <p class="popup-rating">⭐ ${row.totalScore || "N/A"} (${row.reviewsCount || 0} reviews)</p>
                    ${row.description && row.description.length < 200 ? `<p class="popup-description">${row.description}</p>` : ""}
                    <a class="popup-link" href="${row.url}" target="_blank">More Info →</a>
                </div>
            `;

            const marker = L.circleMarker([lat, lng], {
                radius: 6,
                color: "#f72585",
                fillColor: "#f72585",
                fillOpacity: 0.8
            }).bindPopup(popupContent);

            markerGroup.addLayer(marker);
        }
    });

    markerGroup.addTo(map.value);
}


/**
 * Food & Drinks
 */
 async function plotFoodDrinks() {
    if (activeFilterExpanded.value === "food") {
        activeFilterExpanded.value = "";
        markerGroup.clearLayers();
        return;
    }

    const data = await loadCSV("/maps/Food_Drinks.csv");
    markerGroup.clearLayers();

    data.forEach((row) => {
        const lat = parseFloat(row["location/lat"]);
        const lng = parseFloat(row["location/lng"]);
        if (!isNaN(lat) && !isNaN(lng)) {
            const address = `${row.street}, ${row.city}, ${row.state}`;

            const popupContent = `
                <div class="popup-content">
                    <h3 class="popup-title">${row.title}</h3>
                    <p class="popup-category">${row.categoryName || "Food & Beverage"}</p>
                    <p class="popup-address">${address}</p>
                    <p class="popup-rating">⭐ ${row.totalScore || "N/A"} (${row.reviewsCount || 0} reviews)</p>
                    ${row.description && row.description.length < 200 ? `<p class="popup-description">${row.description}</p>` : ""}
                    <a class="popup-link" href="${row.url}" target="_blank">More Info →</a>
                </div>
            `;

            const marker = L.circleMarker([lat, lng], {
                radius: 6,
                color: "#ffb703",
                fillColor: "#ffb703",
                fillOpacity: 0.8
            }).bindPopup(popupContent);

            markerGroup.addLayer(marker);
        }
    });

    markerGroup.addTo(map.value);
}
/**
 * Groceries
 */
 async function plotGroceries() {
    if (activeFilterExpanded.value === "groceries") {
        activeFilterExpanded.value = "";
        markerGroup.clearLayers();
        return;
    }

    const data = await loadCSV("/maps/Groceries_ConvinienceStores.csv");
    markerGroup.clearLayers();

    data.forEach((row) => {
        const lat = parseFloat(row["location/lat"]);
        const lng = parseFloat(row["location/lng"]);
        if (!isNaN(lat) && !isNaN(lng)) {
            const address = `${row.street}, ${row.city}, ${row.state}`;

            const popupContent = `
                <div class="popup-content">
                    <h3 class="popup-title">${row.title}</h3>
                    <p class="popup-category">${row.categoryName || "Grocery / Convenience"}</p>
                    <p class="popup-address">${address}</p>
                    <p class="popup-rating">⭐ ${row.totalScore || "N/A"} (${row.reviewsCount || 0} reviews)</p>
                    ${row.description && row.description.length < 200 ? `<p class="popup-description">${row.description}</p>` : ""}
                    <a class="popup-link" href="${row.url}" target="_blank">More Info →</a>
                </div>
            `;

            const marker = L.circleMarker([lat, lng], {
                radius: 6,
                color: "#2a9d8f",
                fillColor: "#2a9d8f",
                fillOpacity: 0.8
            }).bindPopup(popupContent);

            markerGroup.addLayer(marker);
        }
    });

    markerGroup.addTo(map.value);
}


/**
 * Shopping
 */
 async function plotShopping() {
    if (activeFilterExpanded.value === "shopping") {
        activeFilterExpanded.value = "";
        markerGroup.clearLayers();
        return;
    }

    const data = await loadCSV("/maps/Shopping.csv");
    markerGroup.clearLayers();

    data.forEach((row) => {
        const lat = parseFloat(row["location/lat"]);
        const lng = parseFloat(row["location/lng"]);
        if (!isNaN(lat) && !isNaN(lng)) {
            const address = `${row.street}, ${row.city}, ${row.state}`;

            const popupContent = `
                <div class="popup-content">
                    <h3 class="popup-title">${row.title}</h3>
                    <p class="popup-category">${row.categoryName || "Shopping Center"}</p>
                    <p class="popup-address">${address}</p>
                    <p class="popup-rating">⭐ ${row.totalScore || "N/A"} (${row.reviewsCount || 0} reviews)</p>
                    ${row.description && row.description.length < 200 ? `<p class="popup-description">${row.description}</p>` : ""}
                    <a class="popup-link" href="${row.url}" target="_blank">More Info →</a>
                </div>
            `;

            const marker = L.circleMarker([lat, lng], {
                radius: 6,
                color: "#219ebc",
                fillColor: "#219ebc",
                fillOpacity: 0.8
            }).bindPopup(popupContent);

            markerGroup.addLayer(marker);
        }
    });

    markerGroup.addTo(map.value);
}

</script>

<style scoped>
#map {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
}

/* FILTER BUTTON */
.filter-container {
  position: absolute;
  top: 100px;
  left: 20px;
  z-index: 1000;
  width: 300px;
  background: rgba(21, 19, 102, 0.2); 
  backdrop-filter: blur(8px); 
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 20px;
  width: 320px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  text-align: center;
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
  margin-bottom: 12px;
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

.filter-drawer, .drawer-toggle {
  display: none;
}

.checkmark .icon {
  width: 16px;
  height: 16px;
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

/* FILTER BUTTON */
.filter-container {
  position: absolute;
  top: 100px;
  left: 20px;
  z-index: 1000;
  width: 300px;
  background: rgba(21, 19, 102, 0.2); 
  backdrop-filter: blur(8px); 
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 20px;
  width: 320px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  text-align: center;
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
  margin-bottom: 12px;
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

.popup-content {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  color: #1f2937;
  max-width: 280px;
  background: #fff;
  padding: 16px 18px;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
  line-height: 1.6;
  border: 1px solid #e5e7eb;
}

.popup-title {
  font-weight: 700;
  font-size: 17px;
  margin-bottom: 6px;
  color: #111827;
}

.popup-category {
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.popup-address {
  font-size: 13.5px;
  color: #374151;
  margin-bottom: 8px;
}

.popup-hours {
  width: 100%;
  font-size: 13px;
  border-collapse: collapse;
  margin-bottom: 8px;
  color: #4b5563;
}

.popup-hours td {
  padding: 4px 6px;
  vertical-align: top;
}

.popup-rating {
  font-size: 13px;
  color: #f59e0b;
  font-weight: 600;
  margin-bottom: 8px;
}

.popup-description {
  font-size: 13px;
  color: #374151;
  margin-bottom: 10px;
}

.popup-link {
  display: inline-block;
  font-size: 13px;
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.popup-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
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

@media (max-width: 768px) {
  .filter-container {
    display: none;
  }
  .drawer-toggle {
    display: block;
    position: absolute;
    top: 90px;
    left: 16px;
    z-index: 1002;
    background: #1e3a8a;
    color: white;
    padding: 10px 18px;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .filter-drawer {
    display: block;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #fff;
    z-index: 1001;
    padding: 20px;
    border-radius: 16px 16px 0 0;
    box-shadow: 0 -8px 20px rgba(0, 0, 0, 0.2);
    max-height: 85vh;
    overflow-y: auto;
    animation: slideUp 0.4s ease-in-out;
  }

  .drawer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .drawer-title {
    font-size: 1.25rem;
    font-weight: bold;
    color: #1e3a8a;
  }

  .close-drawer {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: #666;
    cursor: pointer;
  }

  .slide-up-enter-active,
  .slide-up-leave-active {
    transition: transform 0.3s ease, opacity 0.3s ease;
  }

  .slide-up-enter-from,
  .slide-up-leave-to {
    transform: translateY(100%);
    opacity: 0;
  }
}
</style>
  