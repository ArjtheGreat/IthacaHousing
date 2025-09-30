<template>
<div class="popup-container">
    <!-- Header -->
    <div class="popup-header">
        <div class="popup-title-container">
            <h3 class="popup-title">
                {{ listing?.listingaddress }}, 
                <span v-if="listing?.listingcity">{{ listing?.listingcity }},</span> 
                {{ listing?.listingzip }}
            </h3>
        </div>
        <button class="close-btn" @click="closePopup">✖</button>
    </div>

    <div class="popup-image-container">
        <!-- Left Arrow (Previous Image) -->
        <button v-if="listing?.listingphotos && listing?.listingphotos.length > 0" @click="prevImage" class="nav-arrow left-arrow">❮</button>

        <!-- Image Display -->
        <img 
        v-if="extractPhoto(listing?.listingphotos).length > 0" 
        :src="extractPhoto(listing?.listingphotos)[currentImageIndex]?.PhotoUrl || ''" 
        alt="Listing Photo" 
        class="listing-image"
        >
        <!-- Right Arrow (Next Image) -->
        <button v-if="extractPhoto(listing?.listingphotos).length > 1" @click="nextImage" class="nav-arrow right-arrow">❯</button>
    </div>

     <!-- Rental Information -->
    <div class="rent-section">
        <div class="rent-box">
            <strong>Rent:</strong>
            <span>${{ listing?.rentamountadjusted.toFixed(2) }}</span>
        </div>
        <div class="rent-box">
            <strong>Predicted Rent:</strong>
            <span :class="{'text-green': listing?.differenceinfairvalue < 0, 'text-red': listing?.differenceinfairvalue > 0}">
            ${{ listing?.predictedrent.toFixed(2) }}
            </span>
        </div>
        <div
            class="rent-diff"
            :class="{
            'text-red': percentChange < 0,
            'text-green': percentChange > 0
            }"
        >
            Percent Change: {{ percentChange.toFixed(2) }}%
        </div> 
    </div>
    <!-- Main Content (2-Column Layout) -->
    <div class="popup-content grid grid-cols-2 gap-4">
    <!-- Left Column (Transit & Walking Info) -->
        <div class="popup-left">
            <table class="info-table">
                <tr>
                    <td><i class="fa-solid fa-bus text-blue-500"></i></td>
                    <td><span class="stat-label">Transit Score:</span></td>
                    <td>{{ listing?.transit_score ?? "N/A" }}</td>
                </tr>
                <!-- <tr>
                    <td><i class="fa-solid fa-person-walking text-green-500"></i></td>
                    <td>Arts Quad:</td>
                    <td>{{ (listing?.ag_quad_time/60).toFixed(0) ?? "N/A" }} min</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-person-walking text-green-500"></i></td>
                    <td>Ag Quad:</td>
                    <td>{{ (listing?.arts_quad_time/60).toFixed(0) ?? "N/A" }} min</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-person-walking text-green-500"></i></td>
                    <td>Uris Hall:</td>
                    <td>{{ (listing?.uris_hall_time/60).toFixed(0) ?? "N/A" }} min</td>
                </tr> -->
                <tr>
                    <td><i class="fa-solid fa-person-walking text-yellow-500"></i></td>
                    <td>Walk Time:</td>
                    <td>{{ (listing?.walk_time) ?? "N/A" }} min</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-car text-yellow-500"></i></td>
                    <td>Drive Time:</td>
                    <td>{{ (listing?.drive_time) ?? "N/A" }} min</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-bicycle text-yellow-500"></i></td>
                    <td>Bike Time:</td>
                    <td>{{ (listing?.bike_time) ?? "N/A" }} min</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-shield-halved text-yellow-500"></i></td>
                    <td>Luxury Score:</td>
                    <td>{{ (listing?.amenities_score).toFixed(2) ?? "N/A" }}/100</td>
                </tr>
            </table>
        </div>

        <!-- Right Column (Bedrooms, Pets, Amenities) -->
        <div class="popup-right">
            <table class="info-table">
                <tr>
                    <td><i class="fa-solid fa-bed text-indigo-500"></i></td>
                    <td>Bedrooms:</td>
                    <td>{{ listing?.bedrooms }}</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-toilet text-purple-500"></i></td>
                    <td>Bathrooms:</td>
                    <td>{{ listing?.bathrooms }}</td>
                </tr>
                <tr>
                    <td><i class="fa fa-paw text-yellow-600"></i></td>
                    <td>Pets:</td>
                    <td>{{ listing?.pets === "Yes" ? "Allowed" : "Not Allowed" }}</td>
                </tr>
                <tr>
                    <td><i class="fa fa-home text-indigo-600"></i></td>
                    <td>Housing Type:</td>
                    <td>{{ listing?.housingtype ?? "N/A" }}</td>
                </tr>
                <tr>
                    <td><i class="fa fa-home text-indigo-600"></i></td>
                    <td>Rent Type:</td>
                    <td>{{ listing?.renttype ?? "N/A" }}</td>
                </tr>
            </table>
        </div>
    </div>

    <div class="popup-mobile-stats">
        <!-- Location Info -->
        <div class="info-row">
            <i class="fa-solid fa-bus text-blue-500"></i>
            <div class="info-text">
            <div class="label">Transit Score</div>
            <div class="value">{{ listing?.transit_score ?? "N/A" }}</div>
            </div>
        </div>

        <div class="info-row">
            <i class="fa-solid fa-person-walking text-yellow-500"></i>
            <div class="info-text">
            <div class="label">Walk Time</div>
            <div class="value">{{ listing?.walk_time ?? "N/A" }} min</div>
            </div>
        </div>

        <div class="info-row">
            <i class="fa-solid fa-car text-yellow-500"></i>
            <div class="info-text">
            <div class="label">Drive Time</div>
            <div class="value">{{ listing?.drive_time ?? "N/A" }} min</div>
            </div>
        </div>

        <div class="info-row">
            <i class="fa-solid fa-bicycle text-yellow-500"></i>
            <div class="info-text">
            <div class="label">Bike Time</div>
            <div class="value">{{ listing?.bike_time ?? "N/A" }} min</div>
            </div>
        </div>

        <div class="info-row">
            <i class="fa-solid fa-shield-halved text-yellow-500"></i>
            <div class="info-text">
            <div class="label">Luxury Score</div>
            <div class="value">{{ listing?.amenities_score?.toFixed(2) ?? "N/A" }}/100</div>
            </div>
        </div>

        <!-- Housing Info -->
        <div class="info-row">
            <i class="fa-solid fa-bed text-indigo-500"></i>
            <div class="info-text">
            <div class="label">Bedrooms</div>
            <div class="value">{{ listing?.bedrooms }}</div>
            </div>
        </div>

        <div class="info-row">
            <i class="fa-solid fa-toilet text-purple-500"></i>
            <div class="info-text">
            <div class="label">Bathrooms</div>
            <div class="value">{{ listing?.bathrooms }}</div>
            </div>
        </div>

        <div class="info-row">
            <i class="fa fa-paw text-yellow-600"></i>
            <div class="info-text">
            <div class="label">Pets</div>
            <div class="value">{{ listing?.pets === "Yes" ? "Allowed" : "Not Allowed" }}</div>
            </div>
        </div>

        <div class="info-row">
            <i class="fa fa-home text-indigo-600"></i>
            <div class="info-text">
            <div class="label">Housing Type</div>
            <div class="value">{{ listing?.housingtype ?? "N/A" }}</div>
            </div>
        </div>

        <div class="info-row">
            <i class="fa fa-home text-indigo-600"></i>
            <div class="info-text">
            <div class="label">Rent Type</div>
            <div class="value">{{ listing?.renttype ?? "N/A" }}</div>
            </div>
        </div>
        </div>


    <!-- Description -->
    <div class="popup-description">
        {{ listing?.shortdescription }}
    </div>

    <!-- Amenities Section -->
    <div class="popup-amenities">
        <strong>Amenities: </strong>
        <span class="amenities-list">
            {{ formatAmenities(listing?.amenities) }}
        </span>
    </div>

    <div class="popup-similar-listings">
        <span class="similar-listing-title"><strong>Similar Listings: </strong></span>
        <div class="similar-listings-list">
            <div 
            v-for="(listing, index) in similarListings" 
            :key="index" 
            class="similar-listing-item"
            >
            <div class="image-container">
                <img 
                :src="extractPhoto(listing?.listingphotos)[0]?.PhotoUrl || ''" 
                alt="Listing Photo" 
                class="listing-photo"
                />
            </div>
            <p class="listing-address">{{ listing?.listingaddress }}</p>
            </div>
        </div>
    </div>

