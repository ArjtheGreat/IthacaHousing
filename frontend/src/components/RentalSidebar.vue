<template>
<div class="popup-container">
    <!-- Header -->
    <div class="popup-header">
        <div class="popup-title-row">
            <h3 class="popup-title">
                {{ listing?.listingaddress }}, 
                <span v-if="listing?.listingcity">{{ listing?.listingcity }},</span> 
                {{ listing?.listingzip }}
            </h3>
            <button class="close-btn" @click="closePopup">✖</button>
        </div>
        <!-- Landlord Section -->
        <div class="popup-landlord">
            <div class="landlord-oneline">
                <i class="fa-solid fa-user" style="color: #6366f1; margin-right: 6px; font-size: 14px;"></i>
                <strong>{{ getLandlordHeader() }}:</strong>&nbsp;<span class="landlord-names-text">{{ getLandlordNames() }}</span>
            </div>
        </div>
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
            
            <!-- Disclaimer -->
            <div class="rent-disclaimer">
                <i class="fa-solid fa-info-circle"></i>
                <span>Fair rent estimates are based on a proprietary machine learning model for investigative purposes only. Results should not be considered as official market valuations. Please dig further if you are interested in a listing.</span>
            </div>
        </div>
    </div>
    <!-- Property Details -->
    <div class="property-size">
            <div class="property-size-header">
                <strong>Property Size</strong>
            </div>
        <div class="details-grid">
            <div class="detail-card bedroom-card">
                <div class="detail-icon">
                    <i class="fa-solid fa-bed"></i>
                </div>
                <div class="detail-content">
                    <div class="detail-number">
                        {{ listing?.available_bedrooms || 'N/A' }} {{ (listing?.available_bedrooms === 1) ? 'Bedroom' : 'Bedrooms' }}
                    </div>
                </div>
            </div>
            
            <div class="detail-card bathroom-card">
                <div class="detail-icon">
                    <i class="fa-solid fa-bath"></i>
                </div>
                <div class="detail-content">
                    <div class="detail-number">
                        {{ listing?.available_bathrooms || 'N/A' }} {{ (listing?.available_bathrooms === 1) ? 'Bathroom' : 'Bathrooms' }}
                    </div>
                </div>
            </div>
        </div>
    </div>


    <!-- Amenities Section -->
    <div class="popup-amenities">
        <div class="amenities-header">
            <strong>Amenities</strong>
        </div>
        
        <div class="amenities-categories" v-if="formatAmenities(listing?.amenities, listing?.pets).length > 0">
            <div 
                v-for="(category, index) in formatAmenities(listing?.amenities, listing?.pets)" 
                :key="category.category" 
                class="amenity-category"
                :class="{ 'category-other': category.category === 'Other' && formatAmenities(listing?.amenities, listing?.pets).length % 2 === 1 }"
            >
                <div class="category-header">
                    <i :class="category.icon" class="category-icon" :style="{ color: category.color }"></i>
                    <span class="category-name">{{ category.category }}</span>
                </div>
                <div class="amenity-pills">
                    <div 
                        v-for="amenity in category.amenities" 
                        :key="amenity.name" 
                        class="amenity-pill"
                        :style="{ '--pill-color': category.color }"
                    >
                        {{ amenity.name }}
                    </div>
                </div>
            </div>
        </div>
        
        <div v-else class="no-amenities">
            <i class="fa-solid fa-info-circle"></i>
            <span>No amenities listed</span>
        </div>
    </div>

    <!-- Transit Section -->
    <div class="popup-transit">
        <div class="transit-header">
            <strong>Transit Accessibility</strong>
            <div class="transit-score">
                <div class="score-visual">
                    <div class="score-bar">
                        <div 
                            class="score-fill" 
                            :style="{ width: (listing?.transit_score || 0) + '%' }"
                        ></div>
                    </div>
                    <span class="score-text">{{ listing?.transit_score ? listing.transit_score.toFixed(0) : "0" }}/100</span>
                    <div class="tooltip-container">
                        <span class="tooltip-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-info-icon lucide-info">
                                <circle cx="12" cy="12" r="10"/>
                                <path d="M12 16v-4"/>
                                <path d="M12 8h.01"/>
                            </svg>
                        </span>
                        <div class="tooltip-content">
                            <div class="tooltip-title">Transit & Accessibility</div>
                            <div class="tooltip-text">
                                The transit score calculates how accessible this listing is to different areas of Cornell. Based on the transit time and how close the nearest TCAT stop is located.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="public-transit-info">
            <!-- Nearest Bus Stop -->
            <div class="nearest-stop">
                <span class="stop-label">Nearest Stop:</span>
                <span class="stop-name">{{ listing?.nearest_stop_name }}</span>
                <span class="walk-time" v-if="listing?.walk_time_to_nearest_stop">
                    <i class="fa-solid fa-person-walking" style="color: #10b981;"></i>
                    {{ formatWalkTime(listing.walk_time_to_nearest_stop) }}
                </span>
            </div>
        </div>
        
        <div class="transit-quads">
            <div class="transit-quad">
                <div class="quad-header">
                    <i class="fa-solid fa-graduation-cap" style="color: #8b5cf6;"></i>
                    <span class="quad-name">Arts Quad</span>
                </div>
                <div class="quad-times">
                    <div class="time-item">
                        <i class="fa-solid fa-bus" style="color: #3b82f6;"></i>
                        <span>{{ listing?.transit_time_to_arts_quad ? listing.transit_time_to_arts_quad.toFixed(1) : "N/A" }} min</span>
                    </div>
                    <div class="time-item">
                        <i class="fa-solid fa-person-walking" style="color: #10b981;"></i>
                        <span>{{ listing?.walk_time_artsquad ? listing.walk_time_artsquad.toFixed(0) : "N/A" }} min</span>
                    </div>
                    <div class="time-item">
                        <i class="fa-solid fa-car" style="color: #ef4444;"></i>
                        <span>{{ listing?.drive_time_artsquad ? listing.drive_time_artsquad.toFixed(0) : "N/A" }} min</span>
                    </div>
                </div>
            </div>
            
            <div class="transit-quad">
                <div class="quad-header">
                    <i class="fa-solid fa-seedling" style="color: #10b981;"></i>
                    <span class="quad-name">Ag Quad</span>
                </div>
                <div class="quad-times">
                    <div class="time-item">
                        <i class="fa-solid fa-bus" style="color: #3b82f6;"></i>
                        <span>{{ listing?.transit_time_to_ag_quad ? listing.transit_time_to_ag_quad.toFixed(1) : "N/A" }} min</span>
                    </div>
                    <div class="time-item">
                        <i class="fa-solid fa-person-walking" style="color: #10b981;"></i>
                        <span>{{ listing?.walk_time_agriculturequad ? listing.walk_time_agriculturequad.toFixed(0) : "N/A" }} min</span>
                    </div>
                    <div class="time-item">
                        <i class="fa-solid fa-car" style="color: #ef4444;"></i>
                        <span>{{ listing?.drive_time_agriculturequad ? listing.drive_time_agriculturequad.toFixed(0) : "N/A" }} min</span>
                    </div>
                </div>
            </div>
            
            <div class="transit-quad">
                <div class="quad-header">
                    <i class="fa-solid fa-cogs" style="color: #f59e0b;"></i>
                    <span class="quad-name">Eng Quad</span>
                </div>
                <div class="quad-times">
                    <div class="time-item">
                        <i class="fa-solid fa-bus" style="color: #3b82f6;"></i>
                        <span>{{ listing?.transit_time_to_eng_quad ? listing.transit_time_to_eng_quad.toFixed(1) : "N/A" }} min</span>
                    </div>
                    <div class="time-item">
                        <i class="fa-solid fa-person-walking" style="color: #10b981;"></i>
                        <span>{{ listing?.walk_time_engineeringquad ? listing.walk_time_engineeringquad.toFixed(0) : "N/A" }} min</span>
                    </div>
                    <div class="time-item">
                        <i class="fa-solid fa-car" style="color: #ef4444;"></i>
                        <span>{{ listing?.drive_time_engineeringquad ? listing.drive_time_engineeringquad.toFixed(0) : "N/A" }} min</span>
                    </div>
                </div>
            </div>
        </div>       
    </div>


    <!-- Description -->
    <!-- Property Details -->
    <div class="property-details">
        <div class="property-details-header">
            <strong>Property & Lease Details</strong>
        </div>
        
        <!-- Basic Property Info -->
        <div class="property-section">
            <h4 class="section-title">From the Owner</h4>
            <div class="description-content">
                {{ listing?.shortdescription }}
            </div>
        </div>

        <!-- Property Assessment Details -->
        <div class="property-section">
            <h4 class="section-title">Property Assessment</h4>
            <div class="info-grid" style="grid-template-columns: repeat(3, 1fr);">
                <!-- Year Built -->
                <div class="info-card assessment-card">
                    <div class="info-icon">
                        <i class="fa-solid fa-calendar-days"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">Year Built</div>
                        <div class="info-value">{{ listing?.year_built || 'N/A' }}</div>
                    </div>
                </div>

                <!-- Neighborhood Assessment -->
                <div class="info-card assessment-card">
                    <div class="info-icon">
                        <i class="fa-solid fa-map-marker-alt"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">Neighborhood</div>
                        <div class="info-value">{{ listing?.neighborhood_assessment || 'N/A' }}</div>
                    </div>
                </div>

                <!-- Certificate of Compliance -->
                <div class="info-card assessment-card" ref="tooltipElement" @mouseenter="showComplianceTooltip = true" @mouseleave="showComplianceTooltip = false">
                    <div class="info-icon">
                        <i class="fa-solid fa-shield-check"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">Safety Status</div>
                        <div class="assessment-value-container">
                            <div class="info-value" :class="getComplianceClass()">
                                {{ getComplianceStatus() }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Tooltip positioned outside container -->
            <div v-if="showComplianceTooltip" class="compliance-tooltip-absolute" :style="tooltipStyle">
                {{ getComplianceTooltipText() }}
            </div>
        </div>

        <!-- Lease Information -->
        <div class="property-section">
            <h4 class="section-title">Lease Information</h4>
            <div class="info-grid" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));">
               

                <!-- Date Available -->
                <div class="info-card lease-card" v-if="listing?.dateavailable">
                    <div class="info-icon">
                        <i class="fa-solid fa-calendar-check"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">Date Available</div>
                        <div class="info-value">{{ formatDate(listing.dateavailable) }}</div>
                    </div>
                </div>

                <!-- Length Available -->
                <div class="info-card lease-card" v-if="listing?.lengthavailable">
                    <div class="info-icon">
                        <i class="fa-solid fa-clock"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">Lease Duration</div>
                        <div class="info-value">{{ formatLeaseDuration(listing.lengthavailable) }}</div>
                    </div>
                </div>

                <!-- Listing Type -->
                <div class="info-card lease-card" v-if="listing?.listingtypes">
                    <div class="info-icon">
                        <i class="fa-solid fa-list"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">Listing Type</div>
                        <div class="info-value">{{ formatListingTypes(listing.listingtypes) }}</div>
                    </div>
                </div>

                <!-- Listing Expiration -->
                <div class="info-card lease-card" v-if="listing?.listingexpirationdate">
                    <div class="info-icon">
                        <i class="fa-solid fa-calendar-times"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">Expires</div>
                        <div class="info-value">{{ formatDate(listing.listingexpirationdate) }}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Utilities & Services
        <div class="property-section">
            <h4 class="section-title">Utilities & Services</h4>
            <div class="info-grid" style="grid-template-columns: repeat(3, 1fr);">
                <div class="info-card utility-card">
                    <div class="info-icon water">
                        <i class="fa-solid fa-tint"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">Water</div>
                        <div class="info-value">{{ listing?.water_access ? formatUtilityValue(listing.water_access) : 'N/A' }}</div>
                    </div>
                </div>

                <div class="info-card utility-card">
                    <div class="info-icon sewer">
                        <i class="fa-solid fa-pipe"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">Sewer</div>
                        <div class="info-value">{{ listing?.sewer_access ? formatUtilityValue(listing.sewer_access) : 'N/A' }}</div>
                    </div>
                </div>

                <div class="info-card utility-card">
                    <div class="info-icon system">
                        <i class="fa-solid fa-cogs"></i>
                    </div>
                    <div class="info-content">
                        <div class="info-label">Sewer System</div>
                        <div class="info-value">{{ listing?.sewer_name ? formatUtilityValue(listing.sewer_name) : 'N/A' }}</div>
                    </div>
                </div>
            </div> 
        </div>  -->
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
                        <div class="listing-details">{{ similarListing?.available_bedrooms }} bed, {{ similarListing?.available_bathrooms }} bath</div>
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
        
        <!-- CMA Disclaimer -->
        <div class="cma-disclaimer">
            <i class="fa-solid fa-info-circle"></i>
            <span>Comparative market analysis estimates are based on a proprietary machine learning model for investigative purposes only. Results should not be considered as official market valuations. Please dig further if you are interested in a listing.</span>
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

