#!/usr/bin/env python3
"""
Fix missing ward geometries by checking original ward_jsons files
"""

import json
import os

missing_wards = [
    ('kollam', 'Chadayamangalam', 'Chadayamangalam', 'Elamadu', 10, 'KANNAMKODU', 
     '/Users/devandev/Desktop/ward_jsons/Kollam/Grama Panchayat/Elamadu.json'),
    
    ('kollam', 'Chadayamangalam', 'Chadayamangalam', 'Nilamel', 1, 'ELIKKUNNAMUKAL',
     '/Users/devandev/Desktop/ward_jsons/Kollam/Grama Panchayat/Nilamel.json'),
    
    ('kollam', 'Kottarakkara', 'Neduvathur', 'Kulakkada', 8, 'PAINUMOODU',
     '/Users/devandev/Desktop/ward_jsons/Kollam/Grama Panchayat/Kulakkada.json'),
    
    ('kozhikode', 'Nadapuram', 'Nadapuram', 'Chekkiad', 9, 'JATHIYERI',
     '/Users/devandev/Desktop/ward_jsons/Kozhikode/Grama Panchayat/Chekkiad.json'),
    
    ('kozhikode', 'Nadapuram', 'Nadapuram', 'Nadapuram', 20, 'KUMMANKODE SOUTH',
     '/Users/devandev/Desktop/ward_jsons/Kozhikode/Grama Panchayat/Nadapuram.json'),
    
    ('kozhikode', 'Nadapuram', 'Nadapuram', 'Nadapuram', 21, 'KAKKAMVELLI',
     '/Users/devandev/Desktop/ward_jsons/Kozhikode/Grama Panchayat/Nadapuram.json'),
    
    ('ernakulam', 'Perumbavoor', 'Kuruppampady', 'Vengoor', 6, 'kannamparambu ponginchuvadu',
     '/Users/devandev/Desktop/ward_jsons/Ernakulam/Grama Panchayat/Vengoor.json'),
    
    ('thiruvananthapuram', 'Kattakkada', 'Malayinkeezhu', 'Vilavoorkal', 12, 'POTTAYIL',
     '/Users/devandev/Desktop/ward_jsons/Thiruvanathapuram/Grama Panchayat/Vilavoorkal.json'),
    
    ('thiruvananthapuram', 'Attingal (SC)', 'Kilimanoor', 'Kilimanoor', 3, 'VILANGARA',
     '/Users/devandev/Desktop/ward_jsons/Thiruvanathapuram/Grama Panchayat/Kilimanoor.json'),
    
    ('thiruvananthapuram', 'Attingal (SC)', 'Kilimanoor', 'Kilimanoor', 12, 'KAYATTUKONAM',
     '/Users/devandev/Desktop/ward_jsons/Thiruvanathapuram/Grama Panchayat/Kilimanoor.json'),
]

print('='*80)
print('🔧 FIXING MISSING WARD GEOMETRIES')
print('='*80)

for district, ac_name, mandal_name, lb_name, ward_no, ward_name, ward_json_path in missing_wards:
    print(f'\n📍 Processing: {ward_name} (Ward #{ward_no})')
    print(f'   LB: {lb_name} ({district})')
    
    # Load the ward JSON file
    try:
        with open(ward_json_path) as f:
            ward_data = json.load(f)
        
        if 'features' not in ward_data:
            print(f'   ❌ No features in {ward_json_path}')
            continue
        
        # Try to find the ward by ward number or name
        found_geom = None
        for feature in ward_data['features']:
            props = feature.get('properties', {})
            feature_ward_no = props.get('ward_number') or props.get('ward_no') or props.get('WARD_NO')
            feature_ward_name = props.get('ward_name') or props.get('name') or props.get('WARD_NAME', '')
            
            # Match by ward number or name
            if (feature_ward_no == ward_no or 
                str(feature_ward_no) == str(ward_no) or
                ward_name.lower() in str(feature_ward_name).lower() or
                str(feature_ward_name).lower() in ward_name.lower()):
                
                if 'geometry' in feature and feature['geometry']:
                    found_geom = feature['geometry']
                    print(f'   ✅ Found geometry for ward #{feature_ward_no}: {feature_ward_name}')
                    break
        
        if not found_geom:
            print(f'   ❌ Could not find geometry in ward JSON')
            continue
        
        # Load district JSON and update the ward
        district_file = f'data/14_districts/{district}.json'
        with open(district_file) as f:
            district_data = json.load(f)
        
        updated = False
        for ac in district_data.get('acs', []):
            if ac_name.lower() in ac['name'].lower():
                for mandal in ac.get('mandals', []):
                    if mandal_name.lower() in mandal['name'].lower():
                        for lb in mandal.get('local_bodies', []):
                            if lb_name.lower() in lb['name'].lower():
                                for idx, ward in enumerate(lb.get('wards', [])):
                                    w_no = ward.get('ward_number') or ward.get('ward_no') or (idx + 1)
                                    w_name = ward.get('ward_name') or ward.get('name', '')
                                    
                                    if (w_no == ward_no or
                                        ward_name.lower() in w_name.lower() or
                                        w_name.lower() in ward_name.lower()):
                                        
                                        ward['geometry'] = found_geom
                                        updated = True
                                        print(f'   ✅ Updated ward geometry in district JSON')
                                        break
                                if updated:
                                    break
                        if updated:
                            break
                if updated:
                    break
        
        if updated:
            # Save the updated district JSON
            with open(district_file, 'w') as f:
                json.dump(district_data, f, indent=2)
            print(f'   ✅ Saved {district_file}')
        else:
            print(f'   ❌ Could not find ward in district JSON')
    
    except Exception as e:
        print(f'   ❌ Error: {e}')

print('\n' + '='*80)
print('✅ COMPLETED! Missing ward geometries have been fixed.')
print('='*80)
