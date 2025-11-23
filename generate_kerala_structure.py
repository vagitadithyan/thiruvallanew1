import csv
import json
import re
import os

csv_path = "/Users/devandev/Desktop/ward_jsons/LSG Mapped - Sheet1.csv"

def clean_id(text):
    """Remove all spaces and special characters, convert to lowercase"""
    cleaned = re.sub(r'[^\w\s-]', '', text)
    cleaned = re.sub(r'[-\s]+', '_', cleaned)
    return cleaned.lower().strip('_')

# District colors (14+ unique colors for all org districts)
DISTRICT_COLORS = {
    'kollam_west': '#FF6B6B',
    'kollam_east': '#4ECDC4',
    'pathanamthitta': '#45B7D1',
    'thiruvananthapuram_south': '#96CEB4',
    'thiruvananthapuram_north': '#FFEAA7',
    'thiruvananthapuram_city': '#DFE6E9',
    'alappuzha_north': '#A29BFE',
    'alappuzha_south': '#FD79A8',
    'kottayam_east': '#FDCB6E',
    'kottayam_west': '#6C5CE7',
    'idukki_north': '#00B894',
    'idukki_south': '#E17055',
    'ernakulam_east': '#74B9FF',
    'ernakulam_north': '#81ECEC',
    'ernakulam_city': '#FAB1A0',
    'thrissur_north': '#FF7675',
    'thrissur_south': '#FD79A8',
    'thrissur_city': '#A29BFE',
    'palakkad_west': '#55EFC4',
    'palakkad_east': '#FD79A8',
    'malappuram_central': '#74B9FF',
    'malappuram_east': '#DFE6E9',
    'malappuram_west': '#FFEAA7',
    'kozhikode_city': '#00B894',
    'kozhikode_north': '#0984E3',
    'kozhikode_rural': '#6C5CE7',
    'wayanad': '#00CEC9',
    'kannur_north': '#FD79A8',
    'kannur_south': '#FDCB6E',
    'kasaragod': '#E17055'
}

# Build hierarchy
hierarchy = {}

print("📖 Reading CSV and creating complete Kerala structure...\n")
print("=" * 70)

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        district_orig = row['Org District'].strip()
        district_clean = clean_id(district_orig)
        
        ac_orig = row['AC'].strip()
        ac_clean = clean_id(ac_orig)
        
        mandal_orig = row['Org Mandal'].strip()
        mandal_clean = clean_id(mandal_orig)
        
        lb_name_orig = row['LBName'].strip()
        lb_name_clean = clean_id(lb_name_orig)
        
        lb_type = 'Municipality' if row['LBType'] == 'M' else 'Corporation' if row['LBType'] == 'C' else 'Panchayat'
        lb_code = row['LBCode'].strip()
        total_wards = int(row['Ward Number'])
        
        # Initialize nested structure
        if district_clean not in hierarchy:
            hierarchy[district_clean] = {
                'original_name': district_orig,
                'acs': {}
            }
            
        if ac_clean not in hierarchy[district_clean]['acs']:
            hierarchy[district_clean]['acs'][ac_clean] = {
                'original_name': ac_orig,
                'mandals': {}
            }
            
        if mandal_clean not in hierarchy[district_clean]['acs'][ac_clean]['mandals']:
            hierarchy[district_clean]['acs'][ac_clean]['mandals'][mandal_clean] = {
                'original_name': mandal_orig,
                'local_bodies': {}
            }
            
        hierarchy[district_clean]['acs'][ac_clean]['mandals'][mandal_clean]['local_bodies'][lb_name_clean] = {
            'original_name': lb_name_orig,
            'type': lb_type,
            'code': lb_code,
            'total_wards': total_wards
        }

# Create final JSON structure
output = {
    'state': {
        'id': 'kerala',
        'name': 'Kerala',
        'total_districts': len(hierarchy),
        'total_acs': sum(len(d['acs']) for d in hierarchy.values())
    },
    'district_colors': DISTRICT_COLORS,
    'districts': []
}

print("🗺️  Building complete structure...\n")

total_mandals = 0
total_lbs = 0
total_wards = 0

for district_id, district_data in sorted(hierarchy.items()):
    district_obj = {
        'id': district_id,
        'name': district_data['original_name'],
        'color': DISTRICT_COLORS.get(district_id, '#95A5A6'),
        'total_acs': len(district_data['acs']),
        'assembly_constituencies': []
    }
    
    for ac_id, ac_data in sorted(district_data['acs'].items()):
        ac_obj = {
            'id': ac_id,
            'name': ac_data['original_name'],
            'district_id': district_id,
            'total_mandals': len(ac_data['mandals']),
            'mandals': []
        }
        
        for mandal_id, mandal_data in sorted(ac_data['mandals'].items()):
            mandal_obj = {
                'id': mandal_id,
                'name': mandal_data['original_name'],
                'total_local_bodies': len(mandal_data['local_bodies']),
                'local_bodies': []
            }
            
            for lb_id, lb_data in sorted(mandal_data['local_bodies'].items()):
                lb_obj = {
                    'id': lb_id,
                    'name': lb_data['original_name'],
                    'code': lb_data['code'],
                    'type': lb_data['type'],
                    'total_wards': lb_data['total_wards'],
                    'data_path': f"data/{district_id}/{ac_id}/{mandal_id}/{lb_id}.geojson"
                }
                
                mandal_obj['local_bodies'].append(lb_obj)
                total_lbs += 1
                total_wards += lb_data['total_wards']
            
            ac_obj['mandals'].append(mandal_obj)
            total_mandals += 1
        
        district_obj['assembly_constituencies'].append(ac_obj)
    
    output['districts'].append(district_obj)
    print(f"✅ {district_data['original_name']}: {len(district_data['acs'])} ACs")

# Create config directory
os.makedirs('config', exist_ok=True)

# Save complete structure
output_path = 'config/kerala_complete.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 70)
print(f"✅ Complete structure saved to: {output_path}")

# Print statistics
print("\n" + "=" * 70)
print("📊 COMPLETE KERALA STATISTICS")
print("=" * 70)
print(f"Total Districts: {len(output['districts'])}")
print(f"Total ACs: {output['state']['total_acs']}")
print(f"Total Mandals: {total_mandals}")
print(f"Total Local Bodies: {total_lbs}")
print(f"Total Wards: {total_wards}")
print("=" * 70)

# Print sample for Thiruvalla AC
print("\n" + "=" * 70)
print("📋 SAMPLE: THIRUVALLA AC (2 MANDALS)")
print("=" * 70)

for district in output['districts']:
    if district['id'] == 'pathanamthitta':
        for ac in district['assembly_constituencies']:
            if ac['id'] == 'thiruvalla':
                print(f"\nDistrict: {district['name']}")
                print(f"AC: {ac['name']}")
                print(f"Total Mandals: {ac['total_mandals']}\n")
                
                for mandal in ac['mandals']:
                    print(f"  🏘️  Mandal: {mandal['name']}")
                    print(f"     Local Bodies: {mandal['total_local_bodies']}")
                    mandal_wards = sum(lb['total_wards'] for lb in mandal['local_bodies'])
                    print(f"     Total Wards: {mandal_wards}")
                    print()
                    
                    for lb in mandal['local_bodies']:
                        print(f"        └─ {lb['type']}: {lb['name']}")
                        print(f"           Code: {lb['code']}")
                        print(f"           Wards: {lb['total_wards']}")
                        print(f"           Path: {lb['data_path']}")

print("\n" + "=" * 70)
print("✅ Generation complete! Ready to create HTML files.")
print("=" * 70)
