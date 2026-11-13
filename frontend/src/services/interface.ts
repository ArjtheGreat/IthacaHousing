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
    ward?: string | null;
    in_business_improvement_district?: boolean | null;
    nearest_stop_name: string;
    walk_time_to_nearest_stop: number;
    transit_score: number;
    transit_time_to_ag_quad: number;
    transit_time_to_arts_quad: number;
    transit_time_to_eng_quad: number;
    water: string;
    sewer: string;
    yr_built: number;
    year_built_source?: string | null;
    parcel_printkey?: string | null;
    parcel_match_method?: string | null;
    assessment_total_value?: number | null;
    assessment_land_value?: number | null;
    assessment_stories?: number | null;
    assessment_zoning?: string | null;
    assessment_property_class?: string | null;
    sqft_per_sale_price: number;
    housingtype?: string;
    renttype?: string;
    dateavailable?: string;
    lengthavailable?: number;
    listingtypes?: string | string[];
    listingexpirationdate?: string;
    
}

export interface HeatmapData {
    heat_data: number[][];
}
