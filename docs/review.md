# Fair Rent Map: Product Review of Filtering and Search UI/UX

Notes from going over the filtering and search UI/UX on the Fair Rent Map. These are recommendations, not a spec.

## Guiding principle

Optimize for the student searching for off-campus housing use case over the researcher studying the market use case. Research features should move to the analytics page.

## Points of interest (POIs)

Groceries should either not be a standalone POI, or the POI concept should go away entirely. Two options:

1. If POIs stay, bus stops/routes, campus buildings, etc. should also be POIs. Groceries alone doesn't make sense.
2. Remove POIs altogether and just display them always, like we already do with everything else.

## Filters

Filters shouldn't silently fail. Raise a visible error when no results match the filter.

## Show actual housing listings

We should show the actual housing listing, in two stages:

- **Stage 1:** simply link to their listing.
- **Stage 2:** build our own listing view, like other housing sites. This is for user convenience and SEO.

## Search bar

The search bar shouldn't just be address search. Maybe we can use an LLM to give users natural language/semantic search. I can't find a competitor that does this.

Example: a user can search "I'm an engineering student and I have 2 roommates and my budget is x and so on." The LLM implements the search criteria/filtering. "Engineering student" means optimize for locations closer to the eng quad.

## Listing view, not map-only

The view shouldn't be map-only. There should be a listing view for "top options" once a user adds their requirements/preferences.

This is where monetization happens: you can tell landlords that we'll bump you up on our recommendation algo.
