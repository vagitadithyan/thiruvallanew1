#!/usr/bin/env python3
"""
Fix missing Local Body geometries by extracting from original ward_jsons
"""

import json
import os
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# Missing LB mappings: (district_json, ac_name, mandal_name, lb_name, ward_json_path)
missing_lbs = [
    ('ernakulam', 'Perumbavoor', 'Kuruppampady', 'Vengoor', 
     '/Users/devandev/Desktop/ward_jsons/Ernakulam/Grama Panchayat/Vengoor.json'),
    
    ('kollam', 'Chadayamangalam', 'Chadayamangalam', 'Elamadu',
     '/Users/devandev/Desktop/ward_jsons/Kollam/Grama Panchayat/Elamadu.json'),
    
    ('kollam', 'Chadayamangalam', 'Chadayamangalam', 'Nilamel',
     '/Users/devandev/Desktop/ward_jsons/Kollam/Grama Panchayat/Nilamel.json'),
    
    ('kollam', 'Kottarakkara', 'Neduvathur', 'Kulakkada',
     '/Users/devandev/Desktop/ward_jsons/Kollam/Grama Panchayat/Kulakkada.json'),
    
    ('kozhikode', 'Nadapuram', 'Nadapuram', 'Chekkiad',
     '/Users/devandev/Desktop/ward_jsons/Kozhikode/Grama Panchayat/Chekkiad.json'),
    
    ('kozhikode', 'Nadapuram', 'Nadapuram', 'Nadapuram',
     '/Users/devandev/Desktop/ward_jsons/Kozhikode/Grama Panchayat/Nadapuram.json'),
    
    ('thiruvananthapuram', 'Kattakkada', 'Malayinkeezhu', 'Vilavoorkal',
     '/Users/devandev/Desktop/ward_jsons/Thiruvanathapuram/Grama Panchayat/Vilavoorkal.json'),
    
    ('thiruvananthapuram', 'Attingal (SC)', 'Kilimanoor', 'Kilimanoor',
     '/Users/devandev/Desktop/ward_jsons/Thiruvanathapuram/Grama Panchayat/Kilimanoor.json'),
]

print('='*80)
print('🔧 FIXING MISSING LOCAL BODY GEOMETRIES')
print('='*80)

for district, ac_name, mandal_name, lb_name, ward_json_path in missing_lbs:
    print(f'\n📍 Processing: {lb_name} ({district})')
    print(f'   Path: {ac_name} > {mandal_name} > {lb_name}')
    
    # Load ward geometries
    try:
        with open(ward_json_path) as f:
            ward_data = json.load(f)
        
        if 'features' not in ward_data or len(ward_data['features']) == 0:
            print(f'   ❌ No features found in {ward_json_path}')
            continue
        
        print(f'   ✅ Loaded {len(ward_data["features"])} ward features')
        
        # Extract all ward geometries and union them
        geometries = []
        for feature in ward_data['features']:
            if 'geometry' in feature and feature['geometry']:
                try:
                    geom = shape(feature['geometry'])
                    if geom.is_valid:
                        geometries.append(geom)
                except Exception as e:
                    print(f'   ⚠️  Invalid geometry in ward: {e}')
        
        if not geometries:
            print(f'   ❌ No valid geometries found')
            continue
        
        print(f'   ✅ Found {len(geometries)} valid ward geometries')
        
        # Union all ward geometries to create LB boundary
        lb_geometry = unary_union(geometries)
        lb_geojson = mapping(lb_geometry)
        
        print(f'   ✅ Created LB geometry: {lb_geojson["type"]}')
        
        # Load district JSON
        district_file = f'data/14_districts/{district}.json'
        with open(district_file) as f:
            district_data = json.load(f)
        
        # Find and update the LB
        updated = False
        for ac in district_data.get('acs', []):
            if ac_name.lower() in ac['name'].lower():
                for mandal in ac.get('mandals', []):
                    if mandal_name.lower() in mandal['name'].lower():
                        for lb in mandal.get('local_bodies', []):
                            if lb_name.lower() in lb['name'].lower():
                                lb['geometry'] = lb_geojson
                                updated = True
                                print(f'   ✅ Updated LB geometry in JSON')
                                break
                        if updated:
                            break
                if updated:
                    break
        
        if not updated:
            print(f'   ❌ Could not find LB in district JSON')
            continue
        
        # Save updated district JSON
        with open(district_file, 'w') as f:
            json.dump(district_data, f, indent=2)
        
        print(f'   ✅ Saved {district_file}')
        
    except Exception as e:
        print(f'   ❌ Error: {e}')

print('\n' + '='*80)
print('✅ COMPLETED! All missing LB geometries have been added.')
print('='*80)
