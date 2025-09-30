# Backend API 🚀

FastAPI-based REST API for Ithaca Housing Insights, providing endpoints for housing data, ML predictions, and spatial analytics.

---

## 📁 File Structure

```
backend/
├── main.py                 # FastAPI application & endpoints
├── db.py                   # Database models & connection
├── serializers.py          # Data serialization utilities
├── site_selector/          # Vacant lot analysis
│   ├── site_selector_api.py
│   └── TompkinsCountyData.csv
├── airflow/                # ML pipeline (see airflow/README.md)
├── tests/                  # Unit tests
│   └── test_backend.py
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
└── docker-compose.yml      # Docker configuration
```

---

## 🏗️ Architecture

### Core Components

1. **main.py** - FastAPI application
   - RESTful API endpoints
   - CORS middleware
   - Prometheus instrumentation
   - Request/response logging

2. **db.py** - Database layer
   - SQLAlchemy ORM models
   - PostgreSQL connection
   - Environment variable loading
   - Database session management

3. **serializers.py** - Data serialization
   - `serialize_listing()` - Convert DB models to JSON
   - `safe_float()` - Handle inf/nan/decimal values
   - Type-safe conversions

---

## 🗄️ Database Schema

### HousingListing Model

```python
{
    listingid: int              # Primary key
    listingaddress: str         # Street address
    listingcity: str           # City
    listingzip: str            # ZIP code
    shortdescription: text     # Listing description
    rentamount: numeric        # Listed rent price
    renttype: str              # Rent period (monthly, etc.)
    pets: str                  # Pet policy
    amenities: str             # Available amenities
    bedrooms: numeric          # Number of bedrooms
    bathrooms: numeric         # Number of bathrooms
    housingtype: str           # Type (Rent, Room to Rent, Shared)
    latitude: numeric          # GPS latitude
    longitude: numeric         # GPS longitude
    listingphotos: json        # Photo URLs
    walk_time: numeric         # Walking time to Cornell
    walk_routes: text          # Walking route (WKT LineString)
    bike_time: numeric         # Biking time to Cornell
    bike_routes: text          # Biking route (WKT LineString)
    drive_time: numeric        # Driving time to Cornell
    drive_routes: text         # Driving route (WKT LineString)
    transit_score: numeric     # Transit accessibility score
    amenities_score: numeric   # Nearby amenities score
    overallsafetyratingpct: numeric  # Safety rating percentage
    rentamountadjusted: numeric      # Log-transformed rent
    predictedrent: numeric     # ML-predicted rent
    differenceinfairvalue: numeric   # Predicted - Actual rent
    nearest_neighbor_listingids: text  # CMA neighbor IDs
}
```

---

## 🔌 API Endpoints

### Listings

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/listings/` | GET | Get all housing listings |
| `/top-ten-listings/` | GET | Top 10 best value listings |
| `/bottom-ten-listings/` | GET | Bottom 10 worst value listings |
| `/listing/{listing_id}` | GET | Get single listing by ID |

### Filters

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/listing/beds/{n_beds}` | GET | Filter by number of bedrooms |
| `/listing/baths/{n_baths}` | GET | Filter by number of bathrooms |
| `/listing/walks` | GET | Below-average walking time |
| `/listing/transit` | GET | Above-average transit score |
| `/listing/pets` | GET | Pet-friendly listings |
| `/room-to-rent-listings/` | GET | Room to rent listings |
| `/rent-listings/` | GET | Full rental listings |
| `/shared-listings/` | GET | Shared housing listings |

### Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/clusters/` | GET | Neighborhood price clusters |
| `/heatmap/` | GET | Rental price heatmap data |
| `/voronoi/` | GET | Voronoi price polygons (GeoJSON) |

### Site Selection

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/vacant-lots` | GET | Vacant lots in Ithaca |
| `/all-lots` | GET | All parcels in Ithaca |

### Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/metrics` | GET | Prometheus metrics |
| `/metric-calculations` | GET | Update ML metrics |
| `/metrics-debug` | GET | Debug metrics endpoint |

---

## 🔧 Setup & Installation

### 1. Environment Setup

Create a `.env` file:

```bash
DB_USER=postgres
DB_PWD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=IthacaHousing
DB_URI=postgresql://user:pass@host:port/dbname
```

### 2. Install Dependencies

```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Server

```bash
# Development
uvicorn main:app --reload

# Production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

The API will be available at `http://localhost:8000`

---

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

---

## 📊 Data Flow

```
Client Request
    ↓
FastAPI Endpoint
    ↓
Database Query (SQLAlchemy)
    ↓
Serializer (safe_float, serialize_listing)
    ↓
JSON Response
```

---

## 🧪 Testing

```bash
pytest tests/test_backend.py
```

---

## 📈 Monitoring

### Prometheus Metrics

Access metrics at `/metrics`:
- Request count
- Response times
- Error rates
- Custom ML metrics (SSE, SSR, R²)

### Grafana Dashboard

Configure Grafana to scrape `/metrics` for visualization.

---

## 🔍 Key Features

### Data Serialization
- **Type Safety**: All Decimal/Numeric fields converted to float
- **Inf/NaN Handling**: Invalid values converted to null
- **JSON Compliance**: Ensures all responses are JSON-serializable

### Spatial Analytics
- **Clustering**: Hierarchical clustering for neighborhood grouping
- **Heatmaps**: Kernel density estimation for price visualization
- **Voronoi Diagrams**: Spatial tessellation for market areas

### Performance
- **Connection Pooling**: Efficient database connections
- **Async Support**: FastAPI async capabilities
- **Caching**: Prepared for Redis caching layer

---

## 🛡️ Error Handling

All endpoints include try-catch blocks with detailed error messages:

```python
try:
    # Database operations
except Exception as e:
    raise HTTPException(
        status_code=500, 
        detail=str(e) + traceback.format_exc()
    )
```

---

## 🔐 Security

- CORS enabled for cross-origin requests
- Environment variables for sensitive data
- SQL injection protection via SQLAlchemy ORM
- Input validation on all endpoints

---

## 📚 Dependencies

Key Python packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `psycopg2` - PostgreSQL adapter
- `pandas` - Data manipulation
- `geopandas` - Spatial data
- `scipy` - Scientific computing
- `prometheus-fastapi-instrumentator` - Metrics

---

## 🚧 Future Enhancements

- [ ] Redis caching layer
- [ ] Rate limiting
- [ ] Authentication & authorization
- [ ] WebSocket support for real-time updates
- [ ] GraphQL endpoint
- [ ] Advanced filtering with query parameters

---

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Write tests
4. Submit pull request

---

## 📝 API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---
