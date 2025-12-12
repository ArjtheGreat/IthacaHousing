# Model Directory Structure

This directory contains the housing data pipeline and related modules, organized into logical subdirectories.

## Directory Structure

```
model/
├── core/                    # Core pipeline and utility modules
│   ├── pipeline.py          # Main pipeline orchestrator (moved to root for backward compatibility)
│   ├── fetch_housing_data.py
│   ├── geocoder.py
│   ├── insert_into_postgredb.py
│   ├── landlord_extraction.py
│   └── pipeline_metrics.py
│
├── extractors/              # Feature extraction modules
│   ├── extract_land_assessment_features.py
│   ├── extract_poi_features.py
│   ├── extract_rental_data.py
│   └── extract_safety_features.py
│
├── calculators/             # Score and calculation modules
│   ├── calculate_amenity_score.py
│   ├── calculate_transit_score.py
│   └── calculate_travel_times_distance.py
│
├── ml/                      # Machine learning modules
│   ├── data_preprocessing.py
│   ├── model_training.py
│   ├── comparative_market_analysis.py
│   └── spatial_regression.py
│
├── data/                    # Data files (CSV, GeoJSON, ZIP)
│   ├── *.csv
│   ├── *.geojson
│   └── *.zip
│
└── pipeline.py              # Main pipeline (imports from subdirectories)

```

## Import Guidelines

When importing modules within the model directory, use the subdirectory structure:

```python
# In pipeline.py or DAGs
import core.fetch_housing_data as fetch_housing_data
import extractors.extract_safety_features as extract_safety_features
import calculators.calculate_transit_score as calculate_transit_score
import ml.model_training as model_training
```

## Notes

- `pipeline.py` is kept at the root level for backward compatibility with existing DAGs
- All data files are stored in the `data/` subdirectory
- Each subdirectory has an `__init__.py` file to make it a Python package

