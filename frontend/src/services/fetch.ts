import axios, { type AxiosResponse } from "axios";
import { type Listing, type HeatmapData } from "@/services/interface"

const baseURL = import.meta.env.VITE_API_URL;

/**
 * Fetches listings from PostgreSQL Database
 * @returns Listing[] with all the listings
 */
export const fetchListings = async (): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listings/`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};

/**
 * Fetches minimal listing data for map display - only essential fields
 * @returns Minimal listing data with only latitude, longitude, rent_per_person, rentamount, predictedrent
 */
export const fetchListingsMinimal = async (): Promise<any[]> => {
    try {
        const response: AxiosResponse<any[]> = await axios.get(`${baseURL}/listings-minimal/`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching minimal listings:", error);
        return []; 
    }
};


/**
 * Fetches listing with specific ID from PostgreSQL Database
 * @returns Listing with that listing id
 */
export const fetchListing = async (listing_id: Number): Promise<Listing | null> => {
    try {
        const response: AxiosResponse<Listing> = await axios.get(`${baseURL}/listing/${listing_id}`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return null; 
    }
};


/**
 * Fetches top ten listings from PostgreSQL Database
 * @returns Listing[] with the top ten listings
 */
export const fetchTopTenListings = async (): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/top-ten-listings/`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};

/**
 * Fetches bottom ten listings from PostgreSQL Database
 * @returns Listing[] with bottom ten listings
 */
export const fetchBottomTenListings = async (): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/bottom-ten-listings/`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};


/**
 * Fetches clusters from PostgreSQL Database
 * @returns Listing[] with all the listings, clustered
 */
export const fetchClusters = async (): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/clusters/`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};


/**
 * Fetches heatmap from PostgreSQL Database
 * @returns Heatmap data
 */
export const fetchHeatMap = async (): Promise<Number[][]> => {
    try {
        const response: AxiosResponse<HeatmapData> = await axios.get(`${baseURL}/heatmap/`);
        if (response.status === 200) {
            return response.data.heat_data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};

/**
 * Fetches Voronoi Polygons from PostgreSQL Database
 * @returns Voronoi data
 */
export const fetchVoronoiPolygons = async (): Promise<Number[][]> => {
    try {
        const response: AxiosResponse<HeatmapData> = await axios.get(`${baseURL}/voronoi/`);
        if (response.status === 200) {
            return response.data.heat_data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};

/**
 * Fetches Bed Filter
 * @param n_beds - The number of beds to filter
 * @returns Bed data
 */
export const fetchBedFilter = async (n_beds: Number): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listing/beds/${n_beds}`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};

/**
 * Fetches bath Filter
 * @param n_baths - The number of baths to filter
 * @returns bath data
 */
export const fetchBathFilter = async (n_baths: Number): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listing/baths/${n_baths}`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};


/**
 * Fetches walk Filter
 * @returns walking data
 */
export const fetchWalkFilter = async (): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listing/walks`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};


/**
 * Fetches transit Filter
 * @returns transit data
 */
export const fetchTransitFilter = async (): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listing/transit`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};

/**
 * Fetches pets Filter
 * @returns pets data
 */
export const fetchPetsFilter = async (): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listing/pets`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return []; 
    }
};


/**
 * Fetches Room to Rent Listings
 * @returns room-to-rent listing data
 */
export const fetchRoomToRentListings = async (): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/room-to-rent-listings/`);
        if (response.status === 200) {
            return response.data;
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching room-to-rent listings:", error);
        return [];
    }
};

/**
 * Fetches Rent Listings
 * @returns rent listing data
 */
export const fetchRentListings = async (): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/rent-listings/`);
        if (response.status === 200) {
            return response.data;
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching rent listings:", error);
        return [];
    }
};

/**
 * Fetches Shared Listings
 * @returns shared listing data
 */
export const fetchSharedListings = async (): Promise<Listing[]> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/shared-listings/`);
        if (response.status === 200) {
            return response.data;
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching shared listings:", error);
        return [];
    }
};


/**
 * Fetches vacant lot parcels
 * @returns vacant lot GeoJSON-like data
 */
export const fetchVacantLots = async (): Promise<any[]> => {
    try {
        const response: AxiosResponse<any[]> = await axios.get(`${baseURL}/vacant-lots`);
        if (response.status === 200) {
        return response.data;
        } else {
        throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching vacant lots:", error);
        return [];
    }
};

/**
 * Fetches vacant lot parcels
 * @returns vacant lot GeoJSON-like data
 */
export const fetchLots = async (): Promise<any[]> => {
    try {
        const response: AxiosResponse<any[]> = await axios.get(`${baseURL}/all-lots`);
        if (response.status === 200) {
        return response.data;
        } else {
        throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching vacant lots:", error);
        return [];
    }
};



