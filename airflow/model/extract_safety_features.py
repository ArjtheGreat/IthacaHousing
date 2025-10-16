import json
import pandas as pd

def extract_safety_features(safety_json):
    """
    Parses the SafetyRatings JSON field and extracts structured columns.
    """
    try:
        if safety_json is None or pd.isna(safety_json):
            return {}

        if isinstance(safety_json, str):
            safety_json = json.loads(safety_json)

        overall_safety = safety_json.get("OverallSafetyRating", None)
        overall_safety_pct = safety_json.get("OverallSafetyRatingAsPercentage", None)

        category_scores = {list(entry.keys())[0]: list(entry.values())[0] for entry in safety_json.get("CategoryScores", [])}
        category_scores_pct = {f"{list(entry.keys())[0]}_pct": list(entry.values())[0] for entry in safety_json.get("CategoryScoresAsPercentage", [])}

        has_certificate = int(safety_json.get("HasValidCertificateOfOccupancy", False))
        meets_min_reqs = int(safety_json.get("MeetsMinimumRequirements", False))
        exceeds_reqs = int(safety_json.get("ExceedsRequirements", False))
        fire_resistant = int(safety_json.get("HasFireResistantConstructionType", False))
        satisfies_code = int(safety_json.get("SatisfiesApplicableCode", False))

        certificate_expiration = safety_json.get("CertificateExpirationDate", None)
        last_updated = safety_json.get("DateLastUpdated", None)

        extracted_data = {
            "OverallSafetyRating": overall_safety,
            "OverallSafetyRatingPct": overall_safety_pct,
            "HasValidCertificateOfOccupancy": has_certificate,
            "MeetsMinimumRequirements": meets_min_reqs,
            "ExceedsRequirements": exceeds_reqs,
            "HasFireResistantConstructionType": fire_resistant,
            "SatisfiesApplicableCode": satisfies_code,
            "CertificateExpirationDate": certificate_expiration,
            "DateLastUpdated": last_updated
        }

        extracted_data.update(category_scores)
        extracted_data.update(category_scores_pct)

        return extracted_data

    except Exception as e:
        print(f"⚠️ Error processing SafetyRatings: {e}")
        return {}


def calculate_safety_score(apartments_for_rent):
    """
    Calculates safety score for each row
    Args:
        apartments_for_rent: dataframe with housing data
    """
    apartments_for_rent["SafetyRatings"] = apartments_for_rent["SafetyRatings"].astype(str)

    safety_df = pd.json_normalize(apartments_for_rent["SafetyRatings"].apply(extract_safety_features))

    safety_df.index = apartments_for_rent.index

    apartments_for_rent = pd.concat([apartments_for_rent, safety_df], axis=1)

    if "Valid Certificate of Compliance" in apartments_for_rent.columns:
        print("🔍 Original values:", apartments_for_rent["Valid Certificate of Compliance"].head())
        print("🔍 Value counts:", apartments_for_rent["Valid Certificate of Compliance"].value_counts(dropna=False))
        
        apartments_for_rent["Valid Certificate of Compliance"] = apartments_for_rent["Valid Certificate of Compliance"].replace({8: 1})
        apartments_for_rent["Valid Certificate of Compliance"] = apartments_for_rent["Valid Certificate of Compliance"].fillna(0)
        
        apartments_for_rent["Valid Certificate of Compliance"] = apartments_for_rent["Valid Certificate of Compliance"].astype(int)
        
        apartments_for_rent = apartments_for_rent.rename(columns={"Valid Certificate of Compliance": "valid_certificate_of_compliance"})
        
        print("✅ After processing:", apartments_for_rent["valid_certificate_of_compliance"].head())
        print("✅ Final value counts:", apartments_for_rent["valid_certificate_of_compliance"].value_counts(dropna=False))
    
    return apartments_for_rent