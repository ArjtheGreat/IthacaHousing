import { describe, it, expect } from 'vitest'
import {
  mergeActiveFilters, activeFilterKeys, filterLabel, relaxSuggestion,
  type ActiveFilters, type FilterStep,
} from '../filters'

interface TestListing {
  listingid: string
  beds: number
  commute: number
}

// Ten listings: a-j, beds 1-5 twice over, commute 5, 10, ... 50 minutes.
const all: TestListing[] = Array.from({ length: 10 }, (_, i) => ({
  listingid: String.fromCharCode(97 + i),
  beds: (i % 5) + 1,
  commute: (i + 1) * 5,
}))

const withBeds = (n: number) => all.filter((l) => l.beds === n)
const withinMinutes = (max: number) => all.filter((l) => l.commute < max)
const ids = (listings: { listingid: string | number }[]) => listings.map((l) => l.listingid)

// The commute dropdown in MapView: 15, 20, 25, 30 minutes.
function commuteStep(current: number): FilterStep {
  return {
    key: 'commute',
    options: [15, 20, 25, 30].filter((t) => t > current),
    listingsAt: withinMinutes,
  }
}

describe('mergeActiveFilters', () => {
  it('returns everything when no filter is on', () => {
    expect(mergeActiveFilters(all, { beds: null, commute: null })).toHaveLength(10)
  })

  it('intersects every active filter', () => {
    const filters = { beds: withBeds(1), commute: withinMinutes(30) }
    // beds 1: a (5 min), f (30 min); only a is under 30
    expect(ids(mergeActiveFilters(all, filters))).toEqual(['a'])
  })

  it('treats an empty list as an active filter that matches nothing', () => {
    expect(mergeActiveFilters(all, { beds: [] })).toEqual([])
  })

  it('handles filter keys it has never seen', () => {
    const filters: ActiveFilters = { budget: all.slice(0, 3) }
    expect(ids(mergeActiveFilters(all, filters))).toEqual(['a', 'b', 'c'])
  })
})

describe('activeFilterKeys and filterLabel', () => {
  it('lists only the filters that are on', () => {
    expect(activeFilterKeys({ beds: withBeds(2), baths: null, commute: [] })).toEqual(['beds', 'commute'])
  })

  it('names known and unknown filters', () => {
    expect(filterLabel('beds')).toBe('Beds')
    expect(filterLabel('location')).toBe('Neighborhood')
    expect(filterLabel('budget')).toBe('Budget')
  })
})

describe('relaxSuggestion', () => {
  it('loosens the commute by the smallest notch that gives results', () => {
    // beds 3: c (15 min), h (40 min). Under 15 min finds nothing; under 20 finds c.
    const filters = { beds: withBeds(3), commute: withinMinutes(15) }
    expect(mergeActiveFilters(all, filters)).toEqual([])
    expect(relaxSuggestion(all, filters, [commuteStep(15)]))
      .toEqual({ kind: 'step', key: 'commute', value: 20, count: 1 })
  })

  it('prefers loosening the commute over dropping a filter', () => {
    // beds 4: d (20 min), i (45 min). Dropping beds would give more, but 25 min is the smaller change.
    const filters = { beds: withBeds(4), commute: withinMinutes(15) }
    expect(relaxSuggestion(all, filters, [commuteStep(15)]))
      .toEqual({ kind: 'step', key: 'commute', value: 25, count: 1 })
  })

  it('drops a filter when no commute notch is enough', () => {
    // beds 5 and baths f-j leave only j (50 min), beyond every notch in the dropdown.
    const filters = { beds: withBeds(5), baths: all.slice(5), commute: withinMinutes(15) }
    expect(relaxSuggestion(all, filters, [commuteStep(15)]))
      .toEqual({ kind: 'drop', key: 'commute', count: 1 })
  })

  it('keeps the drop that shows the most listings', () => {
    // Dropping beds leaves a; dropping baths leaves b, g.
    const filters = { beds: withBeds(2), baths: [all[0]] }
    expect(relaxSuggestion(all, filters)).toEqual({ kind: 'drop', key: 'baths', count: 2 })
  })

  it('breaks ties in activeFilters order', () => {
    // Dropping either leaves two listings.
    const filters = { beds: withBeds(1), baths: withBeds(2) }
    expect(relaxSuggestion(all, filters)).toEqual({ kind: 'drop', key: 'beds', count: 2 })
  })

  it('works for filters added later without knowing about them', () => {
    // A budget filter that only lets b through: dropping it leaves a, f; dropping beds leaves b.
    const filters: ActiveFilters = { beds: withBeds(1), budget: [all[1]] }
    expect(relaxSuggestion(all, filters)).toEqual({ kind: 'drop', key: 'budget', count: 2 })
  })

  it('ignores the commute step when the commute filter is off', () => {
    const filters = { beds: [], commute: null }
    expect(relaxSuggestion(all, filters, [commuteStep(15)]))
      .toEqual({ kind: 'drop', key: 'beds', count: 10 })
  })

  it('returns null when no single change helps', () => {
    const filters = { beds: [], baths: [] }
    expect(relaxSuggestion(all, filters)).toBeNull()
  })
})
