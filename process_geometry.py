import json
import os
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# List of source files
source_files = [
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Municipality/Thiruvalla.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Anicadu.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Kadapra.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Kallooppara.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Kaviyoor.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Kunnathanam.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Kuttoor.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Mallappally.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Nedumpuram.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Niranam.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Peringara.json",
    "/Users/devandev/Desktop/ward_jsons/Pathanamthitta/Grama Panchayat/Puramattom.json"
]

# LSGD to Mandal Mapping (Thiruvalla & Mallappally)
lsgd_to_mandal = {
    # Thiruvalla Mandal (Thiruvalla Municipality + Pulikeezhu Block)
    'Thiruvalla': 'Thiruvalla',
    'Kuttoor': 'Thiruvalla',
    'Kadapra': 'Thiruvalla',
    'Nedumpuram': 'Thiruvalla',
    'Niranam': 'Thiruvalla',
    'Peringara': 'Thiruvalla',
    
    # Mallappally Mandal (Mallappally Block + Puramattom from Koipuram)
    'Kaviyoor': 'Mallappally',
    'Kunnathanam': 'Mallappally',
    'Anicadu': 'Mallappally',
    'Kallooppara': 'Mallappally',
    'Mallappally': 'Mallappally',
    'Puramattom': 'Mallappally'
}

all_wards = []
panchayat_geoms = {} # Key: LSGD Name
mandal_geoms = {}    # Key: Mandal Name
ac_geoms = []

print("Reading source files...")
for file_path in source_files:
    if not os.path.exists(file_path):
        print(f"Warning: File not found: {file_path}")
        continue
        
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            features = data.get('features', [])
            
            for feature in features:
                props = feature.get('properties', {})
                lsgd_name = props.get('LSGD')
                
                # Normalize LSGD name
                mandal = lsgd_to_mandal.get(lsgd_name, 'Unknown')
                
                # Add Mandal info to properties
                props['Mandal'] = mandal
                feature['properties'] = props
                
                # Add to all wards list
                all_wards.append(feature)
                
                geom = shape(feature['geometry'])
                
                # Collect geometry for Panchayat aggregation
                if lsgd_name not in panchayat_geoms:
                    panchayat_geoms[lsgd_name] = {'geoms': [], 'mandal': mandal}
                panchayat_geoms[lsgd_name]['geoms'].append(geom)
                
                # Collect geometry for Mandal aggregation
                if mandal not in mandal_geoms:
                    mandal_geoms[mandal] = []
                mandal_geoms[mandal].append(geom)
                
                # Collect geometry for AC aggregation
                ac_geoms.append(geom)
                
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

print(f"Total wards loaded: {len(all_wards)}")

# Process Panchayats (Level 3)
print("Processing Panchayat boundaries...")
panchayat_features = []
for lsgd, data in panchayat_geoms.items():
    try:
        merged_geom = unary_union(data['geoms'])
        panchayat_features.append({
            "type": "Feature",
            "geometry": mapping(merged_geom),
            "properties": {
                "LSGD": lsgd,
                "Mandal": data['mandal'],
                "Level": "Panchayat"
            }
        })
    except Exception as e:
        print(f"Error merging panchayat {lsgd}: {e}")

# Process Mandals (Level 2)
print("Processing Mandal boundaries...")
mandal_features = []
for mandal, geoms in mandal_geoms.items():
    try:
        merged_geom = unary_union(geoms)
        mandal_features.append({
            "type": "Feature",
            "geometry": mapping(merged_geom),
            "properties": {
                "Mandal": mandal,
                "Level": "Mandal"
            }
        })
    except Exception as e:
        print(f"Error merging mandal {mandal}: {e}")

# Process AC (Level 1)
print("Processing AC boundary...")
ac_feature = None
try:
    merged_ac_geom = unary_union(ac_geoms)
    ac_feature = {
        "type": "Feature",
        "geometry": mapping(merged_ac_geom),
        "properties": {
            "Name": "Thiruvalla AC",
            "Level": "AC"
        }
    }
except Exception as e:
    print(f"Error merging AC: {e}")

# Construct final data object
final_data = {
    "ac": {
        "type": "FeatureCollection",
        "features": [ac_feature] if ac_feature else []
    },
    "mandals": {
        "type": "FeatureCollection",
        "features": mandal_features
    },
    "panchayats": {
        "type": "FeatureCollection",
        "features": panchayat_features
    },
    "wards": {
        "type": "FeatureCollection",
        "features": all_wards
    }
}

output_path = "/Users/devandev/Desktop/Thiruvalla/data.js"
with open(output_path, 'w') as f:
    f.write("const thiruvallaData = ")
    json.dump(final_data, f)
    f.write(";")

print(f"Successfully wrote data to {output_path}")
