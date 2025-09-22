import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Allexpress.settings')
django.setup()

from parcel.models import PathaoAPIClient

def test_pathao_api():
    print("Testing Pathao API connection...")
    
    client = PathaoAPIClient()
    print(f"Access token: {client.access_token}")
    
    if not client.access_token:
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful")
    
    # Test cities endpoint
    cities = client.get_cities()
    print(f"Cities API response: {cities}")
    
    if cities:
        print("✅ Cities API working")
        
        # Test zones endpoint for first city
        city_id = cities[0].get('city_id') or cities[0].get('id')
        zones = client.get_zones(city_id)
        print(f"Zones for city {city_id}: {zones}")
        
        if zones:
            print("✅ Zones API working")
            
            # Test areas endpoint for first zone
            zone_id = zones[0].get('zone_id') or zones[0].get('id')
            areas = client.get_areas(zone_id)
            print(f"Areas for zone {zone_id}: {areas}")
            
            if areas:
                print("✅ Areas API working")
            else:
                print("❌ Areas API not working")
        else:
            print("❌ Zones API not working")
    else:
        print("❌ Cities API not working")
    
    return True

if __name__ == "__main__":
    test_pathao_api()