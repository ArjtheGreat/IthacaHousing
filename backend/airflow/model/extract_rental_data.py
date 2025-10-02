from openai import OpenAI
import os
import json
import pandas as pd
import ast

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

api_key=os.getenv("OPENAI_API_KEY")

def process_prompt_for_rent_bedroom_extraction(num_bedrooms, num_bathrooms, rent, housing_type, rent_type, short_description):
    """
    Use the OpenAI API to extract normalized rental info and compute rent_per_person.

    Args:
        num_bedrooms (int): Number of bedrooms in the listing.
        num_bathrooms (int): Number of bathrooms in the listing.
        rent (float): The listed rent amount.
        rent_type (str): "Price Per Unit" or "Price Per Person".
        short_description (str): Short description of the rental.

    Returns:
        dict: Normalized info with available_bedrooms, available_bathrooms, rent_per_person.
    """
    try:
        full_prompt = f"""
        Short Description: {short_description}
        Number of Bedrooms: {num_bedrooms}
        Number of Bathrooms: {num_bathrooms}
        Rent: {rent}
        Rent Type: {rent_type}
        Housing Type: {housing_type}
        """

        response = get_openai_response_for_rent_bedroom_extraction(
            model_name="gpt-4.1-mini",
            prompt=full_prompt
        )

        # Ensure it's valid JSON
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            print("⚠️ Model returned invalid JSON. Raw response:", response)
            return {"error": "Invalid JSON", "raw": response}

        return parsed

    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}


def get_openai_response_for_rent_bedroom_extraction(model_name, prompt, temperature=0.2, max_tokens=300):
    """
    Query the OpenAI API to extract structured rental info.
    """
    if client is None:
        raise Exception("OpenAI client not initialized. Check OPENAI_API_KEY environment variable.")
    
    messages = [
        {
            "role": "system",
            "content": """
            You are a rental data normalizer.
            Rules for normalization:
            1. Always return **valid JSON only**. No text outside JSON. Keys must be: available_bedrooms, available_bathrooms, rent_per_person, num_people.
            2. The field `available_bedrooms` must reflect the number of bedrooms actually available to rent:
              - If the description says "1 bedroom in a 6 bedroom apartment", then available_bedrooms = 1 (NOT 6).
              - If it says "sublease of 2 rooms in a 5 bedroom apartment", then available_bedrooms = 2.
              - If housingtype == "Room to Rent", assume available_bedrooms = 1 unless the description explicitly states multiple rooms are available.
              - If housingtype == "Rent", then default to the provided bedroom count unless overridden by description.
            3. `available_bathrooms` = bathrooms provided, unless the description overrides it.
            4. Rent normalization:
              - If rent_type == "Price Per Person": rent_per_person = rent.
              - If rent_type == "Price Per Unit": rent_per_person = rent / available_bedrooms.
              - If bedrooms is missing or 0, rent_per_person = rent.
            5. `num_people` = the number of tenants implied in the description or by convention:
              - If description says "1 bedroom in a 6 bedroom apartment", num_people = 1.
              - If "shared room for 2" or similar phrasing, num_people = 2 (even if available_bedrooms = 1).
              - If rent_type == "Price Per Person", default num_people = available_bedrooms.
              - If rent_type == "Price Per Unit", default num_people = total bedrooms unless description says otherwise.
            6. If the description and numeric inputs conflict, the **description always overrides**.

            Example output (NO QUOTES, valid JSON):
            {
              "available_bedrooms": 1,
              "available_bathrooms": 2,
              "rent_per_person": 1000,
              "num_people": 1
            }
            """
        },
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"OpenAI API call failed: {str(e)}")


def safe_process(row, max_retries=5, delay=0.2):
    """
    Try calling the LLM with retries.
    If it keeps failing, fall back to deterministic calculation.
    """
    for attempt in range(max_retries):
        try:
            response = process_prompt_for_rent_bedroom_extraction(
                row["Bedrooms"],
                row["Bathrooms"],
                row["RentAmount"],
                row["RentType"],
                row["HousingType"],
                row["ShortDescription"]
            )
            
            if isinstance(response, dict):
                return response
            else:
                return json.loads(response)
        
        except Exception as e:
            print(f"Row {row.get('ListingId', 'NA')} attempt {attempt+1} failed: {e}")
            time.sleep(delay * (attempt + 1))  
    
    rent = row["RentAmount"]
    bedrooms = row["Bedrooms"] if row["Bedrooms"] else 1
    if row["RentType"] == "Price Per Person":
        rent_per_person = rent
    else:
        rent_per_person = rent / bedrooms if bedrooms else rent

    return {
        "available_bedrooms": bedrooms,
        "available_bathrooms": row["Bathrooms"],
        "rent_per_person": rent_per_person,
        "num_people": bedrooms if row["RentType"] == "Price Per Person" else bedrooms
    }


def extract_rental_data(apartments_for_rent):
    """
    Run Apply to extract rental data
    """
    apartments_for_rent["extracted_rental_data"] = apartments_for_rent.apply(
        safe_process, axis=1
    )

    apartments_for_rent["extracted_rental_data"] = apartments_for_rent["extracted_rental_data"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    extracted_df = pd.json_normalize(apartments_for_rent["extracted_rental_data"])

    apartments_for_rent = pd.concat([apartments_for_rent, extracted_df], axis=1)

    return apartments_for_rent
