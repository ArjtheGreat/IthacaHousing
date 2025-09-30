# Frontend Application 🎨

Vue.js 3 + TypeScript single-page application for visualizing Ithaca housing data with interactive maps and analytics.

---

## 📁 File Structure

```
frontend/
├── src/
│   ├── main.ts                 # Application entry point
│   ├── App.vue                 # Root component
│   ├── components/             # Vue components
│   │   ├── MapView.vue        # Main map visualization
│   │   ├── NavBar.vue         # Navigation bar
│   │   ├── RentalSidebar.vue  # Listing details sidebar
│   │   └── ...                # Other UI components
│   ├── router/                 # Vue Router configuration
│   │   └── index.ts           # Route definitions
│   ├── services/               # API & business logic
│   │   ├── fetch.ts           # API fetch functions
│   │   └── interface.ts       # TypeScript interfaces
│   ├── stores/                 # Pinia state management
│   │   ├── counter.ts         # Example store
│   │   └── theme.ts           # Theme store
│   ├── assets/                 # Static assets
│   │   ├── base.css           # Base styles
│   │   ├── main.css           # Main styles
│   │   ├── avatars/           # Team avatars
│   │   └── ...
│   └── views/                  # Page views
├── public/                     # Public static files
│   ├── maps/                   # Map data (CSV, GeoJSON)
│   ├── graphs/                 # Historical data
│   └── robots.txt
├── package.json                # NPM dependencies
├── vite.config.ts             # Vite configuration
├── tsconfig.json              # TypeScript configuration
└── index.html                 # HTML entry point
```

---

## 🏗️ Architecture

### Component Hierarchy

```
App.vue
└── Router View
    ├── MapView.vue (Main Page)
    │   ├── NavBar.vue
    │   ├── RentalSidebar.vue
    │   └── Leaflet Map
    │       ├── CircleMarkers (listings)
    │       ├── Heatmap Layer
    │       └── Route Polylines
    └── Other Views
```

### State Management

```
Pinia Stores
├── Theme Store         # Dark/light mode
└── Counter Store       # Example state
```

---

## 🗺️ MapView.vue Architecture

The main component powering the interactive map visualization.

### Key Features

1. **Dynamic Marker Rendering**
   - Color-coded by fair value (green = good deal, red = overpriced)
   - Dispersed markers for same-address listings
   - Clickable markers with sidebar details

2. **Filtering System**
   - **Explore Ithaca Tab**: Heatmaps, clusters, top/bottom listings
   - **Personal Taste Tab**: Beds, baths, walk time, transit, pets

3. **Map Layers**
   - Base layer: Jawg Maps
   - Listings layer: Circle markers
   - Heatmap layer: Kernel density
   - Route layer: Walking routes (WKT polylines)

### Marker Dispersion Algorithm

```typescript
// Groups listings by exact coordinates
// Disperses overlapping markers in circular pattern
// Radius: ~11 meters (0.00005 degrees)
```

Benefits:
- ✅ Only affects same-address listings
- ✅ All units visible and clickable
- ✅ Maintains spatial accuracy

---

## 📡 API Integration

### Service Layer (`fetch.ts`)

```typescript
// Example API calls
fetchListings()                  // GET /listings/
fetchTopTenListings()           // GET /top-ten-listings/
fetchBedFilter(beds)            // GET /listing/beds/{n}
fetchHeatMap()                  // GET /heatmap/
```

### Data Flow

```
User Interaction
    ↓
Vue Component Event
    ↓
API Service Call (fetch.ts)
    ↓
Backend REST API
    ↓
Update Component State
    ↓
Re-render UI
```

---

## 🎨 Styling

### CSS Architecture

```
assets/
├── base.css        # CSS variables, resets, base styles
└── main.css        # Component-specific styles
```

### Design System

- **Colors**: Dynamic theme-aware colors
- **Typography**: System font stack
- **Spacing**: Consistent spacing scale
- **Breakpoints**: Responsive design

---

## 🔧 Setup & Installation

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint
```

---

## 🚀 Deployment

### Fly.io Deployment

```bash
# Install Fly CLI
brew install flyctl

# Deploy
fly deploy

# Open app
fly open
```

### Environment Variables

Create `.env` file:

```bash
VITE_API_BASE_URL=https://api.ithacainsights.com
VITE_JAWG_API_KEY=your_jawg_api_key
```

---

## 🗺️ Map Configuration

### Leaflet Setup

```typescript
// Map initialization
const map = L.map("map", {
  center: [42.455, -76.48],  // Ithaca, NY
  zoom: 14,
  maxZoom: 20
});

