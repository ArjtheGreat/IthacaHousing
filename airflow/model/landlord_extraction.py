import re
from openai import OpenAI
import pandas as pd
import os
from pathlib import Path
import json
import time

MODEL_PATH = "/opt/airflow/model"
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = str(Path(__file__).resolve().parent)

def load_ownership_data():
    """Load ownership data with proper path handling"""
    model_path = "/opt/airflow/model"
    if not os.path.exists(model_path):
        model_path = str(Path(__file__).resolve().parent)
    
    csv_path = os.path.join(model_path, "Tompkins_County_Ownership.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Ownership CSV file not found at: {csv_path}")
    
    return pd.read_csv(csv_path, on_bad_lines="skip")

def load_assessment_data():
    """Load assessment data with proper path handling"""
    model_path = "/opt/airflow/model"
    if not os.path.exists(model_path):
        model_path = str(Path(__file__).resolve().parent)
    
    csv_path = os.path.join(model_path, "TompkinsCountyMergedData.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Assessment CSV file not found at: {csv_path}")
    
    return pd.read_csv(csv_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = None
if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize OpenAI client: {e}")
        client = None
else:
    print("Warning: OPENAI_API_KEY environment variable not set")

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

def match_address(row, ownership_df, columns_to_add=None, tolerance=0):
    """
    Matches a apartments_for_rent row to an ownership_df record by street + house number.
    Returns a dict of {col: value} for selected columns.
    """
    same_street = ownership_df[ownership_df["StreetCore"] == row["StreetCore"]]
    if same_street.empty:
        return {col: None for col in (columns_to_add or [])}

    for _, cand in same_street.iterrows():
        if cand["HouseNumStart"] <= row["HouseNumStart"] <= cand["HouseNumEnd"]:
            return {col: cand[col] for col in (columns_to_add or [])}
        if abs(cand["HouseNumStart"] - row["HouseNumStart"]) <= tolerance:
            return {col: cand[col] for col in (columns_to_add or [])}

    return {col: None for col in (columns_to_add or [])}

def process_prompt_for_landlord(landlords):
    """
    Normalize a landlord list using the OpenAI API.
    
    Args:
        landlords (list or str): Raw landlord names or text to normalize.
    
    Returns:
        dict: {
            "landlords": [cleaned names],
            "error": None or error message
        }
    """
    try:
        if isinstance(landlords, list):
            landlords = ", ".join(str(x) for x in landlords)

        prompt = f"""
        The following may include duplicates, variations, or noise.
        Normalize it into a clean Python list of unique landlord names (no quotes in the names):
        {landlords}
        """

        response_text = get_openai_response_for_landlord_extraction(
            model_name="gpt-4.1-mini",
            prompt=prompt
        )

        try:
            landlords_list = json.loads(response_text.replace("'", '"'))
        except json.JSONDecodeError:
            landlords_list = [
                x.strip().strip('"').strip("'")
                for x in response_text.strip("[]").split(",")
                if x.strip()
            ]

        return landlords_list

    except Exception as e:
        print(f"❌ Error processing landlord prompt: {e}")
        return {"landlords": [], "error": str(e)}


def get_openai_response_for_landlord_extraction(
    model_name: str,
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 300,
    max_retries: int = 3
):
    """
    Query the OpenAI API to extract structured landlord names with retries and fallback.
    """
    if client is None:
        raise RuntimeError("❌ OpenAI client not initialized. Check OPENAI_API_KEY environment variable.")
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are a rental data normalizer.\n"
                "Return a single valid Python list of unique landlord names.\n"
                "No commentary, no quotes around list elements.\n"
                'Example: ["John Kimball", "Mary Kimball"]'
            ),
        },
        {"role": "user", "content": prompt},
    ]

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"⚠️ OpenAI API error (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(2 * (attempt + 1))

    raise RuntimeError("❌ Failed to get response from OpenAI after multiple retries.")