</div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, computed, onMounted, watch } from 'vue';
import { fetchListing }  from "@/services/fetch"; 
import type { Listing } from "@/services/interface"

const props = defineProps({
    listing: Object,
});

const emit = defineEmits(['close', 'zoom']);

const closePopup = () => {
    emit('close');
};  

const currentImageIndex = ref(0); // Holds the current index of the images in the gallery
const totalImages = computed(() => extractPhoto(props.listing?.listingphotos).length); // Holds the number of images in the gallery
const similarListings = ref<Listing[]>([]);

/**
 * Percent Change
 */
const percentChange = computed(() => {
  if (!props.listing?.predictedrent || !props.listing?.rentamountadjusted) return 0;
  return ((props.listing.predictedrent - props.listing.rentamountadjusted) / props.listing.rentamountadjusted) * 100;
});


/**
 * Formats amenities data for display.
 * @param {any} amenitiesData - JSON object, array, or string of amenities.
 * @returns {string} - Formatted amenities string for display.
 */
const formatAmenities = (amenitiesData: any): string => {
  if (!amenitiesData) return "None Listed";
  
  try {
    let amenities;
    
    if (typeof amenitiesData === 'object') {
      amenities = Array.isArray(amenitiesData) ? amenitiesData : [];
    } else {
      const amenitiesStr = String(amenitiesData);
      if (amenitiesStr.startsWith('[') && amenitiesStr.endsWith(']')) {
        amenities = JSON.parse(amenitiesStr);
      } else {
        amenities = [amenitiesStr];
      }
    }
    
    return Array.isArray(amenities) ? amenities.join(', ') : "None Listed";
  } catch (error) {
    console.warn('Error formatting amenities:', error);
    return "None Listed";
  }
};

