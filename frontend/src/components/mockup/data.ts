/**
 * Data for the /rent-preview design walkthrough.
 *
 * The listings are a snapshot of the production /listings-minimal endpoint (taken 2026-09-30)
 * so the mockup shows real addresses, rents and walk times without calling the API.
 */
import snapshot from '@/assets/mockup/listings-snapshot.json';
import { valueScore } from '@/utils/complexes';

export type Quad = 'engineeringquad' | 'artsquad' | 'agriculturequad';

export interface SnapshotListing {
    listingid: string;
    listingaddress: string;
    latitude: number;
    longitude: number;
    rent_per_person: number | null;
    available_bedrooms: number | null;
    predictedrent: number | null;
    walk_time_engineeringquad: number | null;
    walk_time_artsquad: number | null;
    walk_time_agriculturequad: number | null;
    bike_time_engineeringquad: number | null;
    /** Lets the snapshot rows pass as the map's MapListing shape. */
    [key: string]: unknown;
}

export interface Criteria {
    beds: number;
    /** Max rent per person, dollars per month. */
    budget: number;
    quad: Quad;
    /** Max walk to the quad, minutes. */
    maxWalk: number;
}

export interface RankedListing extends SnapshotListing {
    rank: number;
    walk: number;
    /** Percent of asking rent that the fair-rent estimate sits under (positive) or over (negative). */
    percent: number | null;
    /** One line explaining why it ranks where it does. */
    reason: string;
    /** Paid placement slot (the monetization hook from the review). */
    featured?: boolean;
}

export const QUAD_LABEL: Record<Quad, string> = {
    engineeringquad: 'Eng Quad',
    artsquad: 'Arts Quad',
    agriculturequad: 'Ag Quad',
};

export const listings = snapshot as SnapshotListing[];

/** The student whose search the walkthrough follows. */
export const persona = {
    name: 'Retep',
    query: "I'm Retep, a beer student at Cornell. I'm moving in with my 5 family members, we can do about $1,000 each, and I want to walk to class.",
    criteria: { beds: 6, budget: 1000, quad: 'agriculturequad', maxWalk: 25 } as Criteria,
};

/** The stricter version Retep tries later, which matches nothing. */
export const tooStrictCriteria: Criteria = { ...persona.criteria, maxWalk: 10 };

/** Rents below this are treated as bad data (a room listed at $230 is not a real per-person price). */
const MIN_PLAUSIBLE_RENT = 400;

export function walkTo(listing: SnapshotListing, quad: Quad): number | null {
    return listing[`walk_time_${quad}`];
}

export function matchListings(criteria: Criteria, pool: SnapshotListing[] = listings): SnapshotListing[] {
    return pool.filter(l => {
        const rent = l.rent_per_person ?? 0;
        const walk = walkTo(l, criteria.quad);
        return l.available_bedrooms === criteria.beds
            && rent >= MIN_PLAUSIBLE_RENT && rent <= criteria.budget
            && walk !== null && walk <= criteria.maxWalk;
    });
}

/** Lower is better: minutes of walking, with up to ±3 minutes of credit for being under/over fair rent. */
function score(listing: SnapshotListing, quad: Quad): number {
    const walk = walkTo(listing, quad) ?? 99;
    const value = Math.max(-0.3, Math.min(0.3, valueScore(listing) ?? 0));
    return walk - 10 * value;
}

/** One listing per building (the cheapest), ranked. */
export function rankListings(criteria: Criteria, limit = 8): RankedListing[] {
    const cheapestByAddress = new Map<string, SnapshotListing>();
    for (const l of matchListings(criteria)) {
        const current = cheapestByAddress.get(l.listingaddress);
        if (!current || (l.rent_per_person ?? 0) < (current.rent_per_person ?? 0)) {
            cheapestByAddress.set(l.listingaddress, l);
        }
    }
    return [...cheapestByAddress.values()]
        .sort((a, b) => score(a, criteria.quad) - score(b, criteria.quad))
        .slice(0, limit)
        .map((l, i) => {
            const walk = walkTo(l, criteria.quad) ?? 0;
            // Same formula as RentalSidebar.vue: the gap as a share of what the landlord asks.
            const percent = l.predictedrent && l.rent_per_person
                ? Math.round(((l.predictedrent - l.rent_per_person) / l.rent_per_person) * 100) : null;
            const valueText = percent === null ? 'no fair-rent estimate'
                : percent >= 0 ? `${percent}% under fair rent` : `${-percent}% over fair rent`;
            return {
                ...l, rank: i + 1, walk, percent,
                reason: `${Math.round(walk)} min walk to ${QUAD_LABEL[criteria.quad]} · ${valueText}`,
                featured: i === 2,
            };
        });
}

export interface RelaxSuggestion {
    maxWalk: number;
    count: number;
}

/** The smallest walk limit (in 5-minute steps) that would give Retep at least one result. */
export function relaxSuggestion(criteria: Criteria): RelaxSuggestion | null {
    for (let maxWalk = criteria.maxWalk + 5; maxWalk <= 45; maxWalk += 5) {
        const count = matchListings({ ...criteria, maxWalk }).length;
        if (count > 0) return { maxWalk, count };
    }
    return null;
}

export interface Chip {
    icon: string;
    label: string;
}

/** How the search bar shows what it understood from the sentence. */
export function chipsFor(criteria: Criteria): Chip[] {
    return [
        { icon: 'fa-bed', label: `${criteria.beds} bedrooms` },
        { icon: 'fa-dollar-sign', label: `≤ $${criteria.budget} per person` },
        { icon: 'fa-person-walking', label: `≤ ${criteria.maxWalk} min walk to ${QUAD_LABEL[criteria.quad]}` },
    ];
}

/** Illustrative TCAT stops around campus and Collegetown. Positions are approximate. */
export const busStops: { name: string; lat: number; lng: number }[] = [
    { name: 'College Ave @ Dryden Rd', lat: 42.4418, lng: -76.4852 },
    { name: 'Schwartz Center', lat: 42.4427, lng: -76.4858 },
    { name: 'Eddy St @ Dryden Rd', lat: 42.4409, lng: -76.4869 },
    { name: 'Stewart Ave @ University Ave', lat: 42.4461, lng: -76.4914 },
    { name: 'Seneca St @ Aurora St', lat: 42.4399, lng: -76.4976 },
    { name: 'Maple Ave @ Mitchell St', lat: 42.4401, lng: -76.4721 },
    { name: 'Sage Hall', lat: 42.4455, lng: -76.4831 },
    { name: 'Dairy Bar', lat: 42.4476, lng: -76.4751 },
];
