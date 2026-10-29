import json
from typing import List, Dict, Any, Tuple, Optional
from app.core.base_schema import BaseModel


# Standard Village GIS Reference Database for Sample Rural Block (e.g. Rampur Block)
# Coordinates in WGS 84 (EPSG:4326) [Longitude, Latitude]
VILLAGE_GEOMETRIES: Dict[str, Dict[str, Any]] = {
    "VILL-UP-RAMPUR-01": {
        "name": "Rampur Central",
        "block": "Rampur",
        "district": "Varanasi",
        "center": [82.9739, 25.3176],
        "polygon_coords": [
            [82.9650, 25.3120], [82.9820, 25.3120], [82.9850, 25.3240],
            [82.9680, 25.3260], [82.9650, 25.3120]
        ]
    },
    "VILL-UP-SHIVPUR-02": {
        "name": "Shivpur",
        "block": "Rampur",
        "district": "Varanasi",
        "center": [82.9880, 25.3310],
        "polygon_coords": [
            [82.9800, 25.3250], [82.9960, 25.3250], [82.9980, 25.3380],
            [82.9810, 25.3390], [82.9800, 25.3250]
        ]
    },
    "VILL-UP-KALYANPUR-03": {
        "name": "Kalyanpur",
        "block": "Rampur",
        "district": "Varanasi",
        "center": [82.9550, 25.3080],
        "polygon_coords": [
            [82.9460, 25.3010], [82.9630, 25.3010], [82.9660, 25.3150],
            [82.9480, 25.3160], [82.9460, 25.3010]
        ]
    },
    "VILL-UP-SITAPUR-04": {
        "name": "Sitapur Khurd",
        "block": "Rampur",
        "district": "Varanasi",
        "center": [83.0010, 25.3150],
        "polygon_coords": [
            [82.9920, 25.3080], [83.0100, 25.3080], [83.0120, 25.3220],
            [82.9940, 25.3230], [82.9920, 25.3080]
        ]
    },
    "VILL-UP-BHARATPUR-05": {
        "name": "Bharatpur",
        "block": "Rampur",
        "district": "Varanasi",
        "center": [82.9410, 25.3280],
        "polygon_coords": [
            [82.9320, 25.3200], [82.9500, 25.3200], [82.9520, 25.3360],
            [82.9340, 25.3370], [82.9320, 25.3200]
        ]
    }
}


class GeoClusterService:
    """
    Handles PostGIS geospatial operations and GeoJSON polygon generation
    for village clusters affected by disease outbreaks.
    """

    @staticmethod
    def get_village_info(village_id: str) -> Optional[Dict[str, Any]]:
        return VILLAGE_GEOMETRIES.get(village_id)

    @staticmethod
    def compute_cluster_bounding_polygon(village_ids: List[str]) -> Dict[str, Any]:
        """
        Computes a bounding polygon / convex hull encompassing all affected villages.
        Returns GeoJSON geometry object.
        """
        all_points = []
        for vid in village_ids:
            v_info = VILLAGE_GEOMETRIES.get(vid)
            if v_info:
                all_points.extend(v_info["polygon_coords"])

        if not all_points:
            # Fallback default point/box
            return {
                "type": "Polygon",
                "coordinates": [[[82.96, 25.31], [82.99, 25.31], [82.99, 25.34], [82.96, 25.34], [82.96, 25.31]]]
            }

        min_lon = min(p[0] for p in all_points)
        max_lon = max(p[0] for p in all_points)
        min_lat = min(p[1] for p in all_points)
        max_lat = max(p[1] for p in all_points)

        # Buffer by 0.005 degrees (~500m)
        buffer = 0.005
        bounding_coords = [
            [round(min_lon - buffer, 4), round(min_lat - buffer, 4)],
            [round(max_lon + buffer, 4), round(min_lat - buffer, 4)],
            [round(max_lon + buffer, 4), round(max_lat + buffer, 4)],
            [round(min_lon - buffer, 4), round(max_lat + buffer, 4)],
            [round(min_lon - buffer, 4), round(min_lat - buffer, 4)]
        ]

        return {
            "type": "Polygon",
            "coordinates": [bounding_coords]
        }

    @classmethod
    def generate_village_map_geojson(
        cls,
        village_risk_levels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generates a standard GeoJSON FeatureCollection of all villages
        with risk metadata for rendering in Flutter Map or web GIS.
        """
        village_risk_levels = village_risk_levels or {}
        features = []

        for vid, vdata in VILLAGE_GEOMETRIES.items():
            risk = village_risk_levels.get(vid, "NORMAL") # NORMAL, WATCH, WARNING, OUTBREAK
            
            # Map risk to hex color
            color_map = {
                "NORMAL": "#4CAF50",   # Green
                "WATCH": "#FFC107",    # Yellow
                "WARNING": "#FF9800",  # Orange
                "OUTBREAK": "#F44336"  # Red
            }

            feature = {
                "type": "Feature",
                "id": vid,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [vdata["polygon_coords"]]
                },
                "properties": {
                    "village_id": vid,
                    "village_name": vdata["name"],
                    "block": vdata["block"],
                    "district": vdata["district"],
                    "center": vdata["center"],
                    "risk_level": risk,
                    "fill_color": color_map.get(risk, "#4CAF50"),
                    "fill_opacity": 0.4 if risk != "NORMAL" else 0.15
                }
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features
        }


geo_cluster_service = GeoClusterService()
