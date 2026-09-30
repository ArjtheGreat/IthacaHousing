import { describe, it, expect } from 'vitest'
import {
  groupIntoComplexes, normalizeAddress, valueScore, getColor, colorForScore, bucketForScore,
  median, sortByValue, titleCase, UNPRICED_COLOR, type MapListing,
} from '../complexes'

let nextId = 0
function listing(overrides: Partial<MapListing> = {}): MapListing {
  return {
    listingid: `id-${nextId++}`,
    listingaddress: '327 EDDY ST',
    latitude: 42.441643,
    longitude: -76.487236,
    rent_per_person: 1000,
    predictedrent: 1000,
    available_bedrooms: 2,
    ...overrides,
  }
}

describe('normalizeAddress', () => {
  it('treats different spellings of one building as equal', () => {
    expect(normalizeAddress('815 S AURORA')).toBe('815 aurora s')
    expect(normalizeAddress('815 AURORA ST S')).toBe('815 aurora s')
    expect(normalizeAddress('717 BUFFALO STREET E')).toBe(normalizeAddress('717 E Buffalo St'))
  })

  it('drops unit markers and punctuation', () => {
    expect(normalizeAddress('957 Dryden Rd. Apt. #C')).toBe('957 dryden')
    expect(normalizeAddress('143 MAPLE AVENUE #3')).toBe('143 maple')
    expect(normalizeAddress('304 THURSTON AVENUE (BLDG. B)')).toBe('304 thurston')
  })

  it('keeps different house numbers apart', () => {
    expect(normalizeAddress('203 WILLIAMS ST')).not.toBe(normalizeAddress('205 WILLIAMS ST'))
  })

  it('handles empty input', () => {
    expect(normalizeAddress(null)).toBe('')
    expect(normalizeAddress('')).toBe('')
  })
})

describe('valueScore and colors', () => {
  it('is positive when rent is below the prediction', () => {
    expect(valueScore({ rent_per_person: 1000, predictedrent: 1100 })).toBeCloseTo(0.1)
    expect(valueScore({ rent_per_person: 1000, predictedrent: 900 })).toBeCloseTo(-0.1)
  })

  it('returns null instead of dividing by a zero or missing rent', () => {
    expect(valueScore({ rent_per_person: 0, predictedrent: 1200 })).toBeNull()
    expect(valueScore({ rent_per_person: null, predictedrent: 1200 })).toBeNull()
    expect(valueScore({ rent_per_person: 1000, predictedrent: null })).toBeNull()
  })

  it('maps scores onto the red-yellow-green scale', () => {
    expect(colorForScore(-0.2)).toBe('#d73027')
    expect(colorForScore(0)).toBe('#fee08b')
    expect(colorForScore(0.2)).toBe('#1a9850')
    expect(colorForScore(5)).toBe('#1a9850')
    expect(colorForScore(-5)).toBe('#d73027')
  })

  it('paints a zero-rent listing grey, not green', () => {
    expect(getColor(0, 1200)).toBe(UNPRICED_COLOR)
    expect(getColor(1000, 1000)).toBe('#fee08b')
  })

  it('buckets scores with a 5% fair band', () => {
    expect(bucketForScore(0.06)).toBe('under')
    expect(bucketForScore(0.05)).toBe('fair')
    expect(bucketForScore(-0.05)).toBe('fair')
    expect(bucketForScore(-0.06)).toBe('over')
  })
})

describe('median', () => {
  it('handles odd, even and empty lists', () => {
    expect(median([3, 1, 2])).toBe(2)
    expect(median([4, 1, 3, 2])).toBe(2.5)
    expect(median([])).toBeNull()
  })
})

