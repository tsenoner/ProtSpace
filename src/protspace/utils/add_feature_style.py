import argparse
import json
from typing import Dict

ALLOWED_SHAPES = [
    'circle', 'circle-open', 'cross', 'diamond',
    'diamond-open', 'square', 'square-open', 'x'
]

def load_feature_styles(feature_styles_input: str) -> Dict[str, Dict[str, Dict[str, str]]]:
    try:
        # Try to parse as JSON string
        return json.loads(feature_styles_input)
    except json.JSONDecodeError:
        # If not a valid JSON string, try to load as a file
        try:
            with open(feature_styles_input, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError(
                f"Invalid input: '{feature_styles_input}' is neither a valid JSON string nor a path to an existing JSON file."
            )

def add_feature_styles(
    json_file: str, feature_styles: Dict[str, Dict[str, Dict[str, str]]], output_file: str
) -> None:
    with open(json_file, "r") as f:
        data = json.load(f)

    if "visualization_state" not in data:
        data["visualization_state"] = {}
    if "feature_colors" not in data["visualization_state"]:
        data["visualization_state"]["feature_colors"] = {}
    if "marker_shapes" not in data["visualization_state"]:
        data["visualization_state"]["marker_shapes"] = {}

    for feature, styles in feature_styles.items():
        # Check if the feature exists
        if feature not in data["protein_data"][next(iter(data["protein_data"]))]["features"]:
            raise ValueError(f"Feature '{feature}' does not exist in the protein data.")

        # Check if all values exist for the feature
        all_values = set()
        for protein_data in data["protein_data"].values():
            all_values.add(str(protein_data["features"].get(feature)))

        # Add colors
        if "colors" in styles:
            if feature not in data["visualization_state"]["feature_colors"]:
                data["visualization_state"]["feature_colors"][feature] = {}
            for value, color in styles["colors"].items():
                if value not in all_values:
                    raise ValueError(f"Value '{value}' does not exist for feature '{feature}'.")
                data["visualization_state"]["feature_colors"][feature][value] = color

        # Add shapes
        if "shapes" in styles:
            if feature not in data["visualization_state"]["marker_shapes"]:
                data["visualization_state"]["marker_shapes"][feature] = {}
            for value, shape in styles["shapes"].items():
                if value not in all_values:
                    raise ValueError(f"Value '{value}' does not exist for feature '{feature}'.")
                if shape not in ALLOWED_SHAPES:
                    raise ValueError(f"Shape '{shape}' is not allowed. Allowed shapes are: {', '.join(ALLOWED_SHAPES)}")
                data["visualization_state"]["marker_shapes"][feature][value] = shape

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

def main():
    parser = argparse.ArgumentParser(
        description="Add or update feature colors and shapes in ProtSpace JSON file"
    )
    parser.add_argument("json_file", help="Path to the input JSON file")
    parser.add_argument("output_file", help="Path to save the updated JSON file")
    parser.add_argument(
        "--feature_styles",
        required=True,
        help='JSON string of feature styles or path to a JSON file, e.g., \'{"feature1": {"colors": {"value1": "rgba(255, 0, 0, 0.8)"}, "shapes": {"value1": "circle"}}}\' or \'path/to/styles.json\'',
    )

    args = parser.parse_args()
    feature_styles = load_feature_styles(args.feature_styles)
    add_feature_styles(args.json_file, feature_styles, args.output_file)

if __name__ == "__main__":
    main()