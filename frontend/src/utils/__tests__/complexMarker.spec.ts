import { describe, it, expect } from 'vitest'
import {
  complexMarkerSvg, compactMarkerSvg, complexPopupHtml, radiusFor, countLabel, textColorOn, escapeHtml,
  type MarkerPaint,
} from '../complexMarker'

const paint: MarkerPaint = {
  center: '#fee08b',
  segments: [
    { color: '#1a9850', count: 2 },
    { color: '#fee08b', count: 14 },
    { color: '#d73027', count: 6 },
  ],
}

describe('radiusFor', () => {
  it('grows with the unit count and is capped', () => {
    expect(radiusFor(2)).toBeLessThan(radiusFor(10))
    expect(radiusFor(10)).toBeLessThan(radiusFor(22))
    expect(radiusFor(43)).toBe(24)
    expect(radiusFor(500)).toBe(24)
  })
})

describe('countLabel', () => {
  it('caps at 99+', () => {
    expect(countLabel(22)).toBe('22')
    expect(countLabel(99)).toBe('99')
    expect(countLabel(100)).toBe('99+')
  })
})

describe('textColorOn', () => {
  it('uses dark text on light fills and white on dark fills', () => {
    expect(textColorOn('#fee08b')).toBe('#1f2937')
    expect(textColorOn('#d73027')).toBe('#ffffff')
  })
})

describe('complexMarkerSvg', () => {
  it('shows the count and an accessible label', () => {
    const { html, size } = complexMarkerSvg(22, paint, '327 EDDY ST')
    expect(html).toContain('>22</text>')
    expect(html).toContain('aria-label="22 units at 327 Eddy St"')
    expect(size).toBeGreaterThan(2 * radiusFor(22))
  })

  it('draws one ring arc per non-empty segment', () => {
    const { html } = complexMarkerSvg(22, paint, '327 EDDY ST')
    expect(html.match(/<path /g)).toHaveLength(3)
    const twoGroups = complexMarkerSvg(5, { center: '#1a9850', segments: [{ color: '#1a9850', count: 4 }, { color: '#fee08b', count: 0 }, { color: '#d73027', count: 1 }] }, 'x')
    expect(twoGroups.html.match(/<path /g)).toHaveLength(2)
  })

  it('draws a full circle when every unit is in one group', () => {
    const { html } = complexMarkerSvg(4, { center: '#1a9850', segments: [{ color: '#1a9850', count: 4 }] }, 'x')
    expect(html).not.toContain('<path ')
    expect(html).toContain('stroke="#1a9850"')
  })

  it('draws no ring when no unit has a price', () => {
    const { html } = complexMarkerSvg(3, { center: '#9ca3af', segments: [] }, 'x')
    expect(html).not.toContain('stroke=')
    expect(html).toContain('>3</text>')
  })

  it('never emits NaN coordinates, even for a tiny sliver', () => {
    const { html } = complexMarkerSvg(43, { center: '#fee08b', segments: [{ color: '#1a9850', count: 1 }, { color: '#d73027', count: 42 }] }, 'x')
    expect(html).not.toContain('NaN')
  })
})

describe('compactMarkerSvg', () => {
  it('is smaller than the full marker and has no count text', () => {
    const compact = compactMarkerSvg(22, '#fee08b', '327 EDDY ST')
    expect(compact.size).toBeLessThan(complexMarkerSvg(22, paint, '327 EDDY ST').size)
    expect(compact.html).not.toContain('<text')
    expect(compact.html).toContain('aria-label="22 units at 327 Eddy St"')
  })
})

describe('complexPopupHtml', () => {
  const content = {
    address: '327 EDDY ST',
    summary: '22 units · $1,200–$1,800',
    rows: [
      { id: '240143-1', beds: '2 bd', rent: '$1,250', color: '#a6c36f', badge: '8.0%', badgeClass: 'under' as const },
      { id: '240143-2', beds: '3 bd', rent: '$1,700', color: '#d73027', badge: '12.0%', badgeClass: 'over' as const },
    ],
  }

  it('renders one button per unit carrying its listing id', () => {
    const el = document.createElement('div')
    el.innerHTML = complexPopupHtml(content)
    const rows = el.querySelectorAll<HTMLButtonElement>('button.complex-popup-row')
    expect(rows).toHaveLength(2)
    expect(rows[0].dataset.listingId).toBe('240143-1')
    expect(rows[0].textContent).toContain('$1,250')
    expect(el.querySelector('.complex-popup-head strong')?.textContent).toBe('327 Eddy St')
  })

  it('shows the filter note only when given', () => {
    expect(complexPopupHtml(content)).not.toContain('complex-popup-note')
    expect(complexPopupHtml({ ...content, note: '8 of 22 units match your filters' })).toContain('8 of 22 units match your filters')
  })

  it('escapes listing text', () => {
    const html = complexPopupHtml({ ...content, address: '<img src=x onerror=alert(1)>' })
    expect(html).not.toContain('<img')
    expect(escapeHtml('"a" & <b>')).toBe('&quot;a&quot; &amp; &lt;b&gt;')
  })
})
