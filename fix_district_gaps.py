#!/usr/bin/env python3
"""
Fix gaps between district boundaries by applying a small buffer operation
"""

import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

def main():
    print("="*80)
    print("🔧 FIXING GAPS BETWEEN DISTRICT BOUNDARIES")
    print("="*80)
    
    # Load the existing GeoJSON
    input_path = 'data/kerala_14_districts.geojson'
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📂 Loaded {len(data['features'])} districts")
    
    # Process each district
    fixed_features = []
    
    for feature in data['features']:
        district_name = feature['properties']['name']
        print(f"\n🔧 Processing {district_name}...")
        
        try:
            # Get the geometry
            geom = shape(feature['geometry'])
            
            # Apply a buffer to close gaps (0.005 degrees ≈ 555 meters)
            # This creates overlaps that eliminate visible cracks
            buffered = geom.buffer(0.005).buffer(-0.005)
            
            # Simplify very slightly to reduce point density (0.0001 degrees ≈ 11 meters)
            # This removes unnecessary detail that can cause rendering issues
            simplified = buffered.simplify(0.0001, preserve_topology=True)
            
            # Create new feature with fixed geometry
            new_feature = {
                'type': 'Feature',
                'properties': feature['properties'],
                'geometry': mapping(simplified)
            }
            
            fixed_features.append(new_feature)
            
            print(f"   ✅ Fixed - Geometry type: {simplified.geom_type}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            # Use original if fixing fails
            fixed_features.append(feature)
    
    # Create fixed GeoJSON
    fixed_geojson = {
        'type': 'FeatureCollection',
        'features': fixed_features
    }
    
    # Verify the result
    print("\n" + "="*80)
    print("🔍 VERIFYING FIXED BOUNDARIES")
    print("="*80)
    
    geometries = [shape(f['geometry']) for f in fixed_features]
    full_kerala = unary_union(geometries)
    
    print(f"\nUnion result: {full_kerala.geom_type}")
    if full_kerala.geom_type == 'MultiPolygon':
        print(f"⚠️  Still {len(list(full_kerala.geoms))} parts (may include islands)")
    else:
        print("✅ Single continuous polygon!")
    
    # Save the fixed GeoJSON
    output_path = 'data/kerala_14_districts_fixed.geojson'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fixed_geojson, f, indent=2)
    
    print("\n" + "="*80)
    print(f"✅ Fixed GeoJSON saved to: {output_path}")
    print("="*80)
    print("\nTo use the fixed version:")
    print("1. Backup original: mv data/kerala_14_districts.geojson data/kerala_14_districts_original.geojson")
    print("2. Use fixed version: mv data/kerala_14_districts_fixed.geojson data/kerala_14_districts.geojson")
    print("3. Refresh your browser")
    print("="*80)

if __name__ == '__main__':
    main()
