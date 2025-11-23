#!/usr/bin/env python3
"""
Consolidate 30 org districts into 14 actual Kerala government districts
"""

import json
import os
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# Map 14 actual districts to their org districts
DISTRICT_CONSOLIDATION = {
    'thiruvananthapuram': ['Thiruvananthapuram South', 'Thiruvananthapuram North', 'Thiruvananthapuram City'],
    'kollam': ['Kollam West', 'Kollam East'],
    'pathanamthitta': ['Pathanamthitta'],
    'alappuzha': ['Alappuzha North', 'Alappuzha South'],
    'kottayam': ['Kottayam East', 'Kottayam West'],
    'idukki': ['Idukki North', 'Idukki South'],
    'ernakulam': ['Ernakulam City', 'Ernakulam East', 'Ernakulam North'],
    'thrissur': ['Thrissur North', 'Thrissur South', 'Thrissur City'],
    'palakkad': ['Palakkad West', 'Palakkad East'],
    'malappuram': ['Malappuram Central', 'Malappuram East', 'Malappuram West'],
    'kozhikode': ['Kozhikode City', 'Kozhikode North', 'Kozhikode Rural'],
    'wayanad': ['Wayanad'],
    'kannur': ['Kannur North', 'Kannur South'],
    'kasaragod': ['Kasaragod']
}

def consolidate():
    print("🔄 Consolidating 30 org districts into 14 actual districts...")
    print("=" * 70)
    
    input_dir = 'data/complete_hierarchy'
    output_dir = 'data/14_districts'
    os.makedirs(output_dir, exist_ok=True)
    
    for actual_district, org_districts in DISTRICT_CONSOLIDATION.items():
        print(f"\n📍 Processing: {actual_district.upper()}")
        print(f"   Consolidating: {', '.join(org_districts)}")
        
        consolidated = {
            'name': actual_district,
            'acs': []
        }
        
        all_geometries = []
        
        for org_district in org_districts:
            # Create clean filename
            clean_name = org_district.lower().replace(' ', '').replace('-', '')
            filepath = os.path.join(input_dir, f'{clean_name}.json')
            
            if not os.path.exists(filepath):
                print(f"   ⚠️  Warning: {filepath} not found")
                continue
            
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Add all ACs from this org district
            consolidated['acs'].extend(data.get('acs', []))
            
            # Collect all geometries for district boundary
            for ac in data.get('acs', []):
                if 'geometry' in ac:
                    geom = shape(ac['geometry'])
                    all_geometries.append(geom)
        
        # Create consolidated district boundary
        if all_geometries:
            try:
                district_boundary = unary_union(all_geometries)
                consolidated['geometry'] = mapping(district_boundary)
                print(f"   ✅ Created boundary with {len(all_geometries)} AC geometries")
            except Exception as e:
                print(f"   ❌ Error creating boundary: {e}")
        
        # Save consolidated district
        output_file = os.path.join(output_dir, f'{actual_district}.json')
        with open(output_file, 'w') as f:
            json.dump(consolidated, f, indent=2)
        
        print(f"   ✅ Saved: {output_file}")
        print(f"   📊 Total ACs: {len(consolidated['acs'])}")
    
    print("\n" + "=" * 70)
    print("✅ Consolidation complete!")
    print("=" * 70)

if __name__ == '__main__':
    consolidate()
