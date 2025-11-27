import csv
import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

from shapely.geometry import shape, mapping
from shapely.ops import unary_union

CSV_PATH = "data/corporation_ward_mapping.csv"
DISTRICT_DATA_DIR = "data/14_districts"
OUTPUT_PATH = "data/corporation_mandals.json"
KOVALAM_LB_PATH = (
    "data/thiruvananthapuram_south/kovalam/kovalam/tvm_corporation_kovalam.geojson"
)


def clean_id(text: str) -> str:
    import re

    cleaned = re.sub(r"[^\w\s-]", "", text or "")
    cleaned = re.sub(r"[-\s]+", "_", cleaned)
    return cleaned.lower().strip("_")


def ensure_dir(path: str):
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class WardIndex:
    """Caches ward geometries per (district, corporation, ward)."""

    def __init__(self):
        self._district_cache: Dict[str, Dict] = {}
        self._corp_index: Dict[str, Dict[str, Dict[str, Dict]]] = {}

    def load_district(self, district_slug: str):
        if district_slug in self._district_cache:
            return self._district_cache[district_slug]

        path = os.path.join(DISTRICT_DATA_DIR, f"{district_slug}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"District data not found: {path}")

        data = load_json(path)
        self._district_cache[district_slug] = data
        self._build_corp_index(district_slug, data)
        return data

    def _build_corp_index(self, district_slug: str, data: Dict):
        corp_lookup: Dict[str, Dict[str, Dict]] = defaultdict(dict)
        acs = data.get("acs") or data.get("assembly_constituencies") or []

        for ac in acs:
            for mandal in ac.get("mandals", []):
                for lb in mandal.get("local_bodies", []):
                    lb_type = (lb.get("type") or "").lower()
                    if lb_type not in ("c", "corporation"):
                        continue
                    corp_key = clean_id(lb.get("name"))
                    ward_map = corp_lookup[corp_key]

                    for ward in lb.get("wards", []):
                        ward_key = clean_id(ward.get("ward_name"))
                        if not ward_key:
                            continue
                        ward_map[ward_key] = ward

        self._corp_index[district_slug] = corp_lookup

    def get_ward(
        self, district_slug: str, corporation_name: str, ward_name: str
    ) -> Dict:
        import difflib

        self.load_district(district_slug)
        corp_key = clean_id(corporation_name)
        ward_key = clean_id(ward_name)
        district_corps = self._corp_index.get(district_slug, {})
        corp_wards = district_corps.get(corp_key)
        if corp_wards is None:
            corp_match = difflib.get_close_matches(
                corp_key, district_corps.keys(), n=1, cutoff=0.7
            )
            if corp_match:
                corp_key = corp_match[0]
                corp_wards = district_corps[corp_key]
                print(
                    f"ℹ️  Using fuzzy match '{corp_key}' for corporation "
                    f"'{corporation_name}'"
                )
            else:
                corp_wards = {}
        ward = corp_wards.get(ward_key)
        if ward:
            return ward
        # Attempt fuzzy matching for spelling variations
        candidates = difflib.get_close_matches(
            ward_key, corp_wards.keys(), n=1, cutoff=0.68
        )
        if candidates:
            match = candidates[0]
            print(
                f"ℹ️  Using fuzzy match '{match}' for ward '{ward_name}' "
                f"in corporation '{corporation_name}'"
            )
            return corp_wards[match]
        raise KeyError(
            f"Ward '{ward_name}' not found in corporation '{corporation_name}' "
            f"for district '{district_slug}'"
        )


def dissolve_wards(wards: List[Dict]):
    ward_geoms = []
    for ward in wards:
        geom = ward.get("geometry")
        if not geom:
            continue
        geom_shape = shape(geom).buffer(0)
        ward_geoms.append(geom_shape)

    if not ward_geoms:
        return None

    return mapping(unary_union(ward_geoms))


def load_csv_rows() -> List[Dict]:
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
    return rows


def group_by_mandal(rows: List[Dict], ward_index: WardIndex):
    groups: Dict[Tuple[str, str, str], Dict] = {}
    failures = 0

    for row in rows:
        district_name = row["District Name"].strip()
        district_slug = clean_id(district_name)
        ac_name = row["AC"].strip()
        org_mandal = row["Organisational Mandal"].strip()
        corporation = row["Corporation"].strip()
        ward_name = row["Ward Name"].strip()

        key = (district_slug, clean_id(ac_name), clean_id(org_mandal))
        if key not in groups:
            groups[key] = {
                "district_id": district_slug,
                "district_name": district_name,
                "ac_id": clean_id(ac_name),
                "ac_name": ac_name,
                "mandal_id": clean_id(org_mandal),
                "mandal_name": org_mandal,
                "corporation_id": clean_id(corporation),
                "corporation_name": corporation,
                "wards": [],
            }

        try:
            ward = ward_index.get_ward(district_slug, corporation, ward_name)
        except KeyError as err:
            failures += 1
            print(f"⚠️  {err}")
            continue

        groups[key]["wards"].append(
            {
                "ward_number": ward.get("ward_number"),
                "ward_name": ward.get("ward_name"),
                "geometry": ward.get("geometry"),
            }
        )

    print(f"✅ Processed CSV rows: {len(rows)}. Missing wards: {failures}.")
    return groups


def build_features(groups: Dict[Tuple[str, str, str], Dict]):
    features = []
    kovalam_group = None

    for data in groups.values():
        geometry = dissolve_wards(data["wards"])
        if not geometry:
            print(
                f"⚠️  Skipping {data['ac_name']} / {data['mandal_name']} "
                f"due to missing geometries"
            )
            continue

        ward_features = []
        for ward in data["wards"]:
            ward_features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "ward_number": ward.get("ward_number"),
                        "ward_name": ward.get("ward_name"),
                    },
                    "geometry": ward.get("geometry"),
                }
            )

        feature = {
            "type": "Feature",
            "properties": {
                "district_id": data["district_id"],
                "district_name": data["district_name"],
                "ac_id": data["ac_id"],
                "ac_name": data["ac_name"],
                "mandal_id": data["mandal_id"],
                "mandal_name": data["mandal_name"],
                "corporation_id": data["corporation_id"],
                "corporation_name": data["corporation_name"],
                "ward_count": len(data["wards"]),
                "wards": [
                    {
                        "ward_number": w.get("ward_number"),
                        "ward_name": w.get("ward_name"),
                    }
                    for w in data["wards"]
                ],
                "ward_features": ward_features,
            },
            "geometry": geometry,
        }
        feature["properties"]["ward_numbers"] = [
            w.get("ward_number") for w in data["wards"]
        ]

        features.append(feature)

        if (
            data["district_id"] == "thiruvananthapuram"
            and data["ac_id"] == "kovalam"
            and data["mandal_id"] == "kovalam"
        ):
            kovalam_group = data

    return features, kovalam_group