/**
 * Extracts and Processes JSON data to get photos.
 * @param {any} listingPhotosData - JSON object or string of listing photos.
 * @returns {Array} - Parsed array of photo objects, or an empty array if invalid.
 */
 const extractPhoto = (listingPhotosData: any): Array<any> => {
  if (!listingPhotosData) return [];

  try {
    // If it's already a parsed object/array, return it
    if (typeof listingPhotosData === 'object') {
      return Array.isArray(listingPhotosData) ? listingPhotosData : [];
    }

    // If it's a string, clean and parse it
    const listingPhotosStr = String(listingPhotosData);
    
    // Check if it's the "[object Object]" string (invalid)
    if (listingPhotosStr === '[object Object]') {
      console.warn('Received invalid object string, returning empty array');
      return [];
    }
    
    const cleanedStr = listingPhotosStr
      .replace(/\\/g, '\\\\')        
      .replace(/'/g, '"')            
      .replace(/\bTrue\b/g, 'true')  
      .replace(/\bFalse\b/g, 'false')
      .replace(/\bNone\b/g, 'null') 
      .replace(/\\n/g, '')          
      .replace(/\\t/g, '')         
      .trim();

    const parsed = JSON.parse(cleanedStr);

    return Array.isArray(parsed) ? parsed : [];
  } catch (error: any) {
    console.error("JSON Parsing Error:", error.message, "Data:", listingPhotosData);
    return [];
  }
};


/**
 * Goes to Next Image in Carosel
 */
const nextImage = () => {
  if (currentImageIndex.value < totalImages.value - 1) {
    currentImageIndex.value++;
  } else {
    currentImageIndex.value = 0; 
  }
};

/**
 * Goes to Previous Image in Carosel
 */
const prevImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--;
  } else {
    currentImageIndex.value = totalImages.value - 1;
  }
};

