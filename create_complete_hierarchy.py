#!/usr/bin/env python3
"""
Generate COMPLETE hierarchy boundaries with fuzzy matching
Districts → ACs → Mandals → Local Bodies (with ward geometry)
"""

import json
import csv
import os
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from collections import defaultdict
from difflib import SequenceMatcher
import re

WARD_JSONS_PATH = '/Users/devandev/Desktop/ward_jsons'
CSV_FILE = f'{WARD_JSONS_PATH}/LSG Mapped - Sheet1.csv'

# Map org districts (from CSV) to actual folder names
ORG_TO_FOLDER = {
    'Thiruvananthapuram South': 'Thiruvanathapuram',
    'Thiruvananthapuram North': 'Thiruvanathapuram',
    'Thiruvananthapuram City': 'Thiruvanathapuram',
    'Kollam West': 'Kollam',
    'Kollam East': 'Kollam',
    'Pathanamthitta': 'Pathanamthitta',
    'Alappuzha North': 'Alappuzha',
    'Alappuzha South': 'Alappuzha',
    'Kottayam East': 'Kottayam',
    'Kottayam West': 'Kottayam',
    'Idukki North': 'Idukki',
    'Idukki South': 'Idukki',
    'Ernakulam City': 'Ernakulam',
    'Ernakulam East': 'Ernakulam',
    'Ernakulam North': 'Ernakulam',
    'Thrissur North': 'Thrissur',
    'Thrissur South': 'Thrissur',
    'Thrissur City': 'Thrissur',
    'Palakkad West': 'Palakkad',
    'Palakkad East': 'Palakkad',
    'Malappuram Central': 'Malappuram',
    'Malappuram East': 'Malappuram',
    'Malappuram West': 'Malappuram',
    'Kozhikode City': 'Kozhikode',
    'Kozhikode North': 'Kozhikode',
    'Kozhikode Rural': 'Kozhikode',
    'Wayanad': 'Wayanad',
    'Kannur North': 'Kannur',
    'Kannur South': 'Kannur',
    'Kasaragod': 'Kasaragod'
}

def clean_name(name):
    """Clean name for comparison"""
    return re.sub(r'[^a-z0-9]', '', name.lower())

def fuzzy_match(name1, name2, threshold=0.7):
    """Check if two names are similar enough"""
    clean1 = clean_name(name1)
    clean2 = clean_name(name2)
    ratio = SequenceMatcher(None, clean1, clean2).ratio()
    return ratio >= threshold

def find_json_file(directory, lb_name, lb_type):
    """Find JSON file with fuzzy matching"""
    if not os.path.exists(directory):
        return None
    
    type_folder = 'Municipality' if lb_type == 'M' else ('Corporation' if lb_type == 'C' else 'Grama Panchayat')
    search_dir = os.path.join(directory, type_folder)
    
    if not os.path.exists(search_dir):
        return None
    
    # Try exact match first
    clean_lb = clean_name(lb_name)
    
    for filename in os.listdir(search_dir):
        if filename.endswith('.json'):
            clean_file = clean_name(filename.replace('.json', ''))
            
            # Exact match
            if clean_lb == clean_file:
                return os.path.join(search_dir, filename)
            
            # Fuzzy match
            if fuzzy_match(lb_name, filename.replace('.json', ''), 0.8):
                return os.path.join(search_dir, filename)
    
    return None

