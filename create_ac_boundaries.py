#!/usr/bin/env python3
"""
Generate AC-level boundaries by merging ward GeoJSON files
"""

import json
import csv
import os
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from collections import defaultdict

# Base path for ward JSON files
WARD_JSONS_PATH = '/Users/devandev/Desktop/ward_jsons'
CSV_FILE = f'{WARD_JSONS_PATH}/LSG Mapped - Sheet1.csv'

def clean_name(name):
    """Clean name for file/ID usage"""
    return name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')

def main():
    print("🔄 Generating AC boundaries from ward data...")
    
    # Read CSV to map local bodies to ACs
    ac_to_lbs = defaultdict(lambda: defaultdict(set))
    ac_names = {}
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            org_district = row['Org District'].strip()
            ac = row['AC'].strip()
            lb_name = row['LBName'].strip()
            lb_type = row['LBType'].strip()
            
            # Map type
            type_folder = 'Municipality' if lb_type == 'M' else ('Corporation' if lb_type == 'C' else 'Grama Panchayat')
            
            ac_id = clean_name(ac)
            ac_names[ac_id] = ac
            lb_file = clean_name(lb_name)
            
            ac_to_lbs[ac_id][(org_district, type_folder)].add(lb_file)
    
    print(f"📊 Found {len(ac_names)} unique ACs")
    
    # Process each AC
    ac_geometries = {}
    
    for ac_id, lb_data in sorted(ac_to_lbs.items()):
        ac_name = ac_names[ac_id]
        print(f"\n🔧 Processing AC: {ac_name}")
        
        geometries = []
        processed_count = 0
        
        for (org_district, type_folder), lb_files in lb_data.items():
            for lb_file in lb_files:
                # Construct path
                ward_path = f"{WARD_JSONS_PATH}/{org_district}/{type_folder}/{lb_file}.json"
                
                try:
                    if os.path.exists(ward_path):
                        with open(ward_path, 'r', encoding='utf-8') as f:
                            geojson = json.load(f)
                            
                            if 'features' in geojson:
                                for feature in geojson['features']:
                                    geom = shape(feature['geometry'])
                                    if geom.is_valid:
                                        geometries.append(geom)
                            elif 'geometry' in geojson:
                                geom = shape(geojson['geometry'])
                                if geom.is_valid:
                                    geometries.append(geom)
                        
                        processed_count += 1
                        print(f"   ✅ {lb_file}")
                except Exception as e:
                    print(f"   ❌ Error with {lb_file}: {e}")
        
        if geometries:
            print(f"   📊 Merging {len(geometries)} geometries...")
            try:
                merged = unary_union(geometries)
                ac_geometries[ac_id] = {
                    'name': ac_name,
                    'geometry': merged
                }
                print(f"   ✅ Created boundary for {ac_name}")
            except Exception as e:
                print(f"   ❌ Error merging {ac_name}: {e}")
        else:
            print(f"   ⚠️  No geometries found for {ac_name}")
    
    # Create GeoJSON
    print(f"\n🔧 Creating AC boundaries GeoJSON...")
    
    features = []
    for ac_id, data in sorted(ac_geometries.items()):
        feature = {
            'type': 'Feature',
            'properties': {
                'ac_id': ac_id,
                'ac_name': data['name']
            },
            'geometry': mapping(data['geometry'])
        }
        features.append(feature)
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    # Save
    output_path = 'data/kerala_ac_boundaries.geojson'
    os.makedirs('data', exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"\n✅ Created AC boundaries: {output_path}")
    print(f"📊 Total ACs: {len(features)}")
    
    print("\n" + "="*70)
    print("🎉 AC boundaries generated successfully!")
    print("="*70)

if __name__ == '__main__':
    main()
