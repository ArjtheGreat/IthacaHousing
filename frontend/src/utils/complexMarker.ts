/**
 * Builds the HTML for a building ("complex") marker and its popup list.
 * Everything here returns plain strings so it can be unit tested without Leaflet.
 */
import { titleCase } from './complexes';

export interface RingSegment {
    color: string;
    count: number;
}

export interface MarkerPaint {
    /** Fill of the center disc (the building's typical price). */
    center: string;
    /** Outer ring, one segment per price group. */
    segments: RingSegment[];
}

export interface MarkerArt {
    html: string;
    /** Width and height of the icon in px. */
    size: number;
}

export interface PopupRow {
    id: string | number;
    beds: string;
    rent: string;
    color: string;
    badge: string;
    badgeClass: 'under' | 'fair' | 'over' | 'none';
}

export interface PopupContent {
    address: string;
    /** e.g. "22 units · $1,200–$1,800" */
    summary: string;
    /** Shown when filters hide some of the building's units, e.g. "8 of 22 units match your filters". */
    note?: string;
    rows: PopupRow[];
}

const MAX_RADIUS = 24;

export function escapeHtml(text: unknown): string {
    return String(text ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/** Marker radius grows with the square root of the unit count and stops at MAX_RADIUS. */
export function radiusFor(count: number): number {
    return Math.min(11 + 2.6 * Math.sqrt(Math.max(count, 1) - 1), MAX_RADIUS);
}

export function countLabel(count: number): string {
    return count > 99 ? '99+' : String(count);
}

/** Dark text on light fills, white text on dark fills. */
export function textColorOn(hex: string): string {
    const [r, g, b] = [1, 3, 5].map(i => parseInt(hex.substr(i, 2), 16));
    return 0.299 * r + 0.587 * g + 0.114 * b > 150 ? '#1f2937' : '#ffffff';
}

function arcPath(cx: number, cy: number, r: number, from: number, to: number): string {
    const point = (angle: number) => [cx + r * Math.sin(angle), cy - r * Math.cos(angle)];
    const [x0, y0] = point(from);
    const [x1, y1] = point(to);
    const largeArc = to - from > Math.PI ? 1 : 0;
    return `M${x0.toFixed(2)},${y0.toFixed(2)} A${r},${r} 0 ${largeArc} 1 ${x1.toFixed(2)},${y1.toFixed(2)}`;
}

function ring(segments: RingSegment[], cx: number, cy: number, r: number, width: number): string {
    const visible = segments.filter(s => s.count > 0);
    const total = visible.reduce((sum, s) => sum + s.count, 0);
    if (total === 0) return '';
    if (visible.length === 1) {
        return `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${visible[0].color}" stroke-width="${width}"/>`;
    }
    const gap = 0.16; // radians of white space between segments
    let angle = 0;
    return visible.map(segment => {
        const span = (segment.count / total) * Math.PI * 2;
        // A sliver still has to be drawable once the gap is taken out.
        const start = angle + Math.min(gap / 2, span / 4);
        const end = angle + span - Math.min(gap / 2, span / 4);
        angle += span;
        return `<path d="${arcPath(cx, cy, r, start, end)}" fill="none" stroke="${segment.color}" stroke-width="${width}"/>`;
    }).join('');
}

function ariaLabel(count: number, address: string): string {
    return escapeHtml(`${count} units at ${titleCase(address)}`);
}

/** Full marker: unit count on a disc in the typical price color, inside a ring showing the price mix. */
export function complexMarkerSvg(count: number, paint: MarkerPaint, address: string): MarkerArt {
    const r = radiusFor(count);
    const size = Math.ceil((r + 4) * 2);
    const c = size / 2;
    const ringWidth = 3.2;
    const fontSize = count > 99 ? 9 : count > 9 ? 11.5 : 12.5;
    const html =
        `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" role="img" aria-label="${ariaLabel(count, address)}">` +
        `<circle cx="${c}" cy="${c + 1.2}" r="${r}" fill="rgba(0,0,0,0.18)"/>` +
        `<circle cx="${c}" cy="${c}" r="${r}" fill="#ffffff"/>` +
        ring(paint.segments, c, c, r - ringWidth / 2, ringWidth) +
        `<circle cx="${c}" cy="${c}" r="${r - ringWidth - 1.6}" fill="${paint.center}"/>` +
        `<text x="${c}" y="${c}" dy="0.36em" text-anchor="middle" font-size="${fontSize}" font-weight="700" fill="${textColorOn(paint.center)}">${countLabel(count)}</text>` +
        `</svg>`;
    return { html, size };
}

/** Zoomed-out marker: a small dot in the typical price color, slightly bigger for bigger buildings. */
export function compactMarkerSvg(count: number, centerColor: string, address: string): MarkerArt {
    const r = Math.min(5 + 1.1 * Math.sqrt(Math.max(count, 1)), 10);
    const size = Math.ceil((r + 3) * 2);
    const c = size / 2;
    const html =
        `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" role="img" aria-label="${ariaLabel(count, address)}">` +
        `<circle cx="${c}" cy="${c}" r="${r + 1.5}" fill="#ffffff"/>` +
        `<circle cx="${c}" cy="${c}" r="${r}" fill="${centerColor}"/>` +
        `</svg>`;
    return { html, size };
}

/** The list shown when a building marker is clicked. Each row is a button carrying its listing id. */
export function complexPopupHtml(content: PopupContent): string {
    const rows = content.rows.map(row =>
        `<button type="button" class="complex-popup-row" data-listing-id="${escapeHtml(row.id)}">` +
        `<span class="complex-popup-dot" style="background:${escapeHtml(row.color)}"></span>` +
        `<span class="complex-popup-beds">${escapeHtml(row.beds)}</span>` +
        `<span class="complex-popup-rent">${escapeHtml(row.rent)}<small>/person</small></span>` +
        `<span class="complex-popup-badge complex-popup-${row.badgeClass}">${escapeHtml(row.badge)}</span>` +
        `</button>`
    ).join('');
    const note = content.note ? `<span class="complex-popup-note">${escapeHtml(content.note)}</span>` : '';
    return `<div class="complex-popup">` +
        `<div class="complex-popup-head"><strong>${escapeHtml(titleCase(content.address))}</strong>` +
        `<span>${escapeHtml(content.summary)}</span>${note}</div>` +
        `<div class="complex-popup-list">${rows}</div>` +
        `</div>`;
}