const showTooltip = ref(false);

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
const showComplianceTooltip = ref(false);
const tooltipElement = ref<HTMLElement | null>(null);

/**
 * Percent Change
 */
const percentChange = computed(() => {
  if (!props.listing?.predictedrent || !props.listing?.rent_per_person) return 0;
  return ((props.listing.predictedrent - props.listing.rent_per_person) / props.listing.rent_per_person) * 100;
});

/**
 * Format walk time into user-friendly ranges
 * @param {number} minutes - Walk time in minutes
 * @returns {string} - Formatted walk time string
 */
const formatWalkTime = (minutes: number): string => {
    if (minutes < 2) return '< 2 min walk';
    if (minutes < 5) return '< 5 min walk';
    if (minutes < 10) return '5-10 min walk';
    if (minutes < 15) return '10-15 min walk';
    if (minutes < 20) return '15-20 min walk';
    return '20+ min walk';
};

/**
 * Format date string to readable format
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date string
 */
const formatDate = (dateString: string): string => {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateString;
    }
};

/**
 * Format lease duration to readable format
 * @param {number} length - Lease length (in months typically)
 * @returns {string} - Formatted duration string
 */
const formatLeaseDuration = (length: number): string => {
    if (!length) return 'N/A';
    if (length === 12) return '12 months';
    if (length === 9) return '9 months';
    if (length === 6) return '6 months';
    if (length === 3) return '3 months';
    if (length === 1) return '1 month';
    return `${length} months`;
};

