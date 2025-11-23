#!/usr/bin/env python3
"""
Consolidate 30 organizational districts into 14 actual Kerala government districts
"""

import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import os

# Mapping from 30 org districts to 14 actual districts
ORG_TO_ACTUAL = {
    'thiruvananthapuram_south': 'thiruvananthapuram',
    'thiruvananthapuram_north': 'thiruvananthapuram',
    'thiruvananthapuram_city': 'thiruvananthapuram',
    'kollam_west': 'kollam',
    'kollam_east': 'kollam',
    'pathanamthitta': 'pathanamthitta',
    'alappuzha_north': 'alappuzha',
    'alappuzha_south': 'alappuzha',
    'kottayam_east': 'kottayam',
    'kottayam_west': 'kottayam',
    'idukki_north': 'idukki',
    'idukki_south': 'idukki',
    'ernakulam_city': 'ernakulam',
    'ernakulam_east': 'ernakulam',
    'ernakulam_north': 'ernakulam',
    'thrissur_north': 'thrissur',
    'thrissur_south': 'thrissur',
    'thrissur_city': 'thrissur',
    'palakkad_west': 'palakkad',
    'palakkad_east': 'palakkad',
    'malappuram_central': 'malappuram',
    'malappuram_east': 'malappuram',
    'malappuram_west': 'malappuram',
    'kozhikode_city': 'kozhikode',
    'kozhikode_north': 'kozhikode',
    'kozhikode_rural': 'kozhikode',
    'wayanad': 'wayanad',
    'kannur_north': 'kannur',
    'kannur_south': 'kannur',
    'kasaragod': 'kasaragod'
}

# Colors for 14 districts
DISTRICT_COLORS = {
    'thiruvananthapuram': '#FF6B6B',
    'kollam': '#4ECDC4',
    'pathanamthitta': '#45B7D1',
    'alappuzha': '#96CEB4',
    'kottayam': '#FFEAA7',
    'idukki': '#DFE6E9',
    'ernakulam': '#A29BFE',
    'thrissur': '#FD79A8',
    'palakkad': '#FDCB6E',
    'malappuram': '#6C5CE7',
    'kozhikode': '#00B894',
    'wayanad': '#E17055',
    'kannur': '#74B9FF',
    'kasaragod': '#81ECEC'
}

# District proper names
DISTRICT_NAMES = {
    'thiruvananthapuram': 'Thiruvananthapuram',
    'kollam': 'Kollam',
    'pathanamthitta': 'Pathanamthitta',
    'alappuzha': 'Alappuzha',
    'kottayam': 'Kottayam',
    'idukki': 'Idukki',
    'ernakulam': 'Ernakulam',
    'thrissur': 'Thrissur',
    'palakkad': 'Palakkad',
    'malappuram': 'Malappuram',
    'kozhikode': 'Kozhikode',
    'wayanad': 'Wayanad',
    'kannur': 'Kannur',
    'kasaragod': 'Kasaragod'
}

def main():
    print("🔄 Consolidating 30 organizational districts into 14 actual Kerala districts...")
    
    # Load the existing 30-district GeoJSON
    geojson_path = 'data/kerala_districts.geojson'
    
    if not os.path.exists(geojson_path):
        print(f"❌ Error: {geojson_path} not found!")
        return
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📂 Loaded {len(data['features'])} organizational district features")
    
    # Group features by actual district
    district_groups = {}
    
    for feature in data['features']:
        org_district_id = feature['properties'].get('district_id', '')
        
        # Map to actual district
        actual_district_id = ORG_TO_ACTUAL.get(org_district_id)
        
        if actual_district_id:
            if actual_district_id not in district_groups:
                district_groups[actual_district_id] = []
            district_groups[actual_district_id].append(feature)
        else:
            print(f"⚠️  No mapping for org district: {org_district_id}")
    
    print(f"\n📊 Found {len(district_groups)} actual districts")
    
    # Create new GeoJSON with 14 districts
    new_features = []
    
    for district_id, features in sorted(district_groups.items()):
        print(f"\n🔧 Merging {len(features)} sub-districts for {DISTRICT_NAMES[district_id]}...")
        
        try:
            # Extract geometries
            geometries = []
            for feature in features:
                geom = shape(feature['geometry'])
                if geom.is_valid:
                    geometries.append(geom)
            
            if not geometries:
                print(f"   ⚠️  No valid geometries for {district_id}")
                continue
            
            # Merge all geometries into one
            merged_geometry = unary_union(geometries)
            
            # Create feature
            new_feature = {
                'type': 'Feature',
                'properties': {
                    'district_id': district_id,
                    'name': DISTRICT_NAMES[district_id],
                    'color': DISTRICT_COLORS[district_id]
                },
                'geometry': mapping(merged_geometry)
            }
            
            new_features.append(new_feature)
            print(f"   ✅ Created boundary for {DISTRICT_NAMES[district_id]}")
            
        except Exception as e:
            print(f"   ❌ Error merging {district_id}: {e}")
    
    # Create final GeoJSON
    final_geojson = {
        'type': 'FeatureCollection',
        'features': new_features
    }
    
    # Save consolidated GeoJSON
    output_path = 'data/kerala_14_districts.geojson'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_geojson, f, indent=2)
    
    print(f"\n✅ Created 14-district GeoJSON: {output_path}")
    print(f"📊 Total districts: {len(new_features)}")
    
    # Also create individual district files
    print("\n🔧 Creating individual 14-district boundary files...")
    
    for feature in new_features:
        district_id = feature['properties']['district_id']
        district_name = feature['properties']['name']
        
        # Create directory
        district_dir = f'data/{district_id}'
        os.makedirs(district_dir, exist_ok=True)
        
        # Save individual file
        individual_geojson = {
            'type': 'FeatureCollection',
            'features': [feature]
        }
        
        individual_path = f'{district_dir}/district_boundary.geojson'
        with open(individual_path, 'w', encoding='utf-8') as f:
            json.dump(individual_geojson, f, indent=2)
        
        print(f"✅ {district_name} → {individual_path}")
    
    print("\n" + "="*70)
    print("🎉 14-district consolidation complete!")
    print("="*70)
    print(f"Main file: {output_path}")
    print(f"Individual files: data/[district_id]/district_boundary.geojson")
    print("="*70)

if __name__ == '__main__':
    main()
