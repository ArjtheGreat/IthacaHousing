import pandas as pd
import fetch_housing_data
import calculate_amenity_score
import calculate_travel_times_distance
import calculate_transit_score
import data_preprocessing
import extract_safety_features
import model_training
import comparative_market_analysis
import insert_into_postgredb


DATA_PATH = "./insert_into_postgres.csv"

def housing_data_pipeline():
    """
    Call the Pipeline for Data Preprocessing for Apache Airflow
    
    Part 1:
        Fetch Data
    Part 2
        Set up data for regression
    Part 3:
        Pre-process and transform data
    Part 4:
        Perform CMA and Regression, insert into DB
    """

    # Part 1
    apartments_for_rent = fetch_housing_data.housing_data_preprocessing()
    
    # Part 2
    apartments_for_rent = calculate_travel_times_distance.compute_all_travel_times(apartments_for_rent)
    apartments_for_rent = calculate_transit_score.calculate_transit_score(apartments_for_rent)
    apartments_for_rent = calculate_amenity_score.calculate_amenity_score(apartments_for_rent)
    apartments_for_rent = extract_safety_features.calculate_safety_score(apartments_for_rent)

    # Part 3
    X, y = model_training.define_X_Y_variables(apartments_for_rent)

    X = data_preprocessing.median_mode_imputation(X)
    # X = data_preprocessing.outlier_imputation(X)
    y = data_preprocessing.log_transform_prices(y)

    X_with_spatial = model_training.get_spatial_coefficients(X, apartments_for_rent)

    # Part 4
    apartments_for_rent = comparative_market_analysis.perform_cma(X_with_spatial, apartments_for_rent)
    apartments_for_rent = model_training.spatial_random_forest_regressor(X_with_spatial, y, apartments_for_rent)
    insert_into_postgredb.psql_insert_copy(apartments_for_rent)

    return apartments_for_rent