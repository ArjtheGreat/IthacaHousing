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
        <div class="rent-main-card">
            <!-- Header -->
            <div class="rent-card-header">
                <h4 class="rent-comparison-title">
                    Fair Rent Comparison
                    <div class="tooltip-container">
                        <span class="tooltip-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-info-icon lucide-info">
                                <circle cx="12" cy="12" r="10"/>
                                <path d="M12 16v-4"/>
                                <path d="M12 8h.01"/>
                            </svg>
                        </span>
                        <div class="tooltip-content">
                            <div class="tooltip-title">How Rent Comparison Works</div>
                            <div class="tooltip-text">
                                <strong>Actual Rent</strong> is what the landlord is asking for.<br><br>
                                <strong>Predicted Rent</strong> is what our proprietary machine learning model considers fair based on the listing's attributes (location, amenities, size, etc.).<br><br>
                                <strong>If predicted rent > actual rent:</strong> The listing is <span class="tooltip-green">underpriced</span> because you are paying less than what the model considers fair - AKA, you're getting a good deal!<br><br>
                                <strong>If predicted < actual:</strong> The listing is <span class="tooltip-red">overpriced</span> because you are paying less than what the model considers fair - AKA, you might be paying too much.
                            </div>
                        </div>
                    </div>
                </h4>
            </div>
            
            <!-- Main Rent Display -->
            <div class="rent-comparison-grid">
                <!-- Actual Rent Column -->
                <div class="rent-column actual-rent">
                    <div class="rent-column-header">
                        <span class="column-label">Actual Rent</span>
                    </div>
                    <div class="rent-total-section">
                        <div class="rent-amount-large">${{ listing?.rent_per_person?.toFixed(2) || 'N/A' }}</div>
                        <div class="rent-label-small">per person</div>
                    </div>
                    <div class="rent-per-person-section">
                        <div class="per-person-amount">${{ listing?.total_rent_amount ? listing.total_rent_amount.toFixed(2) : 'N/A' }}</div>
                        <div class="per-person-label">Total Rent (<span class="people-count">{{ listing?.num_people || 'N/A' }} {{ (listing?.num_people === 1) ? 'person' : 'people' }} </span>)</div>
                    </div>
                </div>

                <!-- Predicted Rent Column -->
                <div class="rent-column predicted-rent">
                    <div class="rent-column-header">
                        <span class="column-label">Fair Rent Estimation</span>
                    </div>
                    <div class="rent-total-section">
                        <div class="rent-amount-large predicted-amount">${{ listing?.predictedrent ? listing.predictedrent.toFixed(2) : 'N/A' }}</div>
                        <div class="rent-label-small">per person</div>
                    </div>
                    <div class="prediction-difference">
                        <div class="difference-badge" :class="{
                            'badge-overpriced': percentChange < 0,
                            'badge-underpriced': percentChange > 0,
                            'badge-fair': percentChange === 0
                        }">
                            <span class="difference-arrow"></span>
                            <span class="difference-percent">{{ Math.abs(percentChange).toFixed(1) }}%</span>
                            <span class="difference-label">{{ percentChange > 0 ? 'Underpriced' : (percentChange < 0 ? 'Overpriced' : 'Fair Price') }}</span>
                        </div>
                    </div>
                </div>
            </div>
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
                    <td>{{ listing?.ag_quad_time ? (listing.ag_quad_time/60).toFixed(0) : "N/A" }} min</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-person-walking text-green-500"></i></td>
                    <td>Ag Quad:</td>
                    <td>{{ listing?.arts_quad_time ? (listing.arts_quad_time/60).toFixed(0) : "N/A" }} min</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-person-walking text-green-500"></i></td>
                    <td>Uris Hall:</td>
                    <td>{{ listing?.uris_hall_time ? (listing.uris_hall_time/60).toFixed(0) : "N/A" }} min</td>
                </tr> -->
                <tr>
                    <td><i class="fa-solid fa-person-walking text-yellow-500"></i></td>
                    <td>Walk Time (Uris):</td>
                    <td>{{ (listing?.walk_time) ?? "N/A" }} min</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-car text-yellow-500"></i></td>
                    <td>Drive Time (Uris):</td>
                    <td>{{ (listing?.drive_time) ?? "N/A" }} min</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-bicycle text-yellow-500"></i></td>
                    <td>Bike Time (Uris):</td>
                    <td>{{ (listing?.bike_time) ?? "N/A" }} min</td>
                </tr>
                <tr>
                    <td><i class="fa-solid fa-shield-halved text-yellow-500"></i></td>
                    <td>Amenities Score:</td>
                    <td>{{ listing?.amenities_score ? listing.amenities_score.toFixed(2) : "N/A" }}/100</td>
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
            <div class="value">{{ listing?.amenities_score ? listing.amenities_score.toFixed(2) : "N/A" }}/100</div>
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

    <!-- Removed duplicate similar listings section - using CMA section instead -->

    <!-- CMA Similar Listings -->
    <div class="cma-section">
        <div class="cma-header">
            <h4 class="cma-title">
                Comparative Market Analysis
                <div class="tooltip-container">
                    <span class="tooltip-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-info-icon lucide-info">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M12 16v-4"/>
                            <path d="M12 8h.01"/>
                        </svg>
                    </span>
                    <div class="tooltip-content">
                        <div class="tooltip-title">What is CMA?</div>
                        <div class="tooltip-text">
                            Comparative Market Analysis (CMA) is another alternative valuation method.<br><br>
                            We look at the 3 most similar rental listings based on location, size, amenities, and other attributes, then average their rent.<br><br>
                            This gives you a market-based estimate of fair rent value, complementing our AI model's prediction.
                        </div>
                    </div>
                </div>
            </h4>
            <!-- Main Rent Display -->
            <div class="rent-comparison-grid">
                <!-- Actual Rent Column -->
                <div class="rent-column actual-rent">
                    <div class="rent-column-header">
                        <span class="column-label">ACTUAL RENT</span>
                    </div>
                    <div class="rent-total-section">
                        <div class="rent-amount-large">${{ listing?.rent_per_person?.toFixed(2) || 'N/A' }}</div>
                        <div class="rent-label-small">per person</div>
                    </div>
                    <div class="rent-per-person-section">
                        <div class="per-person-amount">${{ listing?.total_rent_amount ? listing.total_rent_amount.toFixed(2) : 'N/A' }}</div>
                        <div class="per-person-label">Total Rent (<span class="people-count">{{ listing?.num_people || 'N/A' }} {{ (listing?.num_people === 1) ? 'person' : 'people' }}</span>)</div>
                    </div>
                </div>

                <!-- CMA Rent Column -->
                <div class="rent-column predicted-rent">
                    <div class="rent-column-header">
                        <span class="column-label">MARKET AVERAGE RENT</span>
                    </div>
                    <div class="rent-total-section">
                        <div class="rent-amount-large predicted-amount">${{ listing?.predicted_rent_cma ? listing.predicted_rent_cma.toFixed(2) : 'N/A' }}</div>
                        <div class="rent-label-small">per person</div>
                    </div>
                    <div class="prediction-difference">
                        <div class="difference-badge" :class="{
                            'badge-overpriced': listing?.rent_per_person && listing?.predicted_rent_cma && (listing.rent_per_person - listing.predicted_rent_cma) > 0,
                            'badge-underpriced': listing?.rent_per_person && listing?.predicted_rent_cma && (listing.rent_per_person - listing.predicted_rent_cma) < 0,
                            'badge-fair': listing?.rent_per_person && listing?.predicted_rent_cma && (listing.rent_per_person - listing.predicted_rent_cma) === 0
                        }">
                            <span class="difference-arrow"></span>
                            <span class="difference-percent">{{ listing?.rent_per_person && listing?.predicted_rent_cma ? Math.abs(((listing.rent_per_person - listing.predicted_rent_cma) / listing.predicted_rent_cma) * 100).toFixed(1) : '0.0' }}%</span>
                            <span class="difference-label">{{ listing?.rent_per_person && listing?.predicted_rent_cma && (listing.rent_per_person - listing.predicted_rent_cma) < 0 ? 'Underpriced' : (listing?.rent_per_person && listing?.predicted_rent_cma && (listing.rent_per_person - listing.predicted_rent_cma) > 0 ? 'Overpriced' : 'Fair Price') }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="cma-listings-grid">
            <div v-for="(similarListing, index) in similarListings.slice(0, 4)" :key="index" class="cma-listing-card">
                <div class="card-left" @click="showListingDetails(similarListing)">
                    <div class="cma-listing-image">
                        <img 
                            v-if="extractPhoto(similarListing?.listingphotos).length > 0" 
                            :src="extractPhoto(similarListing?.listingphotos)[0]?.PhotoUrl || ''" 
                            alt="Listing Photo" 
                            class="cma-photo"
                        >
                        <div v-else class="cma-photo-placeholder">📷</div>
                    </div>
                    <div class="listing-info">
                        <div class="listing-address">{{ similarListing?.listingaddress }}</div>
                        <div class="listing-details">{{ similarListing?.bedrooms }} bed, {{ similarListing?.bathrooms }} bath</div>
                        <div class="listing-amenities" v-if="similarListing?.amenities_score">
                            Amenities: {{ similarListing?.amenities_score.toFixed(1) }}/100
                        </div>
                        <div class="listing-walk-time" v-if="similarListing?.walk_time">
                            Walk: {{ similarListing?.walk_time }} min
                        </div>
                    </div>
                </div>
                <div class="card-right">
                    <div class="listing-rent">
                        ${{ similarListing?.rent_per_person ? similarListing.rent_per_person.toFixed(2) : 'N/A' }}
                        <div class="per-person-text">per person</div>
                    </div>
                    <button class="view-more-btn" @click="selectListing(similarListing)">
                        View More
                    </button>
                </div>
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

const emit = defineEmits(['close', 'zoom', 'select-listing']);

const closePopup = () => {
    emit('close');
};

const showListingDetails = (listing: Listing) => {
    // This could show a tooltip or expand the card with more details
    console.log('Showing details for:', listing?.listingaddress);
};

const selectListing = (listing: Listing) => {
    emit('select-listing', listing);
    emit('close'); // Close current sidebar to show selected listing
};  

const currentImageIndex = ref(0); // Holds the current index of the images in the gallery
const totalImages = computed(() => extractPhoto(props.listing?.listingphotos).length); // Holds the number of images in the gallery
const similarListings = ref<Listing[]>([]);

/**
 * Percent Change
 */
const percentChange = computed(() => {
  if (!props.listing?.predictedrent || !props.listing?.rent_per_person) return 0;
  return ((props.listing.predictedrent - props.listing.rent_per_person) / props.listing.rent_per_person) * 100;
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
/**
 * Handles tooltip positioning to prevent cutoff
 */
const handleTooltipPosition = () => {
    const tooltipContainers = document.querySelectorAll('.tooltip-container');
    
    tooltipContainers.forEach(container => {
        const tooltip = container.querySelector('.tooltip-content') as HTMLElement;
        if (!tooltip) return;
        
        const checkPosition = () => {
            const rect = container.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            
            // Check if tooltip would be cut off at the top
            if (rect.top - tooltipRect.height < 0) {
                tooltip.classList.add('tooltip-below');
            } else {
                tooltip.classList.remove('tooltip-below');
            }
        };
        
        // Check on hover
        container.addEventListener('mouseenter', checkPosition);
        // Also check on window resize
        window.addEventListener('resize', checkPosition);
    });
};

onMounted(async () => {
    await fetchSimilarListings();
    // Add tooltip positioning after component is mounted
    setTimeout(handleTooltipPosition, 100);
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
    margin-bottom: 20px;
    padding: 16px 0;
    border-bottom: 2px solid #e5e7eb;
}

.rent-main-card {
    background: none;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.rent-card-header {
    margin-bottom: 20px;
    text-align: center;
}

.rent-comparison-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #374151;
    margin: 0;
    letter-spacing: 0.025em;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.tooltip-container {
    position: relative;
    display: inline-block;
}

.tooltip-icon {
    font-size: 0.9rem;
    color: #6b7280;
    cursor: help;
    transition: color 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.tooltip-icon svg {
    width: 16px;
    height: 16px;
    stroke: currentColor;
}

.tooltip-icon:hover {
    color: #374151;
}

.tooltip-content {
    visibility: hidden;
    opacity: 0;
    position: absolute;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    background: #1f2937;
    color: white;
    padding: 16px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    width: 320px;
    font-size: 0.85rem;
    line-height: 1.4;
    z-index: 1000;
    transition: opacity 0.3s ease, visibility 0.3s ease;
}

.tooltip-content::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: #1f2937 transparent transparent transparent;
}

.tooltip-content.tooltip-below {
    bottom: auto;
    top: 125%;
}

.tooltip-content.tooltip-below::after {
    top: auto;
    bottom: 100%;
    border-color: transparent transparent #1f2937 transparent;
}

.tooltip-container:hover .tooltip-content {
    visibility: visible;
    opacity: 1;
}

.tooltip-title {
    font-weight: 600;
    margin-bottom: 8px;
    color: #f9fafb;
    font-size: 0.9rem;
}

.tooltip-text {
    color: #e5e7eb;
}

.tooltip-text strong {
    color: #f9fafb;
    font-weight: 600;
}

.tooltip-green {
    color: #10b981;
    font-weight: 600;
}

.tooltip-red {
    color: #ef4444;
    font-weight: 600;
}

.rent-comparison-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    align-items: stretch;
}

.rent-column {
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    
}

.rent-column-header {
    margin-bottom: 12px;
    text-align: center;
}

.column-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.rent-total-section {
    text-align: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e5e7eb;
}

.rent-amount-large {
    font-size: 1.8rem;
    font-weight: 700;
    color: #000000;
    line-height: 1;
    margin-bottom: 4px;
}

.rent-label-small {
    font-size: 0.8rem;
    color: #000000;
    font-weight: 500;
}

.estimation-text {
    font-size: 0.7rem;
    color: #9ca3af;
    font-style: italic;
}

.model-credit {
    font-size: 0.65rem;
    color: #9ca3af;
    font-weight: 400;
    margin-top: 2px;
    opacity: 0.8;
}

.predicted-amount {
    color: #000000 !important; /* Neutral color for predicted rent */
}

.rent-per-person-section {
    text-align: center;
}

.per-person-amount {
    font-size: 1.1rem;
    font-weight: 600;
    color: black;
    margin-bottom: 2px;
}

.per-person-label {
    font-size: 0.75rem;
    color: black;
    font-weight: 500;
}

.people-count {
    font-weight: 700;
    color: #1e40af;
    background: rgba(59, 130, 246, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
}

.prediction-difference {
    text-align: center;
    margin-top: 12px;
}

.difference-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.badge-overpriced {
    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    color: #dc2626;
    border: 1px solid #fecaca;
}

.badge-underpriced {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    color: #16a34a;
    border: 1px solid #bbf7d0;
}

.pill-underpriced {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    color: #16a34a;
    border: 1px solid #bbf7d0;
}

.pill-overpriced {
    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    color: #dc2626;
    border: 1px solid #fecaca;
}

.pill-fair {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    color: #475569;
    border: 1px solid #cbd5e1;
}

.badge-fair {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    color: #6b7280;
    border: 1px solid #d1d5db;
}

.difference-arrow {
    font-size: 1rem;
}

.difference-percent {
    font-weight: 700;
}

.difference-label {
    font-size: 0.75rem;
    font-weight: 500;
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

/* CMA Section Styles */
.cma-section {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 2px solid #e5e7eb;
}

.cma-header {
    margin-bottom: 16px;
}

.cma-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #374151;
    margin: 0 0 12px 0;
    letter-spacing: 0.025em;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.cma-average {
    text-align: center;
    padding: 12px 16px;
    background: none;
    border-radius: 8px;
    margin-bottom: 16px;
}

.average-label {
    font-size: 0.85rem;
    color: #6b7280;
    font-weight: 500;
    margin-bottom: 8px;
}

.cma-split-container {
    display: flex;
    align-items: center;
    gap: 8px;
    justify-content: center;
}

.cma-price-section {
    flex: 1;
    text-align: left;
}

.cma-pill-section {
    flex: 1;
    text-align: right;
}

.average-value {
    font-size: 1.3rem;
    font-weight: 700;
    color: #1e40af;
    margin-bottom: 2px;
}

.per-person-label {
    font-size: 0.75rem;
    color: #6b7280;
    font-weight: 500;
}

.cma-listings-grid {
    display: grid;
    gap: 12px;
}

.cma-listing-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
    min-height: 100px;
}

.cma-listing-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
    border-color: #3b82f6;
}

.cma-listing-image {
    width: 20%;
    max-height: 250px;
    object-fit: cover;
}

.card-left {
    display: flex;
    align-items: center;
    flex: 1;
    min-width: 0;
    gap: 12px;
    cursor: pointer;
}

.card-left:hover {
    opacity: 0.8;
}

.card-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    flex-shrink: 0;
    gap: 8px;
}


.cma-photo {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
}

.cma-photo-placeholder {
    width: 100%;
    height: 100%;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    color: #9ca3af;
}

.listing-info {
    flex: 1;
    min-width: 0;
}

.listing-address {
    font-size: 0.9rem;
    font-weight: 500;
    color: #374151;
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.listing-details {
    font-size: 0.8rem;
    color: #6b7280;
}

.listing-amenities {
    font-size: 0.75rem;
    color: black;
    font-weight: 500;
}

.listing-walk-time {
    font-size: 0.75rem;
    color: #6b7280;
}

.listing-rent {
    font-size: 1.2rem;
    font-weight: 700;
    color: #000000;
    text-align: right;
}

.per-person-text {
    font-size: 0.75rem;
    color: #6b7280;
    font-weight: 500;
    margin-top: 2px;
}

.view-more-btn {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.view-more-btn:hover {
    background: #2563eb;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.cma-comparison {
    margin-top: 16px;
    text-align: center;
}

.comparison-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    white-space: nowrap;
}

.pill-arrow {
    font-size: 0.9rem;
}

.pill-text {
    font-size: 0.8rem;
}

.comparison-arrow {
    font-size: 1rem;
}

.comparison-text {
    font-weight: 500;
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
        margin-bottom: 12px;
    }

    .rent-main-card {
        padding: 16px;
    }

    .rent-comparison-grid {
        grid-template-columns: 1fr;
        gap: 12px;
    }

    .rent-column {
        padding: 12px;
    }

    .rent-amount-large {
        font-size: 1.5rem;
    }

    .rent-comparison-title {
        font-size: 1rem;
    }

    .tooltip-content {
        width: 280px;
        font-size: 0.8rem;
        padding: 12px;
    }

    .column-label {
        font-size: 0.8rem;
    }

    .difference-badge {
        font-size: 0.8rem;
        padding: 6px 10px;
    }

    .cma-average {
        text-align: center;
        padding: 8px 12px;
    }

    .cma-split-container {
        flex-direction: column;
        gap: 8px;
        align-items: center;
    }

    .cma-price-section {
        text-align: center;
    }

    .cma-pill-section {
        text-align: center;
    }

    .average-value {
        font-size: 1.1rem;
    }

    .comparison-pill {
        font-size: 0.75rem;
        padding: 4px 12px;
    }

    .per-person-text {
        font-size: 0.7rem;
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