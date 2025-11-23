import json
import os
import glob
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# Path to ward JSON files
ward_jsons_path = "/Users/devandev/Desktop/ward_jsons"

# Load CSV mapping
import csv

csv_path = "/Users/devandev/Desktop/ward_jsons/LSG Mapped - Sheet1.csv"

# Map LBName to Org District
lb_to_district = {}

print("📖 Reading CSV mapping...")
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        lb_name = row['LBName'].strip()
        district = row['Org District'].strip()
        lb_to_district[lb_name] = district

print(f"✅ Loaded {len(lb_to_district)} LB to District mappings\n")

# Collect geometries by district
district_geometries = {}

print("🗺️ Processing ward JSON files...")

# Find all JSON files recursively
for root, dirs, files in os.walk(ward_jsons_path):
    for file in files:
        if file.endswith('.json') and not file.startswith('.'):
            file_path = os.path.join(root, file)
            lb_name = os.path.splitext(file)[0]
            
            # Get district for this LB
            district = lb_to_district.get(lb_name)
            
            if not district:
                print(f"⚠️  No district mapping for: {lb_name}")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if 'features' in data:
                        for feature in data['features']:
                            geom = shape(feature['geometry'])
                            
                            if district not in district_geometries:
                                district_geometries[district] = []
                            
                            district_geometries[district].append(geom)
                
                print(f"✅ Processed: {lb_name} → {district}")
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

print(f"\n📊 Found {len(district_geometries)} districts with geometries\n")

# Create unified GeoJSON with all districts
print("🔧 Creating unified Kerala districts GeoJSON...")

features = []

for district_name, geometries in district_geometries.items():
    if geometries:
        try:
            # Union all geometries for this district
            print(f"   Merging {len(geometries)} geometries for {district_name}...")
            district_boundary = unary_union(geometries)
            
            # Create clean district ID
            district_id = district_name.lower().replace(' ', '_')
            
            feature = {
                'type': 'Feature',
                'properties': {
                    'district_id': district_id,
                    'district_name': district_name,
                    'geometries_count': len(geometries)
                },
                'geometry': mapping(district_boundary)
            }
            
            features.append(feature)
            print(f"   ✅ Created boundary for {district_name}")
            
        except Exception as e:
            print(f"   ❌ Error creating boundary for {district_name}: {e}")

# Create final GeoJSON
kerala_geojson = {
    'type': 'FeatureCollection',
    'features': features
}

# Save to file
os.makedirs('data', exist_ok=True)
output_path = 'data/kerala_districts.geojson'

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(kerala_geojson, f, indent=2)

print(f"\n✅ Kerala districts boundary saved to: {output_path}")
print(f"📊 Total districts: {len(features)}")

# Also save individual district boundaries
print("\n🔧 Creating individual district boundary files...")

for feature in features:
    district_id = feature['properties']['district_id']
    district_dir = f"data/{district_id}"
    os.makedirs(district_dir, exist_ok=True)
    
    district_geojson = {
        'type': 'FeatureCollection',
        'features': [feature]
    }
    
    district_path = f"{district_dir}/district_boundary.geojson"
    with open(district_path, 'w', encoding='utf-8') as f:
        json.dump(district_geojson, f, indent=2)
    
    print(f"✅ {feature['properties']['district_name']} → {district_path}")

print("\n" + "="*70)
print("🎉 District boundaries created successfully!")
print("="*70)
print(f"Main file: {output_path}")
print(f"Individual files: data/[district_id]/district_boundary.geojson")
print("="*70)
