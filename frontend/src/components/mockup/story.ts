/**
 * The frames of the /rent-preview walkthrough, in order.
 * Each frame is a snapshot of the redesigned UI with a caption explaining the change.
 */
export type FrameId = 'start' | 'search' | 'results' | 'detail' | 'no-results' | 'analytics';

export interface Frame {
    id: FrameId;
    title: string;
    caption: string;
}

export const frames: Frame[] = [
    {
        id: 'start',
        title: 'Meet Retep',
        caption: 'Retep is a beer student at Cornell, and he is bringing all five members of his family. ' +
            'Everything a student needs is already on the map: listings, campus quads and TCAT stops. ' +
            'There are no "points of interest" to toggle on.',
    },
    {
        id: 'search',
        title: 'Describe it, don\'t filter it',
        caption: 'The search bar takes a sentence, not just an address. ' +
            'An LLM turns it into concrete criteria and shows them back as chips, so Retep can see and correct what it understood. ' +
            '"Beer student" becomes "walk to the Ag Quad", where food science lives, and "5 family members" becomes six bedrooms.',
    },
    {
        id: 'results',
        title: 'Top options, not just dots',
        caption: 'Once Retep has said what he wants, the map gets a ranked list beside it. ' +
            'Rank blends walk time and fair-rent value, and every row says why it is there. ' +
            'The Featured slot is where landlords pay for placement.',
    },
    {
        id: 'detail',
        title: 'Go to the real listing',
        caption: 'Opening a result keeps the fair-rent comparison the map is known for, and adds one thing the current app lacks: a link to the actual listing. ' +
            'That is stage 1. Stage 2 is our own listing page, for convenience and SEO.',
    },
    {
        id: 'no-results',
        title: 'Filters never fail silently',
        caption: 'Retep tightens the walk to 10 minutes and nothing matches. ' +
            'Today the map just goes blank. Here he gets told, sees the closest relaxation that would work, and can apply it in one click.',
    },
    {
        id: 'analytics',
        title: 'Research tools move to Analytics',
        caption: 'The price-differential legend, heatmap and clustering serve people studying the market, not students picking an apartment. ' +
            'They move to the Analytics page, and the rent map stays focused on one job.',
    },
];
