from typing import Any, Dict, List


class JsonReader:
    """A class to read and manipulate JSON data for ProtSpace."""

    def __init__(self, json_data: Dict[str, Any]):
        self.data = json_data

    def get_projection_names(self) -> List[str]:
        return [proj["name"] for proj in self.data.get("projections", [])]

    def get_all_features(self) -> List[str]:
        features = set()
        for protein_data in self.data.get("protein_data", {}).values():
            features.update(protein_data.get("features", {}).keys())
        return list(features)

    def get_protein_ids(self) -> List[str]:
        return list(self.data.get("protein_data", {}).keys())

    def get_projection_data(self, projection_name: str) -> List[Dict[str, Any]]:
        for proj in self.data.get("projections", []):
            if proj["name"] == projection_name:
                return proj.get("data", [])
        raise ValueError(f"Projection {projection_name} not found")

    def get_projection_info(self, projection_name: str) -> Dict[str, Any]:
        for proj in self.data.get("projections", []):
            if proj["name"] == projection_name:
                result = {"dimensions": proj.get("dimensions")}
                if "info" in proj:
                    result["info"] = proj["info"]
                return result
        raise ValueError(f"Projection {projection_name} not found")

    def get_protein_features(self, protein_id: str) -> Dict[str, Any]:
        return self.data.get("protein_data", {}).get(protein_id, {}).get("features", {})

    def get_feature_colors(self, feature: str) -> Dict[str, str]:
        return self.data.get('visualization_state', {}).get('feature_colors', {}).get(feature, {})

    def get_marker_shape(self, feature: str) -> Dict[str, str]:
        return self.data.get('visualization_state', {}).get('marker_shapes', {}).get(feature, {})

    def get_unique_feature_values(self, feature: str) -> List[Any]:
        unique_values = set()
        for protein_data in self.data.get("protein_data", {}).values():
            value = protein_data.get("features", {}).get(feature)
            if value is not None:
                unique_values.add(value)
        return list(unique_values)

    def update_feature_color(self, feature: str, value: str, color: str):
        if 'visualization_state' not in self.data:
            self.data['visualization_state'] = {}
        if 'feature_colors' not in self.data['visualization_state']:
            self.data['visualization_state']['feature_colors'] = {}
        if feature not in self.data['visualization_state']['feature_colors']:
            self.data['visualization_state']['feature_colors'][feature] = {}

        self.data['visualization_state']['feature_colors'][feature][value] = color

    def update_marker_shape(self, feature: str, value: str, shape: str):
        if 'visualization_state' not in self.data:
            self.data['visualization_state'] = {}
        if 'marker_shapes' not in self.data['visualization_state']:
            self.data['visualization_state']['marker_shapes'] = {}
        if feature not in self.data['visualization_state']['marker_shapes']:
            self.data['visualization_state']['marker_shapes'][feature] = {}

        self.data['visualization_state']['marker_shapes'][feature][value] = shape

    def get_data(self) -> Dict[str, Any]:
        """Return the current JSON data."""
        return self.data
