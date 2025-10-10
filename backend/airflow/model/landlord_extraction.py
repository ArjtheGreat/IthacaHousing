import re
import pandas as pd
import os
from pathlib import Path

MODEL_PATH = "/opt/airflow/model"
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = str(Path(__file__).resolve().parent)

csv_path = os.path.join(MODEL_PATH, "Tompkins_County_Ownership.csv")
address_ownership_df = pd.read_csv(csv_path, on_bad_lines='skip')

def standardize_street_names(address_series):
    """Standardize street name abbreviations for consistent matching"""
    replacements = {
        "STREET": "ST", "AVENUE": "AVE", "BOULEVARD": "BLVD", "PLACE": "PL",
        "ROAD": "RD", "DRIVE": "DR", "COURT": "CT", "LANE": "LN",
        "TERRACE": "TER", "PARKWAY": "PKWY", "CIRCLE": "CIR", "HIGHWAY": "HWY",
        "SQUARE": "SQ", "TRAIL": "TRL", "CENTER": "CTR", "EXPRESSWAY": "EXPY",
        "MOUNT": "MT", "FORT": "FT", "EAST": "E", "NORTH": "N",
        "WEST": "W", "SOUTH": "S"
    }

    def replace_words(address):
        if pd.isna(address):
            return address
        address = address.upper().strip()
        for full, abbr in replacements.items():
            address = re.sub(rf"\b{full}\b", abbr, address)
        return address

    return address_series.apply(replace_words)

def clean_address_series(address_series):
    """Clean and normalize addresses for matching"""
    def normalize_directionals(addr):
        if pd.isna(addr):
            return addr
        addr = addr.upper().strip()
        
        # Fix directional placement
        addr = re.sub(r"^(\d+)([NSEW])\b", r"\1 \2", addr)
        addr = re.sub(
            r"^(\d+)\s+([NSEW])\s+([A-Z ]+?)\s+(ST|STREET|AVE|AVENUE|RD|ROAD|DR|DRIVE|BLVD|BOULEVARD|LN|LANE|CT|COURT|PL|PLACE|TER|TERRACE|CIR|CIRCLE|PKWY|PARKWAY)\b",
            r"\1 \3 \4 \2",
            addr,
        )
        addr = re.sub(r"\s{2,}", " ", addr).strip()
        return addr

    def clean(addr):
        if pd.isna(addr):
            return addr
        
        addr = addr.upper().strip()
        addr = addr.replace("\n", " ").replace("\r", " ")
        
        addr = re.sub(r'[.,]', '', addr)
        addr = re.sub(r'\(.*?\)', '', addr)
        
        addr = re.sub(r'\b(APT|UNIT|#)\s*\d+\b', '', addr)
        addr = re.sub(r'\b(BLDG|BUILDING|REAR|FRONT|LOWER|UPPER|BASEMENT|FLOOR|FL)\b.*', '', addr)
        
        addr = re.sub(r"\b(ITHACA|CORNELL|TOMPKINS|NEWFIELD|TRUMANSBURG|LANSING|GROTON|DRYDEN)\s+NY\b.*$", "", addr)
        
        addr = re.sub(r'(\d+)\s*(?:&|AND)\s*\d+[A-Z]?\s+', r'\1 ', addr)
        addr = re.sub(r'(\d+)\s*-\s*\d+[A-Z]?', r'\1', addr)
        addr = re.sub(r'.*-\s*([A-Z]+\s+(ST|AVE|RD|LN|CT|BLVD|TER|PL|PKWY|DR))', r'\1', addr)
        
        addr = normalize_directionals(addr)
        addr = re.sub(r'\s{2,}', ' ', addr)
        return addr.strip()

    address_series = address_series.apply(clean)
    return standardize_street_names(address_series)

def split_address_components(address_series):
    """Split addresses into house number ranges and street core"""
    def extract_parts(addr):
        if pd.isna(addr):
            return [None, None, None]
        
        addr = addr.strip()
        
        # Handle address ranges (e.g., "100-200 Main St")
        range_match = re.match(r"(\d+)\s*-\s*(\d+)", addr)
        if range_match:
            start, end = map(int, range_match.groups())
            base_street = re.sub(r"^\d+\s*-\s*\d+\s*", "", addr)
            return [start, end, base_street.strip()]

        # Handle single addresses (e.g., "100 Main St")
        single_match = re.match(r"(\d+)\s+(.*)", addr)
        if single_match:
            num = int(single_match.group(1))
            base_street = single_match.group(2).strip()
            return [num, num, base_street]

        return [None, None, addr]

    results = address_series.apply(extract_parts)
    
    house_start = results.apply(lambda x: x[0])
    house_end = results.apply(lambda x: x[1])
    street_core = results.apply(lambda x: x[2])
    
    return house_start, house_end, street_core

def match_address(row, ownership_df, tolerance=0):
    """Match a listing address to ownership data"""
    same_street = ownership_df[
        ownership_df["StreetCore"] == row["StreetCore"]
    ]
    if same_street.empty:
        return None

    for _, cand in same_street.iterrows():
        if cand["HouseNumStart"] <= row["HouseNumStart"] <= cand["HouseNumEnd"]:
            return cand["Owner Name"]
        if abs(cand["HouseNumStart"] - row["HouseNumStart"]) <= tolerance:
            return cand["Owner Name"]
    return None

def extract_landlord_names(apartments_for_rent):
    """
    Extract landlord/owner names for apartments_for_rent dataframe
    Returns only owner_name column, with "Not Found" for unmatched addresses
    """
    print("🏠 Extracting landlord names...")
    
    apartments_for_rent["ListingAddress_formatted"] = clean_address_series(apartments_for_rent["ListingAddress"])
    address_ownership_df["Address_Formatted"] = clean_address_series(address_ownership_df["Address"])
    
    apt_house_start, apt_house_end, apt_street_core = split_address_components(apartments_for_rent["ListingAddress_formatted"])
    own_house_start, own_house_end, own_street_core = split_address_components(address_ownership_df["Address_Formatted"])
    
    apartments_for_rent["HouseNumStart"] = apt_house_start
    apartments_for_rent["HouseNumEnd"] = apt_house_end
    apartments_for_rent["StreetCore"] = apt_street_core
    
    address_ownership_df["HouseNumStart"] = own_house_start
    address_ownership_df["HouseNumEnd"] = own_house_end
    address_ownership_df["StreetCore"] = own_street_core
    
    def match_owner_name(row):
        owner = match_address(row, address_ownership_df)
        return owner if owner else "Not Found"
    
    apartments_for_rent["owner_name"] = apartments_for_rent.apply(match_owner_name, axis=1)
    
    apartments_for_rent.drop(columns=["ListingAddress_formatted", "HouseNumStart", "HouseNumEnd", "StreetCore"], inplace=True)
    
    print(f"✅ Extracted landlord names for {len(apartments_for_rent)} listings")
    matched_count = (apartments_for_rent["owner_name"] != "Not Found").sum()
    print(f"📊 Successfully matched {matched_count}/{len(apartments_for_rent)} listings to owners")
    
    return apartments_for_rent