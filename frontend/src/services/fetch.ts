import axios, { type AxiosResponse } from "axios";
import { type Listing, type HeatmapData } from "@/services/interface"

const baseURL = import.meta.env.VITE_API_URL;

/**
 * What a filter fetch returns when it fails.
 * The API answers 404 when nothing matches, which is a real (empty) result;
 * anything else means we don't know, so return null and let the caller keep the filter off.
 */
const filterFailure = (error: unknown): Listing[] | null => {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
        return [];
    }
    return null;
};

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
export const fetchListing = async (listing_id: string | number): Promise<Listing | null> => {
    try {
        const response: AxiosResponse<Listing> = await axios.get(
            `${baseURL}/listing/${encodeURIComponent(String(listing_id))}`
        );
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listing:", error);
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
export const fetchBedFilter = async (n_beds: Number): Promise<Listing[] | null> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listing/beds/${n_beds}`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return filterFailure(error); 
    }
};

/**
 * Fetches bath Filter
 * @param n_baths - The number of baths to filter
 * @returns bath data
 */
export const fetchBathFilter = async (n_baths: Number): Promise<Listing[] | null> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listing/baths/${n_baths}`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return filterFailure(error); 
    }
};


/**
 * Fetches walk Filter
 * @returns walking data
 */
export const fetchWalkFilter = async (): Promise<Listing[] | null> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listing/walks`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return filterFailure(error); 
    }
};


/**
 * Fetches transit Filter
 * @returns transit data
 */
export const fetchTransitFilter = async (): Promise<Listing[] | null> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listing/transit`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return filterFailure(error); 
    }
};

/**
 * Fetches pets Filter
 * @returns pets data
 */
export const fetchPetsFilter = async (): Promise<Listing[] | null> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/listing/pets`);
        if (response.status === 200) {
            return response.data; 
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching listings:", error);
        return filterFailure(error); 
    }
};


/**
 * Fetches Room to Rent Listings
 * @returns room-to-rent listing data
 */
export const fetchRoomToRentListings = async (): Promise<Listing[] | null> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/room-to-rent-listings/`);
        if (response.status === 200) {
            return response.data;
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching room-to-rent listings:", error);
        return filterFailure(error);
    }
};

/**
 * Fetches Rent Listings
 * @returns rent listing data
 */
export const fetchRentListings = async (): Promise<Listing[] | null> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/rent-listings/`);
        if (response.status === 200) {
            return response.data;
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching rent listings:", error);
        return filterFailure(error);
    }
};

/**
 * Fetches Shared Listings
 * @returns shared listing data
 */
export const fetchSharedListings = async (): Promise<Listing[] | null> => {
    try {
        const response: AxiosResponse<Listing[]> = await axios.get(`${baseURL}/shared-listings/`);
        if (response.status === 200) {
            return response.data;
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching shared listings:", error);
        return filterFailure(error);
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

/**
 * Fetches latest pipeline metrics from rental_model_runs table
 * @returns Latest pipeline metrics data
 */
export const fetchPipelineMetrics = async (): Promise<any> => {
    try {
        const response: AxiosResponse<any> = await axios.get(`${baseURL}/pipeline-metrics/`);
        if (response.status === 200) {
            return response.data;
        } else {
            throw new Error(`Unexpected status code: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching pipeline metrics:", error);
        return null;
    }
};




export interface AssistantFilters {
    beds: number | null;
    baths: number | null;
    budget: number | null;
    commute: { destination: string; mode: string; max_time: number } | null;
}

export interface AssistantRecommendation {
    listingid: string;
    address: string;
    rent_per_person: number | null;
    beds: number | null;
    baths: number | null;
    reason: string;
}

export interface AssistantResponse {
    reply: string;
    remaining?: number;
    filters: AssistantFilters | null;
    recommendations: AssistantRecommendation[];
}

export interface AssistantPreferences {
    text: string;
    schematic: string;
    updated_at: string | null;
}

export interface AssistantAccount {
    email: string | null;
    limit: number;
    remaining: number;
    preferences_remaining: number;
    preferences: AssistantPreferences | null;
}

function assistantError(error: unknown, fallback: string): Error {
    const detail = axios.isAxiosError(error) ? error.response?.data?.detail : null;
    const err = new Error(typeof detail === 'string' ? detail : fallback) as Error & { status?: number };
    if (axios.isAxiosError(error)) err.status = error.response?.status;
    return err;
}

const authHeader = (token: string) => ({ Authorization: `Bearer ${token}` });

/**
 * Asks the listing assistant (Claude, via the backend) to set filters and recommend listings
 * @param messages - The chat so far, ending with the user's newest message
 * @param currentFilters - What the Personal Preferences panel has set right now
 * @param token - The signed-in user's Supabase access token
 */
export const fetchAssistantRecommendations = async (
    messages: { role: 'user' | 'assistant'; content: string }[],
    currentFilters: Record<string, string | number | null>,
    token: string,
): Promise<AssistantResponse> => {
    try {
        const response: AxiosResponse<AssistantResponse> = await axios.post(
            `${baseURL}/assistant/recommend`,
            { messages, current_filters: currentFilters },
            { timeout: 120_000, headers: authHeader(token) },
        );
        return response.data;
    } catch (error) {
        throw assistantError(error, "Couldn't reach the assistant. Try again.");
    }
};

/** Who's signed in, how many assistant requests they have left today, and their saved preferences */
export const fetchAssistantAccount = async (token: string): Promise<AssistantAccount> => {
    try {
        const response = await axios.get<AssistantAccount>(`${baseURL}/assistant/me`, { headers: authHeader(token) });
        return response.data;
    } catch (error) {
        throw assistantError(error, "Couldn't load your account. Try again.");
    }
};

/** Saves what the user is looking for; the backend turns it into a compact preference string */
export const saveAssistantPreferences = async (
    text: string,
    token: string,
): Promise<{ preferences: AssistantPreferences; preferences_remaining: number }> => {
    try {
        const response = await axios.put(`${baseURL}/assistant/preferences`, { text }, { timeout: 60_000, headers: authHeader(token) });
        return response.data;
    } catch (error) {
        throw assistantError(error, "Couldn't save your preferences. Try again.");
    }
};

export const deleteAssistantPreferences = async (token: string): Promise<void> => {
    try {
        await axios.delete(`${baseURL}/assistant/preferences`, { headers: authHeader(token) });
    } catch (error) {
        throw assistantError(error, "Couldn't clear your preferences. Try again.");
    }
};
