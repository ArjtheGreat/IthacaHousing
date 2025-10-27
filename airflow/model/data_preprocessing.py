import pandas as pd
import numpy as np

numerical_columns = [
    "LengthAvailable", "combined_bedrooms_bathrooms", "drive_time_urishall", "transit_score",
    "YR_BUILT_ENCODED"
]

def get_safety_rating_column(df):
    """Get the safety rating column name (handles multiple cases)"""
    if "Valid Certificate of Compliance" in df.columns:
        df["Valid Certificate of Compliance"] = df["Valid Certificate of Compliance"].replace({8: 1, float('nan'): 0})
        df = df.rename(columns={"Valid Certificate of Compliance": "valid_certificate_of_compliance"})
    
    if "valid_certificate_of_compliance" in df.columns:
        return "valid_certificate_of_compliance"
    elif "OverallSafetyRatingPct" in df.columns:
        return "OverallSafetyRatingPct"
    elif "overallsafetyratingpct" in df.columns:
        return "overallsafetyratingpct"
    else:
        return None

categorical_columns = [
    "Pets"
]

def calc_adjusted_bed_bath_values(apartments_for_rent):
    """
    Returns new combined bedroom and bathrooms columns
    """
    print("Calculating rent adjustments using extracted data...")    
    apartments_for_rent["bedroom_bathroom_ratio"] = 1.5*apartments_for_rent["Bedrooms"]/apartments_for_rent["Bathrooms"]
    apartments_for_rent["available_bedrooms_to_total_bedrooms_ratio"] = apartments_for_rent["available_bedrooms"]/apartments_for_rent["Bedrooms"]
    apartments_for_rent["available_bathrooms"] = round(apartments_for_rent["available_bedrooms"]/apartments_for_rent["bedroom_bathroom_ratio"])

    apartments_for_rent["combined_bedrooms_bathrooms"] = (
        1.5 * apartments_for_rent["available_bedrooms"] + apartments_for_rent["available_bathrooms"]
    )

    return apartments_for_rent

def add_property_features(apartments_for_rent):
    """
    Add property-specific features from ownership data
    """
    print("Adding property features from ownership data...")
    
    sqft_col = "assessment_sqft" if "assessment_sqft" in apartments_for_rent.columns else "SQ_FT"
    sale_price_col = "sale_price" if "sale_price" in apartments_for_rent.columns else "SALE_PRICE"
    
    if sqft_col in apartments_for_rent.columns and sale_price_col in apartments_for_rent.columns:
        valid_data = (apartments_for_rent[sqft_col] > 0) & (apartments_for_rent[sale_price_col] > 0) & \
                    pd.notna(apartments_for_rent[sqft_col]) & pd.notna(apartments_for_rent[sale_price_col])
        
        apartments_for_rent["sqft_per_sale_price"] = np.where(
            valid_data,
            np.sqrt(apartments_for_rent[sale_price_col] / apartments_for_rent[sqft_col]),
            np.nan
        )
        print(f"✅ Added sqft_per_sale_price feature for {valid_data.sum()} valid records")
    else:
        print("⚠️ assessment_sqft/SQ_FT or sale_price/SALE_PRICE columns not found, skipping sqft_per_sale_price calculation")
        apartments_for_rent["sqft_per_sale_price"] = np.nan

    # Encode year built
    def encode_year_built(year):
        """Encode year built into categorical values"""
        if pd.isna(year) or year == 0:
            return 0  
        elif year < 2000:
            return -1  
        else:
            return 1 
    
    year_built_col = "year_built" if "year_built" in apartments_for_rent.columns else "YR_BUILT"
    
    if year_built_col in apartments_for_rent.columns:
        apartments_for_rent["YR_BUILT_ENCODED"] = apartments_for_rent[year_built_col].apply(encode_year_built)
        print(f"✅ Added YR_BUILT_ENCODED feature")
    else:
        print("⚠️ year_built/YR_BUILT column not found, skipping year built encoding")
        apartments_for_rent["YR_BUILT_ENCODED"] = 0  

    return apartments_for_rent

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
            elif col == "drive_time_urishall":
                median = 30  # Default 30 minutes
            elif col == "transit_score":
                median = 50  # Default middle score
            elif col == "amenities_score":
                median = 50  # Default middle score
            elif col in ["OverallSafetyRatingPct", "overallsafetyratingpct"]:
                median = 70  # Default safety rating
            elif col == "valid_certificate_of_compliance":
                median = 0  # Default to 0 (no valid certificate)
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