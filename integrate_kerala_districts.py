#!/usr/bin/env python3
"""
Process Kerala_districts.geojson to extract 14 main districts and make them crack-free
"""

import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

print("=" * 80)
print("🔧 PROCESSING YOUR KERALA DISTRICTS FILE")
print("=" * 80)

# Load your Kerala_districts.geojson
with open('Kerala_districts.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\n📂 Loaded {len(data['features'])} features")

# Extract the 14 main districts (admin_level = 5)
main_districts = []
district_names = set()

for feature in data['features']:
    props = feature['properties']
    
    # Check if it's a main district (admin_level 5)
    if props.get('admin_level') == '5' and props.get('boundary') == 'administrative':
        name = props.get('name', '').replace(' district', '').replace(' District', '')
        
        # Kerala has 14 main districts - filter by these names
        kerala_districts = [
            'Thiruvananthapuram', 'Kollam', 'Pathanamthitta', 'Alappuzha',
            'Kottayam', 'Idukki', 'Ernakulam', 'Thrissur', 'Palakkad',
            'Malappuram', 'Kozhikode', 'Wayanad', 'Kannur', 'Kasaragod'
        ]
        
        # Exclude non-district features
        if name in kerala_districts and name not in district_names:
            district_names.add(name)
            # Store with clean name
            feature['properties']['name'] = name
            main_districts.append(feature)
            print(f"   ✅ Found: {name}")

print(f"\n📊 Extracted {len(main_districts)} main districts")

# Process each district to remove cracks
fixed_features = []
for feature in main_districts:
    district_name = feature['properties']['name']
    print(f"\n🔧 Processing {district_name}...")
    
    # Convert to shapely geometry
    geom = shape(feature['geometry'])
    
    # Apply buffer to close gaps (0.005 degrees ≈ 555 meters)
    print(f"   → Applying 555m buffer to close gaps...")
    buffered = geom.buffer(0.005).buffer(-0.005)
    
    # Simplify to reduce complexity while preserving topology
    print(f"   → Simplifying geometry...")
    simplified = buffered.simplify(0.0001, preserve_topology=True)
    
    # Create new feature with clean properties
    district_id = district_name.lower().replace(' ', '')
    
    new_feature = {
        'type': 'Feature',
        'properties': {
            'district': district_id,
            'name': district_name,
            'st_nm': 'Kerala',
            'st_code': '32'
        },
        'geometry': mapping(simplified)
    }
    
    fixed_features.append(new_feature)
    print(f"   ✅ Done - {simplified.geom_type}")

# Create output GeoJSON
output_data = {
    'type': 'FeatureCollection',
    'features': fixed_features
}

# Save to data directory
output_file = 'data/kerala_14_districts_fixed.geojson'
print(f"\n💾 Saving to: {output_file}")

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f)

file_size = len(json.dumps(output_data)) / (1024 * 1024)
print(f"✅ Done! File size: {file_size:.2f} MB")
print(f"✅ Created crack-free 14 districts map!")
print("=" * 80)
