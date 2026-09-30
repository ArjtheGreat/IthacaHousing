import { describe, it, expect } from 'vitest'
import { filterByBudget, budgetLabel, BUDGET_OPTIONS } from '../budget'

let nextId = 0
function listing(rent_per_person: number | null) {
  return { listingid: `id-${nextId++}`, rent_per_person }
}

describe('filterByBudget', () => {
  it('keeps listings at or under the cap', () => {
    const cheap = listing(800)
    const exact = listing(1000)
    const pricey = listing(1001)
    expect(filterByBudget([cheap, exact, pricey], 1000)).toEqual([cheap, exact])
  })

  it('drops listings with a missing or zero rent once a budget is set', () => {
    const priced = listing(900)
    expect(filterByBudget([priced, listing(null), listing(0)], 1000)).toEqual([priced])
  })

  it('keeps low rents instead of treating them as bad data', () => {
    const low = listing(230)
    expect(filterByBudget([low], 1000)).toEqual([low])
  })

  it('returns every listing, unpriced ones included, when the budget is Any', () => {
    const all = [listing(900), listing(3000), listing(null)]
    expect(filterByBudget(all, 0)).toEqual(all)
  })

  it('handles an empty list', () => {
    expect(filterByBudget([], 1000)).toEqual([])
  })
})

describe('budget options', () => {
  it('are ascending dollar amounts', () => {
    expect(BUDGET_OPTIONS.length).toBeGreaterThan(0)
    expect([...BUDGET_OPTIONS].sort((a, b) => a - b)).toEqual(BUDGET_OPTIONS)
  })

  it('label caps with a thousands separator', () => {
    expect(budgetLabel(1000)).toBe('≤ $1,000 / person')
    expect(budgetLabel(800)).toBe('≤ $800 / person')
  })
})
