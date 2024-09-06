import argparse
from typing import Optional

from .app import ProtSpace
from .config import DEFAULT_PORT, IMAGE_OUTPUT_DIR


def create_file(
    app: ProtSpace,
    projection: str,
    feature: str,
    output_dir: str = IMAGE_OUTPUT_DIR,
    width: int = 1600,
    height: int = 1000,
) -> None:
    available_projections = app.reader.get_projection_names()
    available_features = app.reader.get_all_features()

    if projection not in available_projections:
        raise ValueError(
            f"Projection '{projection}' not found. Available projections are: {', '.join(available_projections)}"
        )

    if feature not in available_features:
        raise ValueError(
            f"Feature '{feature}' not found. Available features are: {', '.join(available_features)}"
        )

    app.generate_images(
        output_dir=output_dir,
        projection=projection,
        feature=feature,
        width=width,
        height=height,
    )
    print(f"Image generated and saved in {output_dir}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ProtSpace")
    parser.add_argument("json", help="Path to the input JSON file")
    parser.add_argument(
        "--pdb_dir",
        required=False,
        help="Path to the directory containing PDB files",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port to run the server on",
    )
    return parser.parse_args()


def main(
    json: str,
    port: int = DEFAULT_PORT,
    pdb_dir: Optional[str] = None,
) -> None:
    protspace = ProtSpace(json, pdb_dir)
    protspace.run_server(debug=True, port=port, quiet=False)


if __name__ == "__main__":
    args = parse_arguments()
    main(**vars(args))
