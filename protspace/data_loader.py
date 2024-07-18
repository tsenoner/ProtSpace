import json
from typing import Dict, List, Any


class JsonReader:
    def __init__(self, json_file: str):
        with open(json_file, 'r') as f:
            self.data = json.load(f)

    def get_projection_names(self) -> List[str]:
        return [proj['name'] for proj in self.data['projections']]

    def get_all_features(self) -> List[str]:
        features = set()
        for protein_data in self.data['protein_data'].values():
            features.update(protein_data['features'].keys())
        return list(features)

    def get_protein_ids(self) -> List[str]:
        return list(self.data['protein_data'].keys())

    def get_projection_data(self, projection_name: str) -> List[Dict[str, Any]]:
        for proj in self.data['projections']:
            if proj['name'] == projection_name:
                return proj['data']
        raise ValueError(f"Projection {projection_name} not found")

    def get_projection_info(self, projection_name: str) -> Dict[str, Any]:
        for proj in self.data['projections']:
            if proj['name'] == projection_name:
                return {
                    'dimensions': proj['dimensions'],
                    'info': proj['info']
                }
        raise ValueError(f"Projection {projection_name} not found")

    def get_protein_features(self, protein_id: str) -> Dict[str, Any]:
        return self.data['protein_data'].get(protein_id, {}).get('features', {})