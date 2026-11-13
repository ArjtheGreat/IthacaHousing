import { describe, expect, it } from 'vitest'
import { AMENITY_OPTIONS, AMENITY_CATEGORIES, groupedAdvertisedAmenities, matchesAmenityKeys, rawAmenityLabels } from '../amenities'

describe('curated amenity filters', () => {
  it('has 23 distinct, categorized choices', () => {
    expect(AMENITY_OPTIONS).toHaveLength(23)
    expect(new Set(AMENITY_OPTIONS.map(option => option.key)).size).toBe(23)
    expect(AMENITY_CATEGORIES).toEqual(['Unit features', 'Building amenities', 'Utilities & services', 'Pets & accessibility'])
  })
  it('normalizes aliases without substring false positives', () => {
    expect(matchesAmenityKeys(JSON.stringify(['24 hour Fitness Center', 'Dishwasher']), ['fitness_center', 'dishwasher'])).toBe(true)
    expect(matchesAmenityKeys(JSON.stringify(['Furnished Packages Available']), ['furnished'])).toBe(false)
    expect(matchesAmenityKeys(JSON.stringify(['Internet Ready', 'High Speed Internet']), ['internet_included'])).toBe(false)
    expect(matchesAmenityKeys(JSON.stringify(['Washer & Dryer']), ['shared_laundry'])).toBe(false)
  })
  it('requires all selected amenities and handles empty/malformed sources safely', () => {
    expect(matchesAmenityKeys('["Dishwasher"]', ['dishwasher', 'pool'])).toBe(false)
    expect(matchesAmenityKeys(null, ['dishwasher'])).toBe(false)
    expect(matchesAmenityKeys(null, [])).toBe(true)
    expect(rawAmenityLabels('{broken')).toEqual([])
  })
})
describe('property detail presentation', () => {
  it('keeps raw unique labels but removes lease terms from amenity cards', () => {
    const groups = groupedAdvertisedAmenities(JSON.stringify(['Fitness Center', '24 hour Fitness Center', '12-month', 'Graduate Students', 'Dishwasher', 'Dishwasher']))
    const all = groups.flatMap(group => group.amenities)
    expect(all).toContain('Fitness Center')
    expect(all).toContain('24 hour Fitness Center')
    expect(all).toContain('Dishwasher')
    expect(all).not.toContain('12-month')
    expect(all).not.toContain('Graduate Students')
    expect(all.filter(label => label === 'Dishwasher')).toHaveLength(1)
  })
})
