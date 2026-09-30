/**
 * Groups listings that belong to the same building ("complex") so the map can
 * draw one marker per building instead of one dot per unit.
 */

export interface MapListing {
    listingid: string | number;
    listingaddress: string;
    listingcity?: string;
    latitude: number;
    longitude: number;
    rent_per_person: number | null;
    predictedrent: number | null;
    available_bedrooms?: number | null;
    [key: string]: unknown;
}

export type Bucket = 'under' | 'fair' | 'over';

export interface Complex<T extends MapListing = MapListing> {
    id: string;
    lat: number;
    lng: number;
    address: string;
    units: T[];
    count: number;
    minRent: number | null;
    maxRent: number | null;
    medianRent: number | null;
    /** Median of valueScore across priced units; null when no unit has a usable rent. */
    medianScore: number | null;
    buckets: Record<Bucket, number>;
    /** Units with a missing or zero rent. They are listed but left out of every stat. */
    unpriced: number;
}

/** Color for listings whose rent is missing or zero. */
export const UNPRICED_COLOR = '#9ca3af';
export const BUCKET_COLORS: Record<Bucket, string> = { under: '#1a9850', fair: '#fee08b', over: '#d73027' };
/** A unit within ±5% of its predicted rent counts as fairly priced. */
const FAIR_BAND = 0.05;
/** Two groups with the same normalized address merge only if they are this close (meters). */
const SAME_BUILDING_METERS = 50;

