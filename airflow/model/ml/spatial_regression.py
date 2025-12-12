
from spreg import ML_Lag
from libpysal.weights import KNN
import pandas as pd

def spatial_regression(X, y, apartments_for_rent):
    coords = apartments_for_rent[["latitude", "longitude"]].values
    knn_weights = KNN.from_array(coords, k=5)

    sar_model = ML_Lag(y, X, w=knn_weights, name_y="Log RentAmount", name_x=X.columns.tolist())

    sar_residuals = sar_model.u

    apartments_for_rent["SAR_Residuals"] = sar_residuals
    apartments_for_rent["Spatial_Lag"] = sar_model.predy

    # X = pd.concat([X, apartments_for_rent[["SAR_Residuals", "Spatial_Lag"]]], axis=1)
    X = pd.concat([X, apartments_for_rent[["SAR_Residuals"]]], axis=1)
    return X