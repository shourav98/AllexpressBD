import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Allexpress.settings')
django.setup()

import logging
from parcel.pathao_integration import PathaoAPIClient

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO)

def test_pathao_api():
    print("Testing Pathao API connection...")
    
    client = PathaoAPIClient()
    print(f"Access token: {client.access_token}")
    
    if not client.access_token:
        print("Authentication failed")
        print(f"Base URL: {client.base_url}")
        print(f"Client ID: {client.client_id}")
        print(f"Store ID: {client.store_id}")
        return False

    print("Authentication successful")
    
    # Test cities endpoint with more details
    print("\n--- Testing Cities Endpoint ---")
    cities = client.get_cities()
    print(f"Cities API response: {cities}")
    
    if cities:
        print(f"Cities API working - found {len(cities)} cities")
        
        # Test zones endpoint for first city
        city_id = cities[0].get('city_id')
        city_name = cities[0].get('city_name')
        print(f"\n--- Testing Zones for City {city_name} (ID: {city_id}) ---")
        
        zones = client.get_zones(city_id)
        print(f"Zones API response: {zones}")
        
        if zones:
            print(f"Zones API working - found {len(zones)} zones")
            
            # Test areas endpoint for first zone
            zone_id = zones[0].get('zone_id')
            zone_name = zones[0].get('zone_name')
            print(f"\n--- Testing Areas for Zone {zone_name} (ID: {zone_id}) ---")
            
            areas = client.get_areas(zone_id)
            print(f"Areas API response: {areas}")
            
            if areas:
                print(f"✅ Areas API working - found {len(areas)} areas")
            else:
                print("Areas API not working")
        else:
            print("Zones API not working")
    else:
        print("Cities API not working")
    
    return True

if __name__ == "__main__":
    test_pathao_api()