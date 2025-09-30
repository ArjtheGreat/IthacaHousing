import pandas as pd
import numpy as np

numerical_columns = [
    "LengthAvailable", "combined_bedrooms_bathrooms", "drive_time", "transit_score", "amenities_score", "OverallSafetyRating"
]

categorical_columns = [
    "Pets"
]
def clean_up_x_y(X, y):
    """
    Just a bit of clean up for X and y
    """
    X_clean = X.copy()
    for col in X_clean.columns:
        X_clean[col] = pd.to_numeric(X_clean[col], errors='coerce')
    X_clean = X_clean.fillna(X_clean.median())
    X_clean = X_clean.astype('float64')
    
    y_clean = pd.to_numeric(y, errors='coerce')
    y_clean = y_clean.fillna(y_clean.median())
    y_clean = y_clean.astype('float64')

    return  X_clean, y_clean
    
def median_mode_imputation(X):
    """
    Median Imputation for Numerical Columns
    Mode imputation for Categorical Columns
    Args:
        X: dataframe with training housing data
    """

    # For Numerical Categories, use Median Imputation
    for col in numerical_columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")
        median = X[col].median()
        
        if pd.isna(median):
            if col == "LengthAvailable":
                median = 12  # Default 12 months
            elif col == "combined_bedrooms_bathrooms":
                median = 3.0  # Default 2 bedrooms + 1 bathroom
            elif col == "drive_time":
                median = 30  # Default 30 minutes
            elif col == "transit_score":
                median = 50  # Default middle score
            elif col == "amenities_score":
                median = 50  # Default middle score
            elif col == "OverallSafetyRating":
                median = 70  # Default safety rating
            else:
                median = 0  # Default fallback
        
        X.fillna({col: median}, inplace=True)

    # For Categorical Categories, use Mode Imputation
    for col in categorical_columns:
        mode_series = X[col].mode()
        if len(mode_series) > 0:
            mode = mode_series[0]
        else:
            non_null_values = X[col].dropna()
            if len(non_null_values) > 0:
                mode = non_null_values.value_counts().index[0]
            else:
                mode = "No" 
        X.fillna({col: mode}, inplace=True)
    
    X["Pets"] = X["Pets"].map({"No": 0, "Yes": 1})

    return X

def outlier_imputation(X):
    """
    Median Imputation for Outliers
    Outliers defined by IQR fence (Median - 1.5*QI, Median + 1.5*Q3)
    Args:
        X: dataframe with training housing data
    """
    threshold = 1.5

    q1 = X[numerical_columns].quantile(0.25)
    q3 = X[numerical_columns].quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - threshold * iqr
    upper_bound = q3 + threshold * iqr

    for col in numerical_columns:
        median_value = X[col].median()
        X[col] = X[col].mask(
            (X[col] < lower_bound[col]) | (X[col] > upper_bound[col]),
            median_value
        )

    return X


def log_transform_prices(y):
    y = pd.to_numeric(y, errors='coerce')
    y = np.log(y)

    return y