/**
 * Parses PostgreSQL Array of Nearest Neighbors
 * @param pgArrayString 
 */
function parsePostgresArray(pgArrayString: String) {
  if (!pgArrayString || pgArrayString.length < 2) {
    return [];
  }

  return pgArrayString
    .slice(1, -1)
    .split(',')
    .map(num => Number(num.trim()));
}

/**
 * Fetch Similar Listings
 */
 async function fetchSimilarListings() {
    const rawIds = props.listing?.nearest_neighbor_listingids;
    
    let ids: number[] = [];
    
    if (rawIds) {
        try {
            // If it's already an array, use it directly
            if (Array.isArray(rawIds)) {
                ids = rawIds.map(id => Number(id)).filter(id => !isNaN(id));
            } 
            // If it's a string, try to parse it as JSON first
            else if (typeof rawIds === 'string') {
                try {
                    const parsed = JSON.parse(rawIds);
                    if (Array.isArray(parsed)) {
                        ids = parsed.map(id => Number(id)).filter(id => !isNaN(id));
                    } else {
                        // Fallback to old string processing
                        ids = rawIds
                            .replace(/[{}]/g, '')     
                            .split(',')                
                            .map((id: string) => Number(id))
                            .filter(id => !isNaN(id));
                    }
                } catch {
                    // If JSON parsing fails, use old string processing
                    ids = rawIds
                        .replace(/[{}]/g, '')     
                        .split(',')                
                        .map((id: string) => Number(id))
                        .filter(id => !isNaN(id));
                }
            }
        } catch (error) {
            console.warn('Error processing nearest neighbor IDs:', error);
            ids = [];
        }
    }

    const fetched = await Promise.all(
        ids.map((id: Number) => fetchListing(id))
    );

    similarListings.value = fetched.filter(l => l !== null) as Listing[];
}
/**
 * 
 */
onMounted(async () => {
    await fetchSimilarListings()
});

watch<Listing | undefined>(
  () => props.listing as Listing,
  async (newListing) => {
    if (newListing) {
      await fetchSimilarListings();
    }
  }
);




</script>
  

<style scoped>
/* 📦 POPUP CONTAINER */
.popup-container {
    background: #ffffff;
    padding: 20px;
    width: 640px;
    height: 100vh;
    box-shadow: 0 5px 14px rgba(0, 0, 0, 0.12);
    border: 1px solid #ddd;
    z-index: 500;
    overflow: scroll;
}

/* 🔝 HEADER */
.popup-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    /* border-bottom: 2px solid #e5e7eb; */
    padding: 16px 0px;
    border-radius: 8px 8px 0 0;
}

/* Centered Title */
.popup-title-container {
    flex-grow: 1;
}

.popup-title, .popup-title span {
    font-size: 1.3rem;
    color: #222;
    margin: 0;
    text-align: left;
    font-weight: bold;
}

/* Close Button */
.close-btn {
    background: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
    color: #888;
    transition: color 0.2s;
}

.close-btn:hover {
    color: #555;
}

/* Image Section */
.popup-image-container {
    text-align: center;
    margin-top: 10px;
    margin-bottom: 10px;
}

.listing-image {
    width: 100%;
    max-height: 250px;
    object-fit: cover;
    border: 2px solid #e5e7eb;
}
/* SIDEBAR POPUP */
.popup-sidebar {
  position: fixed;
  top: 60px;
  right: 30px;
  width: auto;
  max-height: 90vh;
  overflow-y: auto;
  background: white;
  box-shadow: -3px 0 15px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  padding: 20px;
  border-left: 1px solid #ddd;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.popup-sidebar {
  display: flex;
}

