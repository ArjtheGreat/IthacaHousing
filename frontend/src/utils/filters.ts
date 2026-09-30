/**
 * Filter logic for the Fair Rent Map.
 * Every active filter is the list of listings it lets through; the map shows their intersection.
 * Everything here works over whatever keys `activeFilters` has, so a new filter needs no changes.
 */

export interface Identified {
  listingid: string | number
}

/** activeFilters in MapView: filter key -> matching listings, or null when the filter is off. */
export type ActiveFilters = Record<string, Identified[] | null | undefined>

/** Listings in `all` that pass every active filter. */
export function mergeActiveFilters<T extends Identified>(all: T[], filters: ActiveFilters): T[] {
  let merged = all
  for (const matches of Object.values(filters)) {
    if (!matches) continue
    const ids = new Set(matches.map((l) => l.listingid))
    merged = merged.filter((l) => ids.has(l.listingid))
  }
  return merged
}

/** Keys of the filters that are currently on, in activeFilters order. */
export function activeFilterKeys(filters: ActiveFilters): string[] {
  return Object.keys(filters).filter((key) => filters[key])
}

const FILTER_LABELS: Record<string, string> = {
  beds: 'Beds',
  baths: 'Baths',
  location: 'Neighborhood',
  commute: 'Commute',
  walk: 'Walk',
  transit: 'TCAT',
  pets: 'Pets',
  roomtorent: 'Room to rent',
  rent: 'Rent',
  shared: 'Shared',
}

/** Human name for a filter key; unknown keys fall back to the capitalized key. */
export function filterLabel(key: string): string {
  return FILTER_LABELS[key] ?? key.charAt(0).toUpperCase() + key.slice(1)
}
