import argparse
import json
from typing import Any, Dict


def load_feature_colors(feature_colors_input: str) -> Dict[str, Dict[str, str]]:
    try:
        # Try to parse as JSON string
        return json.loads(feature_colors_input)
    except json.JSONDecodeError:
        # If not a valid JSON string, try to load as a file
        try:
            with open(feature_colors_input, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError(
                f"Invalid input: '{feature_colors_input}' is neither a valid JSON string nor a path to an existing JSON file."
            )


def add_feature_colors(
    json_file: str, feature_colors: Dict[str, Dict[str, str]], output_file: str
) -> None:
    with open(json_file, "r") as f:
        data = json.load(f)

    if "visualization_state" not in data:
        data["visualization_state"] = {}
    if "feature_colors" not in data["visualization_state"]:
        data["visualization_state"]["feature_colors"] = {}

    for feature, color_map in feature_colors.items():
        # Check if the feature exists
        if (
            feature
            not in data["protein_data"][next(iter(data["protein_data"]))][
                "features"
            ]
        ):
            raise ValueError(
                f"Feature '{feature}' does not exist in the protein data."
            )

        # Check if all values exist for the feature
        all_values = set()
        for protein_data in data["protein_data"].values():
            all_values.add(str(protein_data["features"].get(feature)))

        for value in color_map.keys():
            if value not in all_values:
                raise ValueError(
                    f"Value '{value}' does not exist for feature '{feature}'."
                )

        if feature not in data["visualization_state"]["feature_colors"]:
            data["visualization_state"]["feature_colors"][feature] = {}
        data["visualization_state"]["feature_colors"][feature].update(color_map)

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Add or update feature colors in ProtSpace JSON file"
    )
    parser.add_argument("json_file", help="Path to the input JSON file")
    parser.add_argument(
        "output_file", help="Path to save the updated JSON file"
    )
    parser.add_argument(
        "--feature_colors",
        required=True,
        help='JSON string of feature colors or path to a JSON file, e.g., \'{"feature1": {"value1": "#FF0000", "value2": "#00FF00"}}\' or \'path/to/colors.json\'',
    )

    args = parser.parse_args()
    feature_colors = load_feature_colors(args.feature_colors)
    add_feature_colors(args.json_file, feature_colors, args.output_file)


if __name__ == "__main__":
    main()