.close-sidebar {
  background: none;
  border: none;
  font-size: 1.3rem;
  cursor: pointer;
  color: #888;
  align-self: flex-end;
  transition: color 0.2s ease-in-out;
}

.close-sidebar:hover {
  color: black;
}

.popup-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
  font-size: 1rem;
  color: #444;
}

.popup-mobile-stats {
    display: none;
}

/* Style for both tables */
.info-table {
  width: 100%;
  border-collapse: collapse;
}

.info-table td {
  padding: 6px 10px;
  vertical-align: middle;
}

/* Icon column */
.info-table td:first-child {
  width: 24px;
  text-align: center;
}

/* Label column */
.info-table td:nth-child(2) {
  white-space: nowrap;
  font-weight: 500;
}

/* Value column */
.info-table td:last-child {
  text-align: left;
}

/* 💰 RENT INFO BOX */
.rent-section {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    background: none;
    border: 1px solid none;
    text-align: center;
    font-family: "Inter", sans-serif;
    align-items: center;
    /* border-top: 2px solid #e5e7eb; */
    border-bottom: 2px solid #e5e7eb;
    margin-bottom: 16px;
    padding-top: 16px;
    padding-bottom: 16px;
}

.rent-box {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: none;
    padding: 8px;
    width: 100%;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
}

.rent-box strong {
    color: #374151;
}

.rent-box span {
    font-size: 1rem;
    font-weight: bold;
    margin-top: 5px;
    color: #111827;
}

.text-green {
    color: #16a34a;
}

.text-red {
    color: #dc2626;
}

.rent-diff {
    grid-column: span 2;
    font-size: 1rem;
    font-weight: bold;
    color: #374151;
    background: none;
    padding: 10px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
}

.rent-diff.text-red {
    color: #dc2626;
}

.rent-diff.text-green {
    color: #16a34a;
}


/* 🌡️ COLOR FOR RENT DIFFERENCE */
.text-red {
    color: #dc2626;
}

.text-green {
    color: #16a34a;
}

/* 📜 FULL-WIDTH SECTIONS */
.full-width {
    grid-column: span 2;
    width: 100%;
}

/* 📝 DESCRIPTION */
.popup-description {
    font-size: 1rem;
    color: #555;
    border-top: 2px solid #e5e7eb;
    padding-top: 16px;
    margin-top: 16px;
}


/* 📌 AMENITIES SECTION */
.popup-amenities {
    /* border-top: 2px solid #e5e7eb; */
    padding-top: 16px;
    padding-bottom: 8px;
    margin-top: 16px;
    font-size: 1rem;
    color: #444;
}

/* 📌 SIMILAR LISTINGS SECTION */
.popup-similar-listings {
    width: 100%;
    border-top: 2px solid #e5e7eb;
    padding-top: 16px;
    padding-bottom: 16px;
    font-size: 1rem;
    color: #444;
}

.similar-listing-title {
    padding: 0 0;
}

.similar-listings-list {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
    width: 100%;
}

.similar-listing-item {
    flex: 1;
    max-width: calc(100% / 3 - 0.67rem); 
    display: flex;
    flex-direction: column;
    align-items: center;
}

.image-container {
    width: 100%;
    overflow: hidden;
}

.listing-photo {
    filter: blur(0px);
    width: 100%;
    height: auto;
    transition: filter 0.3s ease;
    object-fit: cover;
    border-radius: 8px;
}

.listing-photo:hover {
  filter: blur(0px);
}

.listing-address {
  margin-top: 0.5rem;
  font-size: 1rem;
  text-align: center;
  color: #333;
}


/* 🔍 ZOOM BUTTON */
.zoom-btn {
    width: 40px; /* Set fixed width */
    height: 40px; /* Set fixed height */
    background-color: #f5f5f5; /* Light background */
    border: none;
    border-radius: 50%; /* Make it circular */
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.2s ease-in-out;
}

