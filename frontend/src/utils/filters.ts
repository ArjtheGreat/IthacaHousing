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

/**
 * A filter that can be loosened one notch at a time instead of dropped,
 * e.g. the commute filter's max-time dropdown.
 */
export interface FilterStep {
  key: string // activeFilters entry this loosens
  options: number[] // looser values to try, in order (only the ones above the current value)
  listingsAt: (value: number) => Identified[] // what the filter would let through at that value
}

export type RelaxSuggestion =
  | { kind: 'step'; key: string; value: number; count: number } // loosen `key` to `value`
  | { kind: 'drop'; key: string; count: number } // turn `key` off

/**
 * The smallest change to the active filters that gets at least one listing back.
 * Loosening a step filter beats dropping any filter, and a smaller notch beats a bigger one.
 * Otherwise drop one filter at a time (leave-one-out) and keep the drop that shows the most listings.
 * Returns null when no single change helps; the caller should offer to reset everything.
 */
export function relaxSuggestion(
  all: Identified[],
  filters: ActiveFilters,
  steps: FilterStep[] = [],
): RelaxSuggestion | null {
  const keys = activeFilterKeys(filters)

  let best: { notch: number; suggestion: RelaxSuggestion } | null = null
  for (const step of steps) {
    if (!keys.includes(step.key)) continue
    for (let notch = 0; notch < step.options.length; notch++) {
      if (best && notch >= best.notch) break
      const value = step.options[notch]
      const count = mergeActiveFilters(all, { ...filters, [step.key]: step.listingsAt(value) }).length
      if (count > 0) {
        best = { notch, suggestion: { kind: 'step', key: step.key, value, count } }
        break
      }
    }
  }
  if (best) return best.suggestion

  let drop: RelaxSuggestion | null = null
  for (const key of keys) {
    const count = mergeActiveFilters(all, { ...filters, [key]: null }).length
    if (count > (drop?.count ?? 0)) drop = { kind: 'drop', key, count }
  }
  return drop
}