def prepare_ownership_data():
    """
    Prepare and process ownership data once to avoid duplicate computation
    Returns processed address_ownership_unique dataframe
    """
    print("🔄 Preparing ownership data...")
    address_ownership_df = load_ownership_data()
    tompkins_assessment_data = load_assessment_data()
    
    address_ownership_df_merged = address_ownership_df.merge(tompkins_assessment_data, left_on="Tax ID", right_on="PRINTKEY", how="left")
    address_ownership_unique = address_ownership_df_merged.drop_duplicates(subset="Tax ID", keep="first")

    address_ownership_unique["Address_Formatted"] = clean_address_series(address_ownership_unique["Address"])
    
    apt_house_start, apt_house_end, apt_street_core = split_address_components(address_ownership_unique["Address_Formatted"])
    
    address_ownership_unique["HouseNumStart"] = apt_house_start
    address_ownership_unique["HouseNumEnd"] = apt_house_end
    address_ownership_unique["StreetCore"] = apt_street_core
    
    column_rename_map = {
        'NEIGHB': 'neighborhood_assessment',
        'DEPTH': 'property_depth',
        'FRONTAGE': 'property_frontage',
        'ACRES': 'property_acres',
        'PC': 'property_pc',
        'WATER': 'water_access',
        'SEWER': 'sewer_access',
        'SWRESNAME': 'sewer_name',
        'YR_BUILT': 'year_built',
        'SALE_PRICE': 'sale_price',
        'SQ_FT': 'assessment_sqft'
    }
    address_ownership_unique = address_ownership_unique.rename(columns=column_rename_map)
    
    print("✅ Ownership data prepared")
    return address_ownership_unique

def extract_address_data(apartments_for_rent):
    """
    Prepare apartment data by cleaning addresses and splitting components
    """
    print("🔄 Preparing apartment data...")
    
    apartments_for_rent["ListingAddress_formatted"] = clean_address_series(apartments_for_rent["ListingAddress"])
    
    house_start, house_end, street_core = split_address_components(apartments_for_rent["ListingAddress_formatted"])
    apartments_for_rent["HouseNumStart"] = house_start
    apartments_for_rent["HouseNumEnd"] = house_end
    apartments_for_rent["StreetCore"] = street_core
    
    print("✅ Apartment data prepared")
    return apartments_for_rent


def add_property_details(apartments_for_rent):
    """
    Add property details from Tompkins County assessment data to apartments_for_rent dataframe
    Returns dataframe with additional property columns
    """
    print("🏠 Adding property details from assessment data...")
    address_ownership_unique = prepare_ownership_data()
    apartments_for_rent = extract_address_data(apartments_for_rent)

    columns_to_add = [
        "neighborhood_assessment",
        "property_depth",
        "property_frontage",
        "property_acres",
        "property_pc",
        "water_access",
        "sewer_access",
        "sewer_name",
        "year_built",
        "sale_price",
        "assessment_sqft"
    ]
    matches = apartments_for_rent.apply(
        lambda r: match_address(r, address_ownership_unique, columns_to_add=columns_to_add),
        axis=1
    )

    matches_df = pd.DataFrame(list(matches))
    apartments_for_rent = pd.concat([apartments_for_rent, matches_df], axis=1)
    
    temp_columns = ["ListingAddress_formatted", "HouseNumStart", "HouseNumEnd", "StreetCore"]
    for col in temp_columns:
        if col in apartments_for_rent.columns:
            apartments_for_rent.drop(columns=[col], inplace=True)
    
    print(f"✅ Added property details for {len(apartments_for_rent)} listings")
    
    return apartments_for_rent


def extract_landlord_names(apartments_for_rent):
    """
    Extract landlord/owner names for apartments_for_rent dataframe
    Returns only owner_name column, with "Not Found" for unmatched addresses
    """
    print("🏠 Extracting landlord names...")
    address_ownership_unique = prepare_ownership_data()
    apartments_for_rent = extract_address_data(apartments_for_rent)

    columns_to_add = ["Owner Name"]
    matches = apartments_for_rent.apply(
        lambda r: match_address(r, address_ownership_unique, columns_to_add=columns_to_add),
        axis=1
    )

    matches_df = pd.DataFrame(list(matches))
    apartments_for_rent = pd.concat([apartments_for_rent, matches_df], axis=1)

    def process_owner_name(row):
        """Process owner name for a single row"""
        if pd.notna(row.get("Owner Name")):
            return str(row["Owner Name"])
        else:
            return "Not Found"
    
    apartments_for_rent["owner_name"] = apartments_for_rent.apply(process_owner_name, axis=1)
    
    temp_columns = ["ListingAddress_formatted", "HouseNumStart", "HouseNumEnd", "StreetCore"]
    for col in temp_columns:
        if col in apartments_for_rent.columns:
            apartments_for_rent.drop(columns=[col], inplace=True)
    
    print(f"✅ Extracted landlord names for {len(apartments_for_rent)} listings")
    matched_count = (apartments_for_rent["owner_name"] != "Not Found").sum()
    print(f"📊 Successfully matched {matched_count}/{len(apartments_for_rent)} listings to owners")
    
    return apartments_for_rent
    