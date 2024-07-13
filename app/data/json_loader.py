import json
from typing import Dict, List, Optional

class JsonReader:
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.data = None

    def _load_data(self):
        if self.data is None:
            with open(self.json_file, 'r') as f:
                self.data = json.load(f)

    def get_protein_data(self) -> Dict:
        self._load_data()
        return self.data.get('protein_data', {})

    def get_projections(self) -> List[Dict]:
        self._load_data()
        return self.data.get('projections', [])

    def get_projection_names(self) -> List[str]:
        projections = self.get_projections()
        return [proj['name'] for proj in projections]

    def get_protein_ids(self) -> List[str]:
        protein_data = self.get_protein_data()
        return list(protein_data.keys())

    def get_projection_data(self, projection_name: str) -> Optional[List[Dict]]:
        projections = self.get_projections()
        for proj in projections:
            if proj['name'] == projection_name:
                return proj.get('data', [])
        return None

    def get_projection_info(self, projection_name: str) -> Optional[Dict]:
        projections = self.get_projections()
        for proj in projections:
            if proj['name'] == projection_name:
                return {k: v for k, v in proj.items() if k != 'data'}
        return None

    def get_protein_features(self, protein_id: str) -> Optional[Dict]:
        protein_data = self.get_protein_data()
        return protein_data.get(protein_id, {}).get('features')

    def get_all_features(self) -> List[str]:
        protein_data = self.get_protein_data()
        all_features = set()
        for protein in protein_data.values():
            all_features.update(protein.get('features', {}).keys())
        return list(all_features)