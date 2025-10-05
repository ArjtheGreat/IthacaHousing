/**
 * Interface for Housing Listing
 */
export interface Listing {
    id: number;
    address: string;
    price: number;
    bedrooms: number;
    bathrooms: number;
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
    
}

export interface HeatmapData {
    heat_data: number[][];
}