/**
 * Check if property has assessment data
 */
const hasPropertyAssessmentData = computed(() => {
    return props.listing?.year_built || 
           props.listing?.assessment_sqft || 
           props.listing?.sale_price || 
           props.listing?.property_acres || 
           props.listing?.property_frontage || 
           props.listing?.property_depth || 
           props.listing?.neighborhood_assessment;
});

/**
 * Check if property has utility data
 */
const hasUtilityData = computed(() => {
    return props.listing?.water_access || 
           props.listing?.sewer_access || 
           props.listing?.sewer_name || 
           props.listing?.property_pc;
});

/**
 * Format numbers with commas for better readability
 */
const formatNumber = (num: number): string => {
    if (!num) return '0';
    return num.toLocaleString();
};

/**
 * Format utility values for better display
 */
const formatUtilityValue = (value: string): string => {
    if (!value) return 'N/A';
    return value.replace('Comm/public', 'Communal/Public')
                .replace('Solid waste fee res.', 'Solid Waste Fee');
};

/**
 * Format listing types to readable format
 * Backend now returns an array, so we just need to join it
 */
const formatListingTypes = (value: string | string[] | undefined): string => {
    if (!value) return 'N/A';
    
    // If it's an array, join it
    if (Array.isArray(value)) {
        return value.join(', ');
    }
    
    // Fallback for any string values
    return String(value);
};

/**
 * Get compliance status text
 */
const getComplianceStatus = (): string => {
    if (props.listing?.valid_certificate_of_compliance === 1) {
        return 'Compliant';
    } else if (props.listing?.valid_certificate_of_compliance === 0) {
        return 'Not Compliant';
    }
    return 'Unknown';
};

/**
 * Get compliance status CSS class
 */