/* Ensure the icon is centered */
.zoom-btn svg {
    width: 20px;
    height: 20px;
    color: #333;
}

/* Hover effect */
.zoom-btn:hover {
    background-color: #ddd;
}


.leaflet-popup-content-wrapper {
    background: none;
    width: 100%;
    box-shadow: none;
}

.leaflet-popup-tip {
  background-color: blue;
}

.info-table {
    width: 100%;
    border-collapse: collapse;
}

.info-table td {
    padding: 4px 8px;
    vertical-align: middle;
    color: #444;
}

.info-table i {
    font-size: 1.2rem;
}

.popup-image-container {
  position: relative;
  width: 100%;
  max-width: 600px; /* Adjust based on design */
  margin: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 12px;
}

.listing-image {
  width: 100%;
  height: auto;
  object-fit: cover;
  border-radius: 12px;
  transition: opacity 0.3s ease-in-out;
}

/* 🔹 Modern Navigation Arrows */
.nav-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.4);
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.3s, transform 0.2s;
}

.nav-arrow:hover {
  background: rgba(0, 0, 0, 0.7);
  transform: scale(1.1);
}

.left-arrow {
  left: 10px;
}

.right-arrow {
  right: 10px;
}

/* 🔹 Sleek Arrow Icons */
.arrow-icon {
  font-size: 22px;
  font-weight: bold;
  user-select: none;
}

@media (max-width: 768px) {
    .popup-container {
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 95vw;
        max-height: 90vh;
        background: white;
        z-index: 10000;
        border-radius: 16px 16px 0 0;
        box-shadow: 0 -6px 18px rgba(0, 0, 0, 0.25);
        padding: 16px;
        overflow-y: auto;
        animation: slideUp 0.3s ease-in-out;
    }

    .popup-header {
        /* flex-direction: column; */
        position: sticky;
        top: 0;
        z-index: 50;
        background: white;
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #e5e7eb;
        align-items: flex-start;
        gap: 8px;
    }

    .popup-title {
        font-size: 0.9rem;
        font-weight: bold;
        text-align: left;
        word-break: break-word;
    }

    .popup-image-container {
        max-height: 180px;
        border-radius: 12px;
        margin-bottom: 12px;
    }

    .listing-image {
        max-height: 180px;
        object-fit: cover;
        border-radius: 12px;
    }

    .nav-arrow {
        width: 28px;
        height: 28px;
        font-size: 16px;
    }

    .popup-content {
        display: none;
    }

    .popup-mobile-stats {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 12px 0;
    }

    .info-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 0;
        border-bottom: 1px solid #eee;
        color: #444;
    }

    .info-text {
        display: flex;
        flex-direction: column;
        justify-content: center;
        flex-grow: 1;
    }

    .label {
        font-size: 0.95rem;
        font-weight: 500;
        color: #333;
    }

    .value {
        font-size: 0.9rem;
        color: #666;
    }

    .rent-section {
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-bottom: 12px;
    }

    .rent-box {
        font-size: 0.95rem;
        padding: 8px;
        text-align: center;
    }

    .rent-box span {
        font-size: 1.1rem;
        font-weight: 600;
    }

    .rent-diff {
        font-size: 0.95rem;
        text-align: center;
        padding: 10px;
    }

    .info-table {
        font-size: 0.9rem;
    }

    .info-table td {
        padding: 4px 6px;
    }

    .popup-description,
        .popup-amenities {
        font-size: 0.95rem;
    }

    .popup-similar-listings {
        padding-top: 12px;
        font-size: 0.95rem;
    }

    .similar-listings-list {
        flex-direction: column;
        gap: 12px;
    }

    .similar-listing-item {
        max-width: 100%;
    }

    .similar-listing-item img {
        border-radius: 8px;
    }

    .listing-address {
        font-size: 0.95rem;
    }
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


</style>