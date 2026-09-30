import { describe, it, expect } from 'vitest';
import { chipsFor, matchListings, persona, rankListings, relaxSuggestion, tooStrictCriteria } from '../data';

describe('rent-preview data', () => {
    it('finds real listings for the persona', () => {
        const ranked = rankListings(persona.criteria);
        expect(ranked.length).toBeGreaterThan(3);
        expect(ranked.map(r => r.rank)).toEqual(ranked.map((_, i) => i + 1));
        for (const r of ranked) {
            expect(r.available_bedrooms).toBe(persona.criteria.beds);
            expect(r.rent_per_person).toBeLessThanOrEqual(persona.criteria.budget);
            expect(r.walk).toBeLessThanOrEqual(persona.criteria.maxWalk);
            expect(r.reason).toMatch(/min walk to Ag Quad/);
        }
    });

    it('lists each building once', () => {
        const addresses = rankListings(persona.criteria).map(r => r.listingaddress);
        expect(new Set(addresses).size).toBe(addresses.length);
    });

    it('has nothing for the too-strict search and a working relaxation', () => {
        expect(matchListings(tooStrictCriteria)).toHaveLength(0);
        const s = relaxSuggestion(tooStrictCriteria);
        expect(s).not.toBeNull();
        expect(s!.maxWalk).toBeGreaterThan(tooStrictCriteria.maxWalk);
        expect(matchListings({ ...tooStrictCriteria, maxWalk: s!.maxWalk })).toHaveLength(s!.count);
    });

    it('shows the parsed criteria as chips', () => {
        expect(chipsFor(persona.criteria).map(c => c.label)).toEqual([
            '6 bedrooms', '≤ $1000 per person', '≤ 25 min walk to Ag Quad',
        ]);
    });
});
