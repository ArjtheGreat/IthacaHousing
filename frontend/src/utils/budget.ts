/**
 * Budget filter for the Fair Rent Map: keeps listings whose rent per person
 * fits under a monthly cap. Runs on the client over /listings-minimal data.
 */

import type { MapListing } from './complexes';

/**
 * Per-person monthly caps offered in the Budget dropdown. Picked from the
 * /listings-minimal distribution (median rent per person is about $1,200):
 * the caps keep roughly 20%, 40%, 55%, 70% and 90% of priced listings.
 */
export const BUDGET_OPTIONS = [800, 1000, 1200, 1500, 2000];

/** Dropdown label for a cap, e.g. 1000 -> "≤ $1,000 / person". */
export function budgetLabel(budget: number): string {
    return `≤ $${budget.toLocaleString('en-US')} / person`;
}

/**
 * Keeps listings with rent_per_person <= budget. A budget of 0 (or less) means
 * "Any" and returns every listing. Once a budget is set, listings with a missing
 * or zero rent are dropped, since we can't tell whether they fit.
 */
export function filterByBudget<T extends Pick<MapListing, 'rent_per_person'>>(listings: T[], budget: number): T[] {
    if (!budget || budget <= 0) return listings;
    return listings.filter(listing => {
        const rent = listing.rent_per_person;
        return rent !== null && rent !== undefined && rent > 0 && rent <= budget;
    });
}
