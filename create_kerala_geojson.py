#!/usr/bin/env python3
"""
Create a proper GeoJSON file for all 14 Kerala districts
Each district should be a single unified geometry
"""

import json
import os
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

def create_kerala_geojson():
    print("🗺️  Creating Kerala 14 Districts GeoJSON...")
    print("=" * 70)
    
    districts_dir = 'data/14_districts'
    output_file = 'data/kerala_14_districts.geojson'
    
    features = []
    
    # Process each district
    district_files = sorted([f for f in os.listdir(districts_dir) if f.endswith('.json')])
    
    for district_file in district_files:
        district_name = district_file.replace('.json', '')
        filepath = os.path.join(districts_dir, district_file)
        
        print(f"\n📍 Processing: {district_name.upper()}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Collect all ward geometries to create proper district boundary
        all_ward_geometries = []
        ac_count = 0
        ward_count = 0
        
        for ac in data.get('acs', []):
            ac_count += 1
            for mandal in ac.get('mandals', []):
                for lb in mandal.get('local_bodies', []):
                    for ward in lb.get('wards', []):
                        if 'geometry' in ward:
                            try:
                                geom = shape(ward['geometry'])
                                if geom.is_valid:
                                    all_ward_geometries.append(geom)
                                    ward_count += 1
                            except Exception as e:
                                print(f"   ⚠️  Error processing ward geometry: {e}")
        
        print(f"   ACs: {ac_count}, Wards: {ward_count}")
        
        # Create unified district boundary from all wards
        if all_ward_geometries:
            try:
                print(f"   🔄 Merging {len(all_ward_geometries)} ward geometries...")
                district_boundary = unary_union(all_ward_geometries)
                
                # Create feature
                feature = {
                    'type': 'Feature',
                    'properties': {
                        'district': district_name,
                        'name': district_name.title(),
                        'acs': ac_count,
                        'wards': ward_count
                    },
                    'geometry': mapping(district_boundary)
                }
                
                features.append(feature)
                geom_type = feature['geometry']['type']
                print(f"   ✅ Created {geom_type} boundary")
                
            except Exception as e:
                print(f"   ❌ Error creating boundary: {e}")
        else:
            print(f"   ⚠️  No ward geometries found!")
    
    # Create GeoJSON FeatureCollection
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print("\n" + "=" * 70)
    print(f"✅ Created: {output_file}")
    print(f"📊 Total districts: {len(features)}")
    print("=" * 70)

if __name__ == '__main__':
    create_kerala_geojson()
