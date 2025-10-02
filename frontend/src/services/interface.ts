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
    rentAmountAdjusted: number;
    listingaddress: Text;
    rent_per_person: number;
    num_people: number;
    
}

export interface HeatmapData {
    heat_data: number[][];
}