const getComplianceClass = (): string => {
    if (props.listing?.valid_certificate_of_compliance === 1) {
        return 'compliant';
    } else if (props.listing?.valid_certificate_of_compliance === 0) {
        return 'non-compliant';
    }
    return 'unknown';
};

/**
 * Get compliance tooltip text
 */
const getComplianceTooltipText = (): string => {
    if (props.listing?.valid_certificate_of_compliance === 1) {
        return 'This property is currently reporting as safety compliant with valid certificate of compliance';
    } else if (props.listing?.valid_certificate_of_compliance === 0) {
        return 'This property is currently not reporting as safety compliant';
    }
    return 'Certificate of Compliance status is currently unknown';
};

/**
 * Tooltip positioning style
 */
const tooltipStyle = computed((): Record<string, string | number> => {
    if (!showComplianceTooltip.value || !tooltipElement.value) {
        return { 
            display: 'none',
            position: 'fixed',
            top: '0px',
            left: '0px',
            transform: 'translateX(-50%)',
            zIndex: '10000'
        };
    }
    
    const rect = tooltipElement.value.getBoundingClientRect();
    return {
        display: 'block',
        position: 'fixed',
        top: `${rect.top - 50}px`,
        left: `${rect.left + rect.width / 2}px`,
        transform: 'translateX(-50%)',
        zIndex: '10000'
    };
});

/**
 * Categorizes and maps amenities to their appropriate category and icon
 * @param {string} amenity - The amenity name
 * @returns {object} - Object with category, icon, and color
 */
const categorizeAmenity = (amenity: string): {category: string, icon: string, color: string} => {
  const amenityLower = amenity.toLowerCase();
  
  // Kitchen & Cooking
  if (amenityLower.includes('dishwasher') || amenityLower.includes('dish') || 
      amenityLower.includes('microwave') || amenityLower.includes('refrigerator') || 
      amenityLower.includes('fridge') || amenityLower.includes('stove') || 
      amenityLower.includes('oven') || amenityLower.includes('cooking')) {
    return {
      category: 'Kitchen',
      icon: 'fa-solid fa-utensils',
      color: '#f59e0b' // amber
    };
  }
  
  // Laundry
  if (amenityLower.includes('washer') || amenityLower.includes('laundry') || 
      amenityLower.includes('dryer')) {
    return {
      category: 'Laundry',
      icon: 'fa-solid fa-tshirt',
      color: '#3b82f6' // blue
    };
  }
  
  // Internet & Technology
  if (amenityLower.includes('wifi') || amenityLower.includes('internet') || 
      amenityLower.includes('wireless') || amenityLower.includes('cable') || 
      amenityLower.includes('tv')) {
    return {
      category: 'Technology',
      icon: 'fa-solid fa-wifi',
      color: '#8b5cf6' // purple
    };
  }
  
  // Parking & Transportation
  if (amenityLower.includes('parking') || amenityLower.includes('garage') || 
      amenityLower.includes('elevator')) {
    return {
      category: 'Transportation',
      icon: 'fa-solid fa-car',
      color: '#6b7280' // gray
    };
  }
  
  // Utilities
  if (amenityLower.includes('heat') || amenityLower.includes('heating') || 
      amenityLower.includes('air') || amenityLower.includes('ac') || 
      amenityLower.includes('cooling') || amenityLower.includes('water') || 
      amenityLower.includes('electric')) {
    return {
      category: 'Utilities',
      icon: 'fa-solid fa-bolt',
      color: '#f59e0b' // yellow/amber
    };
  }
  
  // Security & Safety
  if (amenityLower.includes('security') || amenityLower.includes('alarm') || 
      amenityLower.includes('smoke') || amenityLower.includes('detector')) {
    return {
      category: 'Security',
      icon: 'fa-solid fa-shield-halved',
      color: '#10b981' // green
    };
  }
  
  // Outdoor & Recreation
  if (amenityLower.includes('balcony') || amenityLower.includes('patio') || 
      amenityLower.includes('deck') || amenityLower.includes('pool') || 
      amenityLower.includes('swimming') || amenityLower.includes('gym') || 
      amenityLower.includes('fitness') || amenityLower.includes('exercise')) {
    return {
      category: 'Recreation',
      icon: 'fa-solid fa-dumbbell',
      color: '#06b6d4' // cyan
    };
  }
  
  // Storage & Space
  if (amenityLower.includes('storage') || amenityLower.includes('closet') || 
      amenityLower.includes('walk')) {
    return {
      category: 'Storage',
      icon: 'fa-solid fa-archive',
      color: '#84cc16' // lime
    };
  }
  
  // Pets (moved to Other category)
  if (amenityLower.includes('pet') || amenityLower.includes('dog') || 
      amenityLower.includes('cat')) {
    return {
      category: 'Other',
      icon: 'fa-solid fa-check-circle',
      color: '#6b7280' // gray
    };
  }
  
  // Accessibility
  if (amenityLower.includes('accessible') || amenityLower.includes('handicap') || 
      amenityLower.includes('wheelchair')) {
    return {
      category: 'Accessibility',
      icon: 'fa-solid fa-wheelchair',
      color: '#ec4899' // pink
    };
  }
  
  // Default category for unmatched amenities
  return {
    category: 'Other',
    icon: 'fa-solid fa-check-circle',
    color: '#6b7280' // gray
  };
};

/**
 * Formats amenities data grouped by category for display.
 * @param {any} amenitiesData - JSON object, array, or string of amenities.
 * @param {any} petsData - Pets information from listing.
 * @returns {Array} - Array of category objects with amenities grouped.
 */
