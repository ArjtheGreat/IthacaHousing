"""Regression tests for county 2026 parcel downloads and spatial enrichment."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from shapely.geometry import Polygon, mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from extractors.enrich_tompkins_parcels import (
    _year, _request_json, download_parcels_for_bbox, enrich_from_2026_parcels,
)


def fixture_feature(parcel_id, address, year, bbox, sqft=20000):
    x0, y0, x1, y1 = bbox
    return {
        "type": "Feature",
        "properties": {
            "FID": parcel_id, "PRINTKEY": str(parcel_id),
            "LOCADDR": address, "YEARBUILT": year,
            "SQ_FT": sqft, "SALE_PRICE": 2000000,
            "ASMT": 1500000, "LAND": 500000,
            "ACRES": 0.2, "ZONING": "R-3", "PROPCLASS": "411",
        },
        "geometry": mapping(Polygon([
            (x0, y0), (x1, y0), (x1, y1), (x0, y1),
        ])),
    }


class CountyParcelTests(unittest.TestCase):
    def test_invalid_years_never_become_years(self):
        for year in (None, "", "0", "9999", "unknown", 1500, 2028):
            self.assertIsNone(_year(year))
        self.assertEqual(_year("2022"), 2022)

    def test_geographic_match_fills_missing_but_keeps_known_year(self):
        features = [
            fixture_feature(101, "201 OAK AVE", "2023",
                            (-76.500, 42.440, -76.490, 42.450)),
            fixture_feature(102, "205 DRYDEN RD", "1990",
                            (-76.490, 42.440, -76.480, 42.450)),
        ]
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "snapshot.geojson"
            snapshot.write_text(json.dumps({
                "type": "FeatureCollection", "features": features
            }), encoding="utf-8")
            frame = pd.DataFrame([
                {"PropertyId": "1", "ListingAddress": "201 Oak Avenue",
                 "latitude": 42.445, "longitude": -76.495,
                 "year_built": None, "assessment_sqft": None},
                {"PropertyId": "2", "ListingAddress": "205 Dryden Rd",
                 "latitude": 42.445, "longitude": -76.485,
                 "year_built": 1980, "assessment_sqft": None},
                {"PropertyId": "3", "ListingAddress": "Far away",
                 "latitude": 42.480, "longitude": -76.450,
                 "year_built": None, "assessment_sqft": None},
            ])
            with patch(
                "extractors.enrich_tompkins_parcels.download_parcels_for_bbox",
                return_value=snapshot,
            ):
                out = enrich_from_2026_parcels(frame)

        self.assertEqual(len(out), len(frame))
        self.assertEqual(int(out.loc[0, "year_built"]), 2023)
        self.assertEqual(out.loc[0, "year_built_source"], "tompkins_2026_parcel")
        self.assertEqual(out.loc[0, "parcel_match_method"], "polygon_and_address")
        self.assertEqual(int(out.loc[0, "assessment_sqft"]), 20000)
        self.assertEqual(int(out.loc[0, "assessment_total_value"]), 1500000)
        self.assertEqual(int(out.loc[1, "year_built"]), 1980)
        self.assertEqual(out.loc[1, "year_built_source"], "legacy_assessment_csv")
        self.assertTrue(pd.isna(out.loc[2, "year_built"]))
        self.assertEqual(out.loc[0, "parcel_printkey"], "101")

    def test_large_id_query_uses_post_instead_of_long_get_url(self):
        class FakeResponse:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return {"type": "FeatureCollection", "features": []}

        class FakeSession:
            def __init__(self):
                self.calls = []
            def post(self, url, data, timeout):
                self.calls.append(("POST", data))
                return FakeResponse()
            def get(self, url, params, timeout):
                self.calls.append(("GET", params))
                return FakeResponse()

        session = FakeSession()
        ids = ",".join(map(str, range(250)))
        result = _request_json(session, {
            "objectIds": ids, "f": "geojson", "returnGeometry": "true",
        })
        self.assertEqual(result["type"], "FeatureCollection")
        self.assertEqual([kind for kind, _ in session.calls], ["POST"])
        self.assertEqual(session.calls[0][1]["objectIds"], ids)

    def test_paginated_download_refuses_incomplete_pages(self):
        bbox = (-76.51, 42.43, -76.47, 42.47)
        features = [
            fixture_feature(i, f"{i} MAIN ST", "2020",
                            (-76.50, 42.44, -76.49, 42.45))
            for i in range(1, 4)
        ]
        with tempfile.TemporaryDirectory() as directory, patch(
            "extractors.enrich_tompkins_parcels.PAGE_SIZE", 2
        ), patch(
            "extractors.enrich_tompkins_parcels._request_json",
            side_effect=[
                {"objectIds": [1, 2, 3]},
                {"type": "FeatureCollection", "features": features[:2]},
                {"type": "FeatureCollection", "features": features[2:]},
            ],
        ):
            class FakeSession:
                def close(self):
                    pass
            target = download_parcels_for_bbox(
                bbox, cache_dir=directory, session=FakeSession(),
            )
            self.assertEqual(len(json.loads(target.read_text())["features"]), 3)
            self.assertEqual(json.loads(target.read_text())["query_bbox_epsg4326"], list(bbox))


if __name__ == "__main__":
    unittest.main()
