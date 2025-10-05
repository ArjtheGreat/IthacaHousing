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

    fillna_dict = {}
    if "overallsafetyratingpct" in apartments_for_rent.columns:
        fillna_dict["overallsafetyratingpct"] = apartments_for_rent["overallsafetyratingpct"].mean()
    if "HasValidCertificateOfOccupancy" in apartments_for_rent.columns:
        fillna_dict["HasValidCertificateOfOccupancy"] = 0
    if "MeetsMinimumRequirements" in apartments_for_rent.columns:
        fillna_dict["MeetsMinimumRequirements"] = 0
    if "ExceedsRequirements" in apartments_for_rent.columns:
        fillna_dict["ExceedsRequirements"] = 0
    if "HasFireResistantConstructionType" in apartments_for_rent.columns:
        fillna_dict["HasFireResistantConstructionType"] = 0
    if "SatisfiesApplicableCode" in apartments_for_rent.columns:
        fillna_dict["SatisfiesApplicableCode"] = 0
    
    if fillna_dict:
        apartments_for_rent.fillna(fillna_dict, inplace=True)
    
    return apartments_for_rent