const formatAmenities = (amenitiesData: any, petsData?: any): Array<{category: string, icon: string, color: string, amenities: Array<{name: string}>}> => {
  try {
    let amenities: string[] = [];
    
    // Process amenities data
    if (amenitiesData) {
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
    }
    
    // Add pets information if available
    if (petsData && petsData === "Yes") {
      amenities.push("Pets Allowed");
    }
    
    if (!Array.isArray(amenities)) return [];
    
    // Group amenities by category
    const categoryMap = new Map();
    
    amenities.forEach(amenity => {
      const trimmedAmenity = amenity.trim();
      const categoryInfo = categorizeAmenity(trimmedAmenity);
      const categoryKey = categoryInfo.category;
      
      if (!categoryMap.has(categoryKey)) {
        categoryMap.set(categoryKey, {
          category: categoryKey,
          icon: categoryInfo.icon,
          color: categoryInfo.color,
          amenities: []
        });
      }
      
      categoryMap.get(categoryKey).amenities.push({
        name: trimmedAmenity
      });
    });
    
    // Convert map to array and sort by category name, with "Other" always last
    return Array.from(categoryMap.values()).sort((a, b) => {
      if (a.category === 'Other') return 1;
      if (b.category === 'Other') return -1;
      return a.category.localeCompare(b.category);
    });
  } catch (error) {
    console.warn('Error formatting amenities:', error);
    return [];
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

/**
 * Format owner names from various formats to a readable string
 * @param {string} ownerName - The raw owner name string
 * @returns {string} - Formatted owner names
 */
const formatOwnerNames = (ownerName: string): string => {
    if (!ownerName || ownerName === 'undefined' || ownerName === 'null') return '';
    
    try {
        // Handle JSON-like strings like {"Fumio Onishi", "Deidre Onishi"}
        if (ownerName.includes('{') && ownerName.includes('}')) {
            // Remove parentheses and braces
            let cleaned = ownerName.replace(/[(){}]/g, '');
            // Split by comma and clean up quotes
            const names = cleaned.split(',').map(name => 
                name.trim().replace(/"/g, '').replace(/'/g, '')
            ).filter(name => name.length > 0 && name !== 'undefined' && name !== 'null');
            
            if (names.length === 0) return '';
            if (names.length === 1) {
                return names[0];
            } else if (names.length === 2) {
                return `${names[0]} and ${names[1]}`;
            } else {
                return names.slice(0, -1).join(', ') + `, and ${names[names.length - 1]}`;
            }
        }
        
        // Handle comma-separated names
        if (ownerName.includes(',')) {
            const names = ownerName.split(',').map(name => name.trim())
                .filter(name => name.length > 0 && name !== 'undefined' && name !== 'null');
            
            if (names.length === 0) return '';
            if (names.length === 1) {
                return names[0];
            } else if (names.length === 2) {
                return `${names[0]} and ${names[1]}`;
            } else {
                return names.slice(0, -1).join(', ') + `, and ${names[names.length - 1]}`;
            }
        }
        
        // Return as-is for single names (but filter out undefined/null)
        const trimmed = ownerName.trim();
        if (trimmed === 'undefined' || trimmed === 'null' || trimmed === '') {
            return '';
        }
        return trimmed;
    } catch (error) {
        console.warn('Error parsing owner names:', error);
        return '';
    }
};

/**
 * Get the appropriate header text based on number of landlords
 * @returns {string} - "Landlord" or "Landlords"
 */
const getLandlordHeader = (): string => {
    if (!props.listing?.owner_name) return 'Landlord';
    
    const nameCount = countOwnerNames(props.listing.owner_name);
    return nameCount > 1 ? 'Landlords' : 'Landlord';
};

/**
 * Get the formatted landlord names or "Unknown"
 * @returns {string} - Formatted names or "Unknown"
 */
const getLandlordNames = (): string => {
    const ownerName = props.listing?.owner_name;
    
    // Handle undefined, null, empty string, or "undefined" string
    if (!ownerName || ownerName === 'undefined' || ownerName === 'null' || ownerName.trim() === '') {
        return 'Unknown';
    }
    
    const formatted = formatOwnerNames(ownerName);
    
    // Double-check if formatting resulted in undefined or empty
    if (!formatted || formatted === 'undefined' || formatted.trim() === '') {
        return 'Unknown';
    }
    
    return formatted;
};

/**
 * Count the number of owner names in the string
 * @param {string} ownerName - The raw owner name string
 * @returns {number} - Number of names
 */
const countOwnerNames = (ownerName: string): number => {
    if (!ownerName) return 0;
    
    try {
        // Handle JSON-like strings like {"Fumio Onishi", "Deidre Onishi"}
        if (ownerName.includes('{') && ownerName.includes('}')) {
            let cleaned = ownerName.replace(/[(){}]/g, '');
            const names = cleaned.split(',').map(name => 
                name.trim().replace(/"/g, '').replace(/'/g, '')
            ).filter(name => name.length > 0);
            return names.length;
        }
        
        // Handle comma-separated names
        if (ownerName.includes(',')) {
            return ownerName.split(',').filter(name => name.trim().length > 0).length;
        }
        
        // Single name
        return ownerName.trim().length > 0 ? 1 : 0;
    } catch (error) {
        console.warn('Error counting owner names:', error);
        return 1; // Fallback to single
    }
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
    border-bottom: 2px solid #e5e7eb;
    padding: 8px 0px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 8px;
}

.popup-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
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
    color: #000000;
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
  color: #000000;
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
    padding: 8px 0;
    border-bottom: 2px solid #e5e7eb;
}

.rent-disclaimer {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin-top: 12px;
    padding: 10px 12px;
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.6rem;
    color: #64748b;
    line-height: 1.4;
}

.rent-disclaimer i {
    color: #6b7280;
    margin-top: 2px;
    flex-shrink: 0;
}

/* 🏠 PROPERTY DETAILS */
.property-size {
    padding: 0;
    margin-top: 12px;
    margin-bottom: 12px;
}

.property-size-header {
    margin-bottom: 8px;
    padding-bottom: 8px;
    font-size: 1.1rem;
    color: #000000;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.property-size-header strong {
    font-weight: 600;
}

.details-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

.detail-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all 0.2s ease;
}

.detail-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.detail-icon {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
    background: #f3f4f6;
    color: #000000;
}

.detail-content {
    flex: 1;
}

.detail-number {
    font-size: 1rem;
    font-weight: 700;
    color: #1f2937;
    line-height: 1;
}

/* Property Section Styles */
.property-details {
    padding: 12px 0;
    margin-top: 12px;
    margin-bottom: 12px;
    border-top: 2px solid #e5e7eb;
}


.property-details-header {
    margin-bottom: 8px;
    padding-bottom: 8px;
    font-size: 1.1rem;
    color: #000000;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.property-details-header strong {
    font-weight: 600;
}

.property-section {
    margin-bottom: 16px;
}

.property-section:last-child {
    margin-bottom: 0;
}

.section-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #1f2937;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Base Info Grid */
.info-grid {
    display: grid;
    gap: 12px;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

/* Smaller variant (used by utilities) */
.info-grid.compact {
    gap: 10px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

/* Base Info Card */
.info-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    transition: all 0.2s ease;
    min-height: 60px;
    position: relative;
    overflow: hidden;
}

.info-card:hover {
    border-color: #d1d5db;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    transform: translateY(-1px);
}

/* Base Icon */
.info-icon {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    flex-shrink: 0;
}

/* Base Content */
.info-content {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.info-label {
    font-size: 0.7rem;
    font-weight: 500;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.025em;
    margin-bottom: 1px;
    line-height: 1;
}

.info-value {
    font-size: 0.8rem;
    font-weight: 600;
    color: #1f2937;
    line-height: 1.1;
    word-break: break-word;
}

/* Assessment-Specific Styling */
.assessment-card .info-icon {
    background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
    color: #374151;
}

.assessment-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
    background: linear-gradient(135deg, #10b981, #059669);
    opacity: 0;
    transition: opacity 0.2s ease;
}
.assessment-card:hover::before {
    opacity: 1;
}

/* Lease-Specific Styling */
.lease-card .info-icon {
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    color: #1e40af;
}

.lease-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    opacity: 0;
    transition: opacity 0.2s ease;
}
.lease-card:hover::before {
    opacity: 1;
}


/* Compliance status */
.info-value.compliant {
    color: #16a34a;
    font-weight: 700;
}
.info-value.non-compliant {
    color: #dc2626;
    font-weight: 700;
}
.info-value.unknown {
    color: #6b7280;
    font-weight: 600;
}

/* Tooltip container */
.assessment-value-container {
    position: relative;
    display: inline-block;
}

.compliance-tooltip {
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: #1f2937;
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 500;
    white-space: normal;
    max-width: 200px;
    text-align: center;
    z-index: 1000;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-bottom: 4px;
}

/* Utility-Specific Accent */
.utility-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
    background: linear-gradient(135deg, #10b981, #059669);
    opacity: 0;
    transition: opacity 0.2s ease;
}
.utility-card:hover::before {
    opacity: 1;
}

/* Color-coded icons */
.utility-card .info-icon.water { background: #dbeafe; color: #2563eb; }
.utility-card .info-icon.sewer { background: #f3e8ff; color: #7c3aed; }
.utility-card .info-icon.system { background: #fef3c7; color: #d97706; }
.utility-card .info-icon.class { background: #dcfce7; color: #16a34a; }


/* Description Content */
.description-content {
    color: #1f2937;
    font-size: 0.95rem;
    line-height: 1.6;
    font-weight: 400;
    margin-top: 8px;
    text-align: left;
}


/* Compliance Status Styling */

/* Absolute positioned tooltip outside container */
.compliance-tooltip-absolute {
    position: fixed;
    background: #1f2937;
    color: white;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 500;
    white-space: normal;
    width: 200px;
    text-align: center;
    z-index: 10000;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    pointer-events: none;
    line-height: 1.4;
}

.rent-main-card {
    background: none;
    padding: 8px;
}

.rent-card-header {
    margin-bottom: 16px;
    text-align: center;
}

.rent-comparison-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #000000;
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
    color: #000000;
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
    color: #000000;
}

.tooltip-content {
    visibility: hidden;
    opacity: 0;
    position: absolute;
    bottom: 125%;
    right: 0;
    transform: translateX(0);
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
    right: 20px;
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
    color: #000000;
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
    color: #000000;
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
    color: #000000;
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
    margin-top: 12px;
    padding-top: 12px;
    padding-bottom: 12px;
    border-top: 2px solid #e5e7eb;
}

.cma-disclaimer {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin-top: 12px;
    padding: 10px 12px;
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.6rem;
    color: #64748b;
    line-height: 1.4;
}

.cma-disclaimer i {
    color: #6b7280;
    margin-top: 2px;
    flex-shrink: 0;
}

.cma-header {
    margin-bottom: 16px;
}

.cma-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #000000;
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
    color: #000000;
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

/* 🔒 SAFETY SECTION */

/* 📝 DESCRIPTION */
.popup-description {
    font-size: 1rem;
    color: #555;
    border-top: 2px solid #e5e7eb;
    padding-top: 12px;
    padding-bottom: 12px;
    margin-top: 12px;
    margin-bottom: 12px;
}

.description-header {
    margin-bottom: 8px;
}

.description-header strong {
    font-size: 1.1rem;
    color: #000000;
    font-weight: 600;
}

.description-content {
    color: #555;
    line-height: 1.5;
}

/* 🏠 LANDLORD SECTION */
.popup-landlord {
    font-size: 0.95rem;
    color: #555;
    margin-top: 12px;
    margin-bottom: 0;
}

.landlord-oneline {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    background: none;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    min-width: 0; /* Allow flex item to shrink */
    overflow: hidden;
}

.landlord-oneline strong {
    color: #1f2937;
    margin-right: 0;
}

.landlord-names-text {
    font-weight: 500;
    color: #374151;
    display: flex;
    align-items: center;
    min-width: 0; /* Allow flex item to shrink */
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* 📌 AMENITIES SECTION */
.popup-transit {
    border-top: 2px solid #e5e7eb;
    padding-top: 12px;
    padding-bottom: 12px;
    margin-top: 12px;
    margin-bottom: 12px;
    font-size: 1rem;
    color: #444;
}

.transit-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.transit-score {
    display: flex;
    align-items: center;
    gap: 8px;
}

.transit-fill {
    background: linear-gradient(90deg, #3b82f6, #1d4ed8);
}

.transit-details {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.transit-info-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
}

.transit-info-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 8px;
}

.transit-info-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.stop-name {
    font-weight: 500;
    color: #1f2937;
}

.walk-time {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.9rem;
    color: #6b7280;
}

.transit-times {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
}

.transit-times-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 12px;
}

.transit-times-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
}

.transit-time-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px;
    background: white;
    border-radius: 6px;
    border: 1px solid #f1f5f9;
}

.time-destination {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9rem;
}

.time-value {
    font-weight: 600;
    color: #1f2937;
}

.popup-amenities {
    border-top: 2px solid #e5e7eb;
    padding: 8px 0px;
    font-size: 1rem;
    color: #444;
}

.amenities-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.amenities-title-container {
    display: flex;
    align-items: center;
    gap: 6px;
}

.amenities-header strong {
    font-size: 1.1rem;
    color: #000000;
    font-weight: 600;
}

.amenities-score {
    display: flex;
    align-items: center;
    gap: 8px;
}

.score-visual {
    display: flex;
    align-items: center;
    gap: 8px;
}

.score-bar {
    width: 60px;
    height: 6px;
    background: #e5e7eb;
    border-radius: 3px;
    overflow: hidden;
}

.score-fill {
    height: 100%;
    background: linear-gradient(90deg, #10b981 0%, #3b82f6 100%);
    border-radius: 3px;
    transition: width 0.3s ease;
}

.score-text {
    font-size: 0.85rem;
    font-weight: 600;
    color: #374151;
    min-width: 35px;
}

.amenities-categories {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px 20px;
}

.amenity-category {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    transition: all 0.2s ease;
}

.amenity-category:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.category-other {
    grid-column: span 2;
}

.category-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}

.category-icon {
    font-size: 1.1rem;
    width: 20px;
    text-align: center;
}

.category-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: #374151;
}

.amenity-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-left: 0; /* No margin needed with container padding */
}

.amenity-pill {
    background: rgba(59, 130, 246, 0.1);
    color: #1e40af;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 500;
    border: 1px solid rgba(59, 130, 246, 0.2);
    transition: all 0.2s ease;
    background: color-mix(in srgb, var(--pill-color) 10%, white);
    color: var(--pill-color);
    border-color: color-mix(in srgb, var(--pill-color) 20%, transparent);
}

.amenity-pill:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.no-amenities {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #9ca3af;
    font-style: italic;
    font-size: 0.9rem;
    padding: 20px;
    text-align: center;
    justify-content: center;
}

.no-amenities i {
    color: #d1d5db;
}

/* 🚌 TRANSIT SECTION */
.popup-transit {
    border-top: 2px solid #e5e7eb;
    padding-top: 12px;
    padding-bottom: 12px;
    margin-top: 12px;
    margin-bottom: 12px;
    font-size: 1rem;
    color: #444;
}

.transit-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.transit-header strong {
    font-size: 1.1rem;
    color: #000000;
    font-weight: 600;
}

.transit-score {
    display: flex;
    align-items: center;
    gap: 8px;
}

.transit-quads {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 12px;
}

.transit-quad {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    transition: all 0.2s ease;
}

.transit-quad:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.quad-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
}

.quad-header i {
    font-size: 1.2rem;
    width: 24px;
    text-align: center;
}

.quad-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: #374151;
}