// Helper function to interpolate between two hex colors
export function interpolateColor(color1: string, color2: string, factor: number): string {
    const hex1 = color1.replace('#', '');
    const hex2 = color2.replace('#', '');

    const r1 = parseInt(hex1.substr(0, 2), 16);
    const g1 = parseInt(hex1.substr(2, 2), 16);
    const b1 = parseInt(hex1.substr(4, 2), 16);

    const r2 = parseInt(hex2.substr(0, 2), 16);
    const g2 = parseInt(hex2.substr(2, 2), 16);
    const b2 = parseInt(hex2.substr(4, 2), 16);

    const r = Math.round(r1 + (r2 - r1) * factor);
    const g = Math.round(g1 + (g2 - g1) * factor);
    const b = Math.round(b1 + (b2 - b1) * factor);

    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

/**
 * How far below (+) or above (-) its predicted rent a listing is, as a fraction of actual rent.
 * Returns null when rent is missing or zero, so callers never divide by zero.
 */
export function valueScore(listing: Pick<MapListing, 'rent_per_person' | 'predictedrent'>): number | null {
    const rent = listing.rent_per_person;
    const predicted = listing.predictedrent;
    if (!rent || !(rent > 0) || !predicted || isNaN(predicted)) return null;
    return (predicted - rent) / rent;
}

/** Red (#d73027) -> Yellow (#fee08b) -> Green (#1a9850) over a score of -0.2 to 0.2. */
export function colorForScore(score: number | null): string {
    if (score === null || isNaN(score)) return UNPRICED_COLOR;
    const clamped = Math.max(-0.2, Math.min(0.2, score));
    const normalized = (clamped + 0.2) / 0.4;
    if (normalized <= 0.5) {
        return interpolateColor('#d73027', '#fee08b', normalized * 2);
    }
    return interpolateColor('#fee08b', '#1a9850', (normalized - 0.5) * 2);
}

/**
 * Gets the color of the dot based on price
 * @param rent - Actual rent
 * @param predicted - Predicted rent
 */
export function getColor(rent: number | null, predicted: number | null): string {
    return colorForScore(valueScore({ rent_per_person: rent, predictedrent: predicted }));
}

export function bucketForScore(score: number): Bucket {
    if (score > FAIR_BAND) return 'under';
    if (score < -FAIR_BAND) return 'over';
    return 'fair';
}

const SUFFIXES: Record<string, string> = {
    street: 'st', avenue: 'ave', road: 'rd', place: 'pl', drive: 'dr', lane: 'ln',
    court: 'ct', circle: 'cir', boulevard: 'blvd', terrace: 'ter',
};
const DIRECTIONS: Record<string, string> = { north: 'n', south: 's', east: 'e', west: 'w' };
const SUFFIX_TOKENS = new Set(Object.values(SUFFIXES));
const DIRECTION_TOKENS = new Set(Object.values(DIRECTIONS));

/**
 * Reduces an address to house number + street name + direction so different spellings of one
 * building compare equal: "815 S AURORA" and "815 AURORA ST S" both become "815 aurora s".
 * Unit markers ("#3", "Apt. C", "(BLDG. B)") are dropped.
 */
export function normalizeAddress(raw: string | null | undefined): string {
    const base = String(raw ?? '').toLowerCase().split(/\s*(?:,|#|\bapt\b|\bunit\b|\bsuite\b|\()/)[0];
    const tokens = base.replace(/\./g, '').split(/\s+/).filter(Boolean)
        .map(t => SUFFIXES[t] || DIRECTIONS[t] || t);
    const houseNumber = tokens.shift() ?? '';
    const directions = tokens.filter(t => DIRECTION_TOKENS.has(t));
    const words = tokens.filter(t => !DIRECTION_TOKENS.has(t) && !SUFFIX_TOKENS.has(t));
    return [houseNumber, ...words, ...directions].join(' ');
}

export function median(values: number[]): number | null {
    if (values.length === 0) return null;
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function metersBetween(a: MapListing, b: MapListing): number {
    const dLat = (a.latitude - b.latitude) * 111000;
    const dLng = (a.longitude - b.longitude) * 111000 * Math.cos((a.latitude * Math.PI) / 180);
    return Math.hypot(dLat, dLng);
}

function buildComplex<T extends MapListing>(units: T[]): Complex<T> {
    const lat = units.reduce((sum, u) => sum + u.latitude, 0) / units.length;
    const lng = units.reduce((sum, u) => sum + u.longitude, 0) / units.length;

    const rents = units.map(u => u.rent_per_person).filter((r): r is number => !!r && r > 0);
    const scores = units.map(valueScore).filter((s): s is number => s !== null);
    const buckets: Record<Bucket, number> = { under: 0, fair: 0, over: 0 };
    scores.forEach(s => { buckets[bucketForScore(s)]++; });

    const address = units[0].listingaddress;
    return {
        id: `${normalizeAddress(address)}@${units[0].latitude.toFixed(4)},${units[0].longitude.toFixed(4)}`,
        lat, lng, address, units,
        count: units.length,
        minRent: rents.length ? Math.min(...rents) : null,
        maxRent: rents.length ? Math.max(...rents) : null,
        medianRent: median(rents),
        medianScore: median(scores),
        buckets,
        unpriced: units.length - scores.length,
    };
}

/**
 * One complex per building. Listings are grouped by exact coordinate, then:
 *  - a coordinate holding two different addresses (a geocoder collision) is split, and
 *  - nearby groups with the same normalized address (one building, two spellings) are merged.
 * A listing on its own comes back as a complex with count 1.
 */
export function groupIntoComplexes<T extends MapListing>(listings: T[]): Complex<T>[] {
    const byCoordAndAddress = new Map<string, T[]>();
    listings.forEach(listing => {
        const key = `${listing.latitude},${listing.longitude}|${normalizeAddress(listing.listingaddress)}`;
        const group = byCoordAndAddress.get(key);
        if (group) group.push(listing); else byCoordAndAddress.set(key, [listing]);
    });

    const merged: T[][] = [];
    byCoordAndAddress.forEach(group => {
        const address = normalizeAddress(group[0].listingaddress);
        const match = merged.find(m =>
            normalizeAddress(m[0].listingaddress) === address && metersBetween(m[0], group[0]) < SAME_BUILDING_METERS);
        if (match) match.push(...group); else merged.push([...group]);
    });

    return spreadCollisions(merged.map(buildComplex));
}

/** Complexes that land on the exact same point are nudged ~9 m apart so both stay clickable. */
function spreadCollisions<T extends MapListing>(complexes: Complex<T>[]): Complex<T>[] {
    const byPoint = new Map<string, Complex<T>[]>();
    complexes.forEach(c => {
        const key = `${c.lat},${c.lng}`;
        const group = byPoint.get(key);
        if (group) group.push(c); else byPoint.set(key, [c]);
    });
    byPoint.forEach(group => {
        if (group.length < 2) return;
        const radius = 0.00008;
        group.forEach((c, index) => {
            const angle = (2 * Math.PI * index) / group.length;
            c.lat += Math.cos(angle) * radius;
            c.lng += Math.sin(angle) * radius;
        });
    });
    return complexes;
}

/** Best deals first; units without a usable rent go last. */
export function sortByValue<T extends MapListing>(units: T[]): T[] {
    return [...units].sort((a, b) => (valueScore(b) ?? -Infinity) - (valueScore(a) ?? -Infinity));
}

export function titleCase(text: string | null | undefined): string {
    return String(text ?? '').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
}