// Tile layer (Jawg Maps)
L.tileLayer(
  'https://tile.jawg.io/.../{z}/{x}/{y}.png',
  { attribution: '...' }
).addTo(map);
```

### Marker Clustering

Uses `leaflet.markercluster` for grouping nearby markers:
- Automatic clustering within 50px radius
- Spiderfy on max zoom
- Custom cluster icons

---

## 🎯 Key Components

### MapView.vue

**Responsibilities:**
- Render Leaflet map
- Display housing listings as markers
- Handle user interactions (click, filter)
- Show/hide sidebar with listing details
- Plot walking routes

**State:**
```typescript
const map = ref(null)
const markers = ref([])
const allListings = ref([])
const selectedListing = ref(null)
const isSidebarVisible = ref(false)
const activeFilter = ref("")
```

### RentalSidebar.vue

**Responsibilities:**
- Display detailed listing information
- Show photos in carousel
- Display amenities, pricing, location
- Fair value indicator

### NavBar.vue

**Responsibilities:**
- Site navigation
- Logo and branding
- Mobile-responsive menu

---

## 📊 Data Visualization

### Heatmap Layer

```typescript
// Kernel density estimation
const heatmapLayer = L.heatLayer(
  heatmapData.value,
  {
    radius: 25,
    blur: 15,
    maxZoom: 17,
    gradient: { ... }
  }
);
```

### Color Coding

```typescript
// Fair value color scale
function getColor(actualRent, predictedRent) {
  const diff = actualRent - predictedRent;
  if (diff < -100) return '#00ff00';      // Great deal
  if (diff < 0) return '#90ee90';         // Good deal
  if (diff < 100) return '#ffff00';       // Fair
  if (diff < 200) return '#ff9900';       // Expensive
  return '#ff0000';                        // Very expensive
}
```

---

## 🧪 Testing

```bash
# Unit tests
npm run test:unit

# E2E tests
npm run test:e2e
```

---

## 📦 Dependencies

### Core
- `vue` - Frontend framework
- `vue-router` - Routing
- `pinia` - State management
- `typescript` - Type safety

### Maps
- `leaflet` - Map library
- `leaflet.heat` - Heatmap plugin
- `leaflet.markercluster` - Marker clustering

### UI
- `@headlessui/vue` - Unstyled UI components

### Build Tools
- `vite` - Build tool
- `vitest` - Testing framework

---

## 🎯 Features Implementation

### Filter System

```typescript
// Two-tab interface
activeTab.value = 'Explore Ithaca' | 'Personal Taste'

// Explore filters
- Show Heatmap
- Show Clusters
- Top 10 Listings
- Bottom 10 Listings

// Personal filters
- Bedrooms (0-5+)
- Bathrooms (0-3+)
- Walking distance
- Transit score
- Pet-friendly
```

### Marker Dispersion

```typescript
function groupListingsByLocation(listings) {
  // Groups by exact coordinates
  // Applies circular dispersion
  // Returns dispersed listings
}
```

---

## 🔍 Performance Optimization

- **Lazy Loading**: Components loaded on demand
- **Code Splitting**: Route-based splitting
- **Asset Optimization**: Image compression
- **Tree Shaking**: Unused code elimination
- **Caching**: Service worker for offline support

---

## 🎨 Customization

### Theme

Modify `assets/base.css` for theme customization:

```css
:root {
  --color-primary: #...;
  --color-background: #...;
  --spacing-unit: 8px;
}
```

### Map Style

Change tile provider in `MapView.vue`:

```typescript
const TILE_PROVIDER = 'https://...';
```

---

## 🐛 Debugging

### Vue DevTools

Install Vue DevTools browser extension for:
- Component inspection
- State management debugging
- Performance profiling

### Console Logging

```typescript
console.log('Map initialized:', map.value);
console.log('Listings loaded:', allListings.value.length);
```

---

## 🚧 Future Enhancements

- [ ] Progressive Web App (PWA) support
- [ ] Advanced filtering (price range, date)
- [ ] Saved searches
- [ ] User accounts & favorites
- [ ] Share listing links
- [ ] Print-friendly views
- [ ] Accessibility improvements

---

## 🤝 Contributing

1. Follow Vue.js style guide
2. Use TypeScript for type safety
3. Write meaningful component names
4. Document complex logic
5. Test before submitting PR

---

## 📚 Resources

- [Vue.js Documentation](https://vuejs.org/)
- [Leaflet Documentation](https://leafletjs.com/)
- [Vite Documentation](https://vitejs.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

---