from airflow.decorators import dag, task
from pendulum import datetime, duration
import pandas as pd
import os
import sys

# Add model directory to path
MODEL_PATH = "/opt/airflow/model"
if not os.path.exists(MODEL_PATH):
    current_file = str(__file__) if isinstance(__file__, bytes) else __file__
    MODEL_PATH = os.path.join(os.path.dirname(current_file), "..", "model")
sys.path.append(MODEL_PATH)

from insert_into_postgredb import psql_insert_copy

@dag(
    dag_id="test_insert_db",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    description="Test if insert_into_postgredb function works",
    default_args={"owner": "airflow", "retries": 1, "retry_delay": duration(minutes=5)},
    tags=["test", "database"]
)
def test_insert_db():
    
    @task
    def test_insert_db_function():
        """
        Test the insert_into_postgredb function with sample data
        """
        print("🧪 Testing insert_into_postgredb function...")
        
        # Create sample test data
        test_data = {
            'ListingId': ['TEST001', 'TEST002'],
            'ListingAddress': ['123 Test St', '456 Test Ave'],
            'ListingCity': ['Ithaca', 'Ithaca'],
            'ListingZip': ['14850', '14850'],
            'CreateDate': ['2024-01-01', '2024-01-01'],
            'ShortDescription': ['Test listing 1', 'Test listing 2'],
            'RentAmount': [1000, 1200],
            'RentType': ['per_person', 'per_person'],
            'Pets': [True, False],
            'Amenities': ['["wifi", "parking"]', '["wifi"]'],
            'Bedrooms': [2, 3],
            'Bathrooms': [1, 2],
            'available_bedrooms': [2, 3],
            'available_bathrooms': [1, 2],
            'HousingType': ['apartment', 'house'],
            'latitude': [42.4480, 42.4490],
            'longitude': [-76.4820, -76.4830],
            'ListingPhotos': ['["photo1.jpg"]', '["photo2.jpg"]'],
            # Route columns removed - not available in current data
            'transit_score': [85.5, 72.3],
            'amenities_score': [78.2, 82.1],
            'valid_certificate_of_compliance': [0, 1],
            'PredictedRent': [950, 1150],
            'DifferenceinFairValue': [50, 50],
            'predicted_rent_cma': [975, 1175],
            'nearest_neighbor_listingIds': ['["ID1", "ID2"]', '["ID3", "ID4"]'],
            'rent_per_person': [500, 400],
            'num_people': [2, 3],
            'total_rent_amount': [1000, 1200],
            'owner_name': ['Test Owner 1', 'Test Owner 2'],
            'nearest_stop_name': ['Test Stop 1', 'Test Stop 2'],
            'walk_time_to_nearest_stop': [2.5, 3.1],
            'transit_time_to_ag_quad': [8.5, 12.3],
            'transit_time_to_arts_quad': [10.2, 15.1],
            'transit_time_to_eng_quad': [9.8, 14.7]
        }
        
        test_df = pd.DataFrame(test_data)
        print(f"📊 Created test DataFrame with {len(test_df)} rows")
        
        try:
            # Test the function
            psql_insert_copy(test_df)
            print("✅ insert_into_postgredb function test PASSED!")
            return "SUCCESS"
        except Exception as e:
            print(f"❌ insert_into_postgredb function test FAILED: {e}")
            raise e

    # Execute the task
    test_insert_db_function()


# Instantiate the DAG
test_insert_db()