.time-item {
  display: grid;
  grid-template-columns: 28px 1fr;   /* fixed icon column + flexible text */
  align-items: center;
  background: #f8fafc;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 0.9rem;
  font-weight: 600;
}

/* Public Transit Information Styles */
.public-transit-info {
  margin-top: 16px;
  padding: 16px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.public-transit-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #000000;
}

.public-transit-header i {
  font-size: 1.1rem;
}

.nearest-stop {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 10px;
  background: #fafafa;           /* subtle background */
  border-radius: 10px;           /* soft rounding */
  padding: 6px 10px;             /* internal breathing room */
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);  /* depth without heaviness */
}

.stop-label {
  color: #6b7280;
  font-weight: 500;
}

.stop-name {
  font-weight: 600;
  color: #111827;
}

.walk-time {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.85rem;
  color: #059669; /* Tailwind's emerald-600 for readability */
  margin-left: auto; /* aligns it neatly to right edge on larger cards */
}

.walk-time i {
  font-size: 0.9rem;
  color: #10b981;
}

.bus-times-header {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.bus-times-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bus-time-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  font-size: 0.85rem;
  font-weight: 500;
  color: #374151;
}

.bus-time-item i {
  font-size: 1rem;
  width: 16px;
  text-align: center;
  color: #1f2937;
  min-height: 44px;
  line-height: 1.2;
  width: 100%;
  box-sizing: border-box;
}

