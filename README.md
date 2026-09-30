# Ithaca Insights

Ithaca Insights, built by [Maitrix Labs](https://maitrixlabs.com/), shows whether a rental listing in Ithaca, NY is priced fairly. Every day we pull the current listings, predict what each one should rent for per person, and put the asking rent and our prediction side by side on a map.

Live site: [ithacainsights.com](https://ithacainsights.com)

## Why we built it

Most off-campus rentals in Ithaca are posted on Cornell's off-campus housing site, and a lot of the people reading them are students signing their first lease. A listing tells you the price. It doesn't tell you whether that price is normal for the number of bedrooms, the walk to campus, and what's included. We wanted a number to compare against.

## What's on the site

The Fair Rent Map at [/rent](https://ithacainsights.com/rent) is the main tool. Each listing is colored by how its asking rent compares to our predicted fair rent, and clicking one shows the two numbers together. You can filter by bedrooms, bathrooms, pets, walkability and transit, pull up the ten listings priced furthest below their prediction, or switch to a neighborhood heatmap.

Inside Ithaca is a dashboard of spatial rent trends, income data and model performance. The History and Urban Growth pages are data stories about how the city grew, built partly on 1920 to 1940 census records.

## How it works

```
offcampus.housing.cornell.edu
        │
        ▼
airflow/     scrape, geocode, add features, train, predict    (daily at 12:00 UTC)
        │
        ▼
Postgres     hosted on Supabase
        │
        ▼
backend/     FastAPI, deployed on Fly.io
        │
        ▼
frontend/    Vue 3 + TypeScript + Leaflet
```

Listings don't follow a consistent format, so we use an OpenAI model (`gpt-4.1-mini`) to read rent and bedroom counts out of the listing text. We then add features for each listing: walking time to Uris Hall, TCAT transit access, nearby restaurants and grocery stores, utilities and amenities included, year built, county assessed value per square foot, and location.

The model is XGBoost trained on log rent per person. We validate it with spatial block cross-validation, which holds out whole areas of the map at a time so a listing's next-door neighbors can't leak into its own test fold. After predicting, we find each listing's four most similar listings to compare against. Smaller Airflow jobs refresh travel times, transit scores and neighborhood data on daily or weekly schedules.

The code for all of this is in [`airflow/model/`](airflow/model/README.md).

## Running it locally

You'll need Python 3.12, Node 22, and a Postgres database.

### Backend

Create `backend/.env` with `DB_URI=postgresql://user:password@host:5432/dbname`, then:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at http://localhost:8000, with interactive docs at `/docs`.

### Frontend

Create `frontend/.env.local`:

```
VITE_API_URL=http://localhost:8000
VITE_JAWG_API_KEY=<your key from jawg.io, used for map tiles>
```

Then:

```bash
cd frontend
npm install
npm run dev
```

### Pipeline

The Airflow project uses the [Astro CLI](https://www.astronomer.io/docs/astro/cli/overview) and Docker. Put `DB_URI`, `OPENAI_API_KEY` and `GOOGLE_PLACES_API_KEY` (used for geocoding) in `airflow/.env`, then:

```bash
cd airflow
astro dev start
```

The Airflow UI runs at http://localhost:8080. The backend reads the tables this pipeline writes, so a fresh database has nothing to show until the training DAG (`housing_data_training`) has run once.

## Tests

```bash
pytest backend/tests
cd frontend && npm run test:unit
```

GitHub Actions runs the frontend tests and a TypeScript type check on changes to `frontend/`, and the backend tests on pushes to `main` that change `backend/`.

## Data sources

- Rental listings: [Cornell University Off-Campus Housing](https://offcampus.housing.cornell.edu)
- Bus routes and stops: TCAT's public GTFS feed
- Parcels, assessments and ownership: Tompkins County
- Neighborhood geography: [CUGIR](https://cugir.library.cornell.edu), Cornell's geospatial data repository
- Map tiles: [Jawg](https://www.jawg.io), with map data © OpenStreetMap contributors

## Contact

Questions about the data or the model go through the [contact page](https://ithacainsights.com/contact). Bugs and feature ideas can go in GitHub issues.

Ithaca Insights is built by [Maitrix Labs](https://maitrixlabs.com/).