def main():
    print("🔄 Generating COMPLETE hierarchy with fuzzy matching...")
    print("=" * 70)
    
    # Read CSV and build hierarchy
    hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    
    print("\n📂 Reading CSV data...")
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            org_district = row['Org District'].strip()
            ac = row['AC'].strip()
            mandal = row['Org Mandal'].strip()
            lb_name = row['LBName'].strip()
            lb_type = row['LBType'].strip()
            lb_code = row['LBCode'].strip()
            
            hierarchy[org_district][ac][mandal][lb_name] = {
                'type': lb_type,
                'code': lb_code,
                'org_district': org_district
            }
    
    print(f"✅ Found {len(hierarchy)} org districts")
    
    # Create output structure
    os.makedirs('data/complete_hierarchy', exist_ok=True)
    
    district_stats = {}
    total_matched = 0
    total_missed = 0
    
    # Process each level
    for org_district, acs in sorted(hierarchy.items()):
        print(f"\n{'='*70}")
        print(f"📍 DISTRICT: {org_district}")
        print(f"{'='*70}")
        
        # Map org district to actual folder name
        folder_district = ORG_TO_FOLDER.get(org_district, org_district)
        district_dir = os.path.join(WARD_JSONS_PATH, folder_district)
        district_features = []
        district_info = {
            'name': org_district,
            'acs': []
        }
        
        for ac, mandals in sorted(acs.items()):
            print(f"\n  📌 AC: {ac}")
            ac_features = []
            ac_info = {
                'name': ac,
                'mandals': []
            }
            
            for mandal, lbs in sorted(mandals.items()):
                print(f"    🔹 Mandal: {mandal}")
                mandal_features = []
                mandal_info = {
                    'name': mandal,
                    'local_bodies': []
                }
                
                for lb_name, lb_data in sorted(lbs.items()):
                    # Find JSON file with fuzzy matching
                    json_path = find_json_file(district_dir, lb_name, lb_data['type'])
                    
                    if json_path:
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                geojson = json.load(f)
                                
                                if 'features' in geojson:
                                    features = geojson['features']
                                elif 'geometry' in geojson:
                                    features = [geojson]
                                else:
                                    features = []
                                
                                if features:
                                    # Store LB info with wards (including individual ward geometries)
                                    wards_data = []
                                    for idx, feature in enumerate(features):
                                        props = feature.get('properties', {})
                                        
                                        # Get ward number
                                        ward_no = props.get('Ward_No') or \
                                                 props.get('ward_no') or \
                                                 props.get('WARD_NO') or \
                                                 (idx + 1)
                                        
                                        # Get ward name
                                        ward_name = props.get('Ward_Name') or \
                                                   props.get('ward_name') or \
                                                   props.get('WARD_NAME') or \
                                                   props.get('name') or \
                                                   f'Ward {ward_no}'
                                        
                                        ward_info = {
                                            'ward_number': str(ward_no),
                                            'ward_name': ward_name,
                                            'geometry': feature['geometry']  # Store ward geometry
                                        }
                                        wards_data.append(ward_info)
                                    
                                    lb_info = {
                                        'name': lb_name,
                                        'code': lb_data['code'],
                                        'type': lb_data['type'],  # Keep original M/C/G format
                                        'wards': wards_data  # Include ward geometries
                                    }
                                    
                                    mandal_info['local_bodies'].append(lb_info)
                                    
                                    # Collect geometries for boundary creation
                                    for feature in features:
                                        geom = shape(feature['geometry'])
                                        if geom.is_valid:
                                            mandal_features.append(geom)
                                            ac_features.append(geom)
                                            district_features.append(geom)
                                    
                                    # Create LB boundary geometry
                                    try:
                                        lb_geoms = [shape(w['geometry']) for w in wards_data if shape(w['geometry']).is_valid]
                                        if lb_geoms:
                                            lb_info['geometry'] = mapping(unary_union(lb_geoms))
                                    except:
                                        pass
                                    
                                    total_matched += 1
                                    print(f"      ✅ {lb_name} ({len(features)} wards)")
                                else:
                                    total_missed += 1
                                    print(f"      ⚠️  {lb_name} (no features)")
                        except Exception as e:
                            total_missed += 1
                            print(f"      ❌ {lb_name}: {str(e)[:50]}")
                    else:
                        total_missed += 1
                        print(f"      ❌ {lb_name} (file not found)")
                
                # Save Mandal boundary if we have geometries
                if mandal_features:
                    try:
                        mandal_geom = unary_union(mandal_features)
                        mandal_id = clean_name(mandal)
                        
                        mandal_geojson = {
                            'type': 'Feature',
                            'properties': {
                                'mandal_id': mandal_id,
                                'mandal_name': mandal,
                                'ac_name': ac,
                                'district_name': org_district,
                                'local_bodies': len(mandal_info['local_bodies'])
                            },
                            'geometry': mapping(mandal_geom)
                        }
                        
                        mandal_info['geometry'] = mandal_geojson
                        ac_info['mandals'].append(mandal_info)
                        print(f"    ✅ Mandal boundary created ({len(mandal_features)} geometries)")
                    except Exception as e:
                        print(f"    ❌ Error creating mandal boundary: {e}")
            
            # Save AC boundary if we have geometries
            if ac_features:
                try:
                    ac_geom = unary_union(ac_features)
                    ac_id = clean_name(ac)
                    
                    ac_geojson = {
                        'type': 'Feature',
                        'properties': {
                            'ac_id': ac_id,
                            'ac_name': ac,
                            'district_name': org_district,
                            'mandals': len(ac_info['mandals'])
                        },
                        'geometry': mapping(ac_geom)
                    }
                    
                    ac_info['geometry'] = ac_geojson
                    district_info['acs'].append(ac_info)
                    print(f"  ✅ AC boundary created ({len(ac_features)} geometries)")
                except Exception as e:
                    print(f"  ❌ Error creating AC boundary: {e}")
        
        # Save District boundary
        if district_features:
            try:
                district_geom = unary_union(district_features)
                district_id = clean_name(org_district)
                
                district_geojson = {
                    'type': 'Feature',
                    'properties': {
                        'district_id': district_id,
                        'district_name': org_district,
                        'acs': len(district_info['acs'])
                    },
                    'geometry': mapping(district_geom)
                }
                
                district_info['geometry'] = district_geojson
                
                # Save complete district data
                output_file = f'data/complete_hierarchy/{district_id}.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(district_info, f, indent=2)
                
                district_stats[org_district] = len(district_features)
                print(f"✅ District saved: {output_file} ({len(district_features)} geometries)")
            except Exception as e:
                print(f"❌ Error creating district boundary: {e}")
    
    # Create summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    print(f"Total Local Bodies Matched: {total_matched}")
    print(f"Total Local Bodies Missed: {total_missed}")
    print(f"Success Rate: {(total_matched/(total_matched+total_missed)*100):.1f}%")
    print(f"\nDistricts processed: {len(district_stats)}")
    for district, count in sorted(district_stats.items()):
        print(f"  • {district}: {count} ward geometries")
    
    print(f"\n✅ Complete hierarchy saved to: data/complete_hierarchy/")
    print("="*70)

if __name__ == '__main__':
    main()
