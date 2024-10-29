import json
import argparse
from protspace.data_loader import JsonReader

def print_dimensionality_reduction_info(reader: JsonReader, verbosity: int) -> None:
    """Print information about dimensionality reduction methods based on verbosity level."""
    projections = reader.get_projection_names()

    if verbosity == 0:
        print(f"\nProjections: {', '.join(projections)}")
        return

    print("\n=== Dimensionality Reduction Methods ===")
    for proj_name in projections:
        print(f"\nProjection: {proj_name}")
        info = reader.get_projection_info(proj_name)

        if info.get("dimensions"):
            print(f"Dimensions: {info['dimensions']}")

        if verbosity >= 2 and info.get("info"):
            print("Additional Information:")
            for key, value in info["info"].items():
                print(f"  - {key}: {value}")

def print_feature_info(reader: JsonReader, verbosity: int) -> None:
    """Print feature information based on verbosity level."""
    features = reader.get_all_features()

    if verbosity == 0:
        print(f"\nFeatures ({len(features)}): {', '.join(features)}")
        return

    print("\n=== Features Overview ===")
    for feature in features:
        unique_values = reader.get_unique_feature_values(feature)
        print(f"\nFeature: {feature}")
        print(f"Unique values: {len(unique_values)}")
        if verbosity >= 2:
            print("Values:", unique_values[:5], "..." if len(unique_values) > 5 else "")

def print_visualization_info(reader: JsonReader) -> None:
    """Print information about feature colors and shapes if available."""
    print("\n=== Visualization Settings ===")
    features = reader.get_all_features()

    for feature in features:
        print(f"\nFeature: {feature}")

        # Print color mappings
        colors = reader.get_feature_colors(feature)
        if colors:
            print("Color mappings:")
            for value, color in colors.items():
                print(f"  - {value}: {color}")

        # Print shape mappings
        shapes = reader.get_marker_shape(feature)
        if shapes:
            print("Shape mappings:")
            for value, shape in shapes.items():
                print(f"  - {value}: {shape}")

def main():
    parser = argparse.ArgumentParser(description='Analyze ProtSpace JSON file.')
    parser.add_argument('json_file', help='Path to the JSON file')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                       help='Increase output verbosity (up to -vvv)')
    args = parser.parse_args()

    # Limit verbosity to 3
    args.verbose = min(args.verbose, 3)

    try:
        # Read JSON file
        with open(args.json_file, 'r') as f:
            data = json.load(f)

    except FileNotFoundError:
        print(f"Error: File '{args.json_file}' not found")
    except json.JSONDecodeError:
        print(f"Error: '{args.json_file}' is not a valid JSON file")
    except Exception as e:
        print(f"Error: {str(e)}")

    # Create JsonReader instance
    reader = JsonReader(data)

    # Print basic statistics
    print(f"Summary:")
    print(f"- Proteins: {len(reader.get_protein_ids())}")
    print(f"- Features: {len(reader.get_all_features())}")
    print(f"- Projections: {len(reader.get_projection_names())}")

    # Print detailed information based on verbosity
    print_dimensionality_reduction_info(reader, args.verbose)
    print_feature_info(reader, args.verbose)

    # Print visualization information at highest verbosity level
    if args.verbose >= 3:
        print_visualization_info(reader)


if __name__ == "__main__":
    main()