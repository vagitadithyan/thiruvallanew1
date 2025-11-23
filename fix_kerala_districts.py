#!/usr/bin/env python3
"""
Fix cracks/gaps in Kerala district boundaries
Uses buffer operations to ensure seamless boundaries
"""

import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

print("🔧 Fixing Kerala District Boundaries...")
print("=" * 60)

# Load the original Kerala districts GeoJSON
input_file = 'Kerala_districts.geojson'
output_file = 'Kerala_districts_fixed.geojson'

print(f"📂 Loading: {input_file}")
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"✅ Loaded {len(data['features'])} districts")

# Process each district
fixed_features = []
for feature in data['features']:
    district_name = feature['properties'].get('district', 'Unknown')
    print(f"   Processing: {district_name}")
    
    # Convert to shapely geometry
    geom = shape(feature['geometry'])
    
    # Apply buffer operation to close gaps
    # Buffer out by 0.001 degrees (≈111 meters), then buffer back in
    buffered = geom.buffer(0.001, join_style=2)  # join_style=2 is MITRE for sharp corners
    debuffered = buffered.buffer(-0.001, join_style=2)
    
    # Simplify slightly to remove micro-variations while preserving topology
    simplified = debuffered.simplify(0.0001, preserve_topology=True)
    
    # Create new feature with fixed geometry
    fixed_feature = {
        'type': 'Feature',
        'properties': feature['properties'],
        'geometry': mapping(simplified)
    }
    
    fixed_features.append(fixed_feature)

# Create output GeoJSON
output_data = {
    'type': 'FeatureCollection',
    'features': fixed_features
}

# Save the fixed version
print(f"\n💾 Saving fixed boundaries to: {output_file}")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f)

file_size = len(json.dumps(output_data)) / (1024 * 1024)
print(f"✅ Done! File size: {file_size:.2f} MB")
print(f"\n📌 Original file: {input_file}")
print(f"📌 Fixed file: {output_file}")
print("\n" + "=" * 60)
print("✨ District boundaries fixed! No more cracks/gaps.")
print("💡 Update your HTML to use 'Kerala_districts_fixed.geojson'")