def write_feature_collection(path: str, features: List[Dict], extra: Dict = None):
    payload = {
        "type": "FeatureCollection",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "features": features,
    }
    if extra:
        payload.update(extra)
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)


def write_kovalam_local_body(group: Dict):
    if not group:
        print("⚠️  Kovalam group not found; skipping local-body export.")
        return

    features = []
    for ward in group["wards"]:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "ward_number": ward.get("ward_number"),
                    "ward_name": ward.get("ward_name"),
                    "corporation": group["corporation_name"],
                    "ac": group["ac_name"],
                },
                "geometry": ward.get("geometry"),
            }
        )

    write_feature_collection(
        KOVALAM_LB_PATH,
        features,
        extra={
            "label": "TVM Corporation (Kovalam)",
            "ward_count": len(features),
        },
    )
    print(
        f"✅ Generated Kovalam-specific ward file with {len(features)} wards "
        f"({KOVALAM_LB_PATH})"
    )


def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            f"Corporation mapping CSV not found at {CSV_PATH}. "
            "Please place the sheet in the data directory."
        )

    ward_index = WardIndex()
    rows = load_csv_rows()
    groups = group_by_mandal(rows, ward_index)
    features, kovalam_group = build_features(groups)

    write_feature_collection(OUTPUT_PATH, features)
    print(
        f"✅ Generated corporation mandal shapes: {len(features)} features "
        f"({OUTPUT_PATH})"
    )

    write_kovalam_local_body(kovalam_group)


if __name__ == "__main__":
    main()

