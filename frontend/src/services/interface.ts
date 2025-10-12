/**
 * Interface for Housing Listing
 */
export interface Listing {
    id: number;
    address: string;
    price: number;
    available_bedrooms: number;
    available_bathrooms: number;
    latitude: number;
    longitude: number;
    listingphotos: String;
    differenceInFairValue: number;
    listingaddress: Text;
    amenities_score: number,
    walk_time: number;
    rentamount: number;
    rent_per_person: number;
    num_people: number;
    owner_name: string;
    neighborhood: string;
    nearest_stop_name: string;
    walk_time_to_nearest_stop: number;
    transit_score: number;
    transit_time_to_ag_quad: number;
    transit_time_to_arts_quad: number;
    transit_time_to_eng_quad: number;
    
}

export interface HeatmapData {
    heat_data: number[][];
}