.time-item i {
  font-size: 1.1rem;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.time-item span {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
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
  text-align: left;
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
    .info-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }

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
        flex-direction: column;
        gap: 8px;
    }

    .popup-title {
        font-size: 0.9rem;
        font-weight: 500; /* Consistent weight for all parts */
        text-align: left;
        white-space: nowrap; /* Keep address on one line */
        overflow: hidden;
        text-overflow: ellipsis;
        text-transform: capitalize; /* Fix all caps issue */
    }
    
    .popup-title span {
        font-weight: 500; /* Fix weird city sizing */
        text-transform: capitalize; /* Fix all caps issue */
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

    .info-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        margin: 1rem 0;
    }

    .info-column {
        display: flex;
        flex-direction: column;
    }

    .section-header {
        margin: 0 0 15px 0;
        padding: 8px 0;
        border-bottom: 2px solid #e5e7eb;
    }

    .section-header h4 {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
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

    .property-size {
        padding: 12px 0;
    }

    .property-size-header {
        margin-bottom: 10px;
    }

    .property-size-header strong {
        font-size: 1rem;
    }

    .details-grid {
        gap: 10px;
    }

    .detail-card {
        padding: 12px;
        gap: 10px;
    }

    .detail-icon {
        width: 28px;
        height: 28px;
        font-size: 1rem;
    }

    .detail-number {
        font-size: 1.2rem;
    }

    .detail-label {
        font-size: 0.8rem;
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
    .popup-amenities,
    .popup-transit,
    .popup-landlord {
        font-size: 0.95rem;
        margin-top: 12px; /* Proper spacing between address and landlord */
    }
    
    /* Fix landlord section centering on mobile */
    .popup-landlord {
        left: 0;
        width: 100%;
        max-width: 100%;
    }
    
    
    .landlord-oneline {
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
    }

    .popup-title-row {
        gap: 8px;
    }

    .description-header {
        margin-bottom: 6px;
    }

    .description-header strong {
        font-size: 1rem;
    }

    .description-content {
        font-size: 0.9rem;
    }

    .transit-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }

    .amenities-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }

    .amenities-score {
        align-self: stretch;
    }

    .score-visual {
        justify-content: space-between;
        width: 100%;
    }

    .score-bar {
        width: 50px;
        height: 5px;
    }

    .score-text {
        font-size: 0.8rem;
    }

    .amenities-categories {
        grid-template-columns: 1fr;
        gap: 12px;
    }

    .amenity-category {
        gap: 6px;
        padding: 10px;
    }

    .category-header {
        gap: 6px;
    }

    .category-icon {
        font-size: 1rem;
        width: 18px;
    }

    .category-name {
        font-size: 0.9rem;
    }

    .amenity-pills {
        margin-left: 0;
        gap: 4px;
    }

    .amenity-pill {
        font-size: 0.8rem;
        padding: 3px 8px;
    }

    .transit-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }

    .transit-score {
        align-self: stretch;
    }

    .transit-quads {
        grid-template-columns: 1fr;
        gap: 10px;
    }

    .transit-quad {
        padding: 10px;
    }

    .quad-header i {
        font-size: 1.1rem;
        width: 20px;
    }

    .quad-name {
        font-size: 0.85rem;
    }

    .quad-times {
        gap: 4px;
    }

    .time-item {
        font-size: 0.85rem;
        padding: 8px 10px;
        gap: 10px;
        min-height: 40px;
        line-height: 1.2;
    }

    .time-item i {
        font-size: 1rem;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .time-item span {
        display: flex;
        align-items: center;
        height: 100%;
        font-size: 0.85rem;
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

/* Mobile responsive styles for property details */
@media (max-width: 768px) {
    .info-grid {
        grid-template-columns: 1fr !important;
        gap: 8px;
    }
    
    .property-details {
        padding: 8px 0;
        margin-top: 8px;
        margin-bottom: 8px;
    }

    .property-details-header {
        margin-bottom: 6px;
    }

    .property-details-header strong {
        font-size: 0.95rem;
    }
    
    .info-card {
        padding: 12px;
        gap: 10px;
        min-height: 60px;
    }
    
    .info-icon {
        width: 24px;
        height: 24px;
        font-size: 0.8rem;
    }
    
    .info-label {
        font-size: 0.7rem;
    }
    
    .info-value {
        font-size: 0.75rem;
    }
    
    .section-title {
        font-size: 0.8rem;
        margin-bottom: 10px;
    }
    
    .property-section {
        margin-bottom: 16px;
  }
}


</style>