describe('groupIntoComplexes', () => {
  it('turns 43 units at one point into one complex', () => {
    const units = Array.from({ length: 43 }, () => listing({ listingaddress: '121 LAKE ST' }))
    const complexes = groupIntoComplexes(units)
    expect(complexes).toHaveLength(1)
    expect(complexes[0].count).toBe(43)
    expect(complexes[0].units).toHaveLength(43)
  })

  it('leaves a lone listing as a complex of one at its own coordinates', () => {
    const [complex] = groupIntoComplexes([listing({ latitude: 42.5, longitude: -76.5 })])
    expect(complex.count).toBe(1)
    expect(complex.lat).toBe(42.5)
    expect(complex.lng).toBe(-76.5)
  })

  it('keeps neighboring buildings separate', () => {
    const complexes = groupIntoComplexes([
      listing({ listingaddress: '203 WILLIAMS ST', latitude: 42.442196, longitude: -76.488625 }),
      listing({ listingaddress: '205 WILLIAMS ST', latitude: 42.442200, longitude: -76.488480 }),
    ])
    expect(complexes).toHaveLength(2)
  })

  it('merges one building geocoded to two nearby points under two spellings', () => {
    const complexes = groupIntoComplexes([
      listing({ listingaddress: '815 S AURORA', latitude: 42.43, longitude: -76.49 }),
      listing({ listingaddress: '815 AURORA ST S', latitude: 42.43005, longitude: -76.49003 }),
    ])
    expect(complexes).toHaveLength(1)
    expect(complexes[0].count).toBe(2)
  })

  it('does not merge the same address when the points are far apart', () => {
    const complexes = groupIntoComplexes([
      listing({ listingaddress: '205 DRYDEN RD', latitude: 42.4415, longitude: -76.4849 }),
      listing({ listingaddress: '205 DRYDEN RD', latitude: 42.4400, longitude: -76.4978 }),
    ])
    expect(complexes).toHaveLength(2)
  })

  it('splits two addresses that share a coordinate and nudges them apart', () => {
    const complexes = groupIntoComplexes([
      listing({ listingaddress: '111 S CAYUGA ST' }),
      listing({ listingaddress: '151 DRYDEN RD' }),
    ])
    expect(complexes).toHaveLength(2)
    expect(complexes[0].lat === complexes[1].lat && complexes[0].lng === complexes[1].lng).toBe(false)
  })

  it('computes rent stats and the price mix', () => {
    const [complex] = groupIntoComplexes([
      listing({ rent_per_person: 800, predictedrent: 1000 }),  // +25% -> under
      listing({ rent_per_person: 1000, predictedrent: 1000 }), // fair
      listing({ rent_per_person: 1200, predictedrent: 1000 }), // -17% -> over
      listing({ rent_per_person: 1400, predictedrent: 1000 }), // over
    ])
    expect(complex.minRent).toBe(800)
    expect(complex.maxRent).toBe(1400)
    expect(complex.medianRent).toBe(1100)
    expect(complex.buckets).toEqual({ under: 1, fair: 1, over: 2 })
    expect(complex.unpriced).toBe(0)
  })

  it('lists zero-rent units but leaves them out of the stats', () => {
    const [complex] = groupIntoComplexes([
      listing({ rent_per_person: 0, predictedrent: 1500 }),
      listing({ rent_per_person: 1000, predictedrent: 1000 }),
    ])
    expect(complex.count).toBe(2)
    expect(complex.unpriced).toBe(1)
    expect(complex.minRent).toBe(1000)
    expect(complex.medianScore).toBe(0)
    expect(complex.buckets).toEqual({ under: 0, fair: 1, over: 0 })
  })

  it('reports null stats when no unit has a rent', () => {
    const [complex] = groupIntoComplexes([listing({ rent_per_person: 0 }), listing({ rent_per_person: 0 })])
    expect(complex.minRent).toBeNull()
    expect(complex.medianRent).toBeNull()
    expect(complex.medianScore).toBeNull()
  })

  it('gives a building the same id when filters change which units are present', () => {
    const units = [listing({ available_bedrooms: 1 }), listing({ available_bedrooms: 2 }), listing({ available_bedrooms: 3 })]
    const all = groupIntoComplexes(units)[0]
    const filtered = groupIntoComplexes(units.slice(1))[0]
    expect(filtered.id).toBe(all.id)
  })

  it('keeps its id when filters change a building geocoded to one point, and still groups a two-point building', () => {
    const units = [
      listing({ listingaddress: '815 S AURORA', latitude: 42.43, longitude: -76.49 }),
      listing({ listingaddress: '815 AURORA ST S', latitude: 42.43005, longitude: -76.49003 }),
      listing({ listingaddress: '815 AURORA ST S', latitude: 42.43005, longitude: -76.49003 }),
    ]
    const filtered = groupIntoComplexes(units.slice(1))
    expect(filtered).toHaveLength(1)
    expect(filtered[0].count).toBe(2)
  })

  it('skips listings without usable coordinates instead of throwing', () => {
    const broken = [
      listing({ latitude: null as unknown as number }),
      listing({ longitude: NaN }),
      listing({ latitude: undefined as unknown as number }),
    ]
    const complexes = groupIntoComplexes([...broken, listing()])
    expect(complexes).toHaveLength(1)
    expect(complexes[0].count).toBe(1)
  })

  it('never merges blank addresses across coordinates', () => {
    const complexes = groupIntoComplexes([
      listing({ listingaddress: '', latitude: 42.44, longitude: -76.48 }),
      listing({ listingaddress: null as unknown as string, latitude: 42.44005, longitude: -76.48003 }),
    ])
    expect(complexes).toHaveLength(2)
  })

  it('does not merge the same number and name on different street types', () => {
    const complexes = groupIntoComplexes([
      listing({ listingaddress: '100 MAIN ST', latitude: 42.44, longitude: -76.48 }),
      listing({ listingaddress: '100 MAIN AVE', latitude: 42.44005, longitude: -76.48003 }),
    ])
    expect(complexes).toHaveLength(2)
  })

  it('groups 5,000 distinct addresses quickly', () => {
    const many = Array.from({ length: 5000 }, (_, i) =>
      listing({ listingaddress: `${i} TEST ST`, latitude: 42 + i * 0.001, longitude: -76 - i * 0.001 }))
    const start = performance.now()
    expect(groupIntoComplexes(many)).toHaveLength(5000)
    expect(performance.now() - start).toBeLessThan(1000)
  })

  it('returns nothing for no listings', () => {
    expect(groupIntoComplexes([])).toEqual([])
  })
})

describe('sortByValue', () => {
  it('puts the best deal first and unpriced units last', () => {
    const cheap = listing({ rent_per_person: 800, predictedrent: 1000 })
    const pricey = listing({ rent_per_person: 1300, predictedrent: 1000 })
    const unpriced = listing({ rent_per_person: 0, predictedrent: 1000 })
    expect(sortByValue([unpriced, pricey, cheap])).toEqual([cheap, pricey, unpriced])
  })
})

describe('titleCase', () => {
  it('fixes all-caps addresses', () => {
    expect(titleCase('327 EDDY ST')).toBe('327 Eddy St')
  })
})
