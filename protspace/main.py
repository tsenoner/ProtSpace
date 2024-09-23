import argparse
from typing import Optional

from .app import ProtSpace
from .utils import DEFAULT_PORT


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ProtSpace")
    parser.add_argument(
        "--json",
        required=False,
        help="Path to the default JSON file",
    )
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
    port: int = DEFAULT_PORT,
    pdb_dir: Optional[str] = None,
    json: Optional[str] = None,
) -> None:
    protspace = ProtSpace(pdb_dir=pdb_dir, default_json_file=json)
    protspace.run_server(debug=True, port=port)


if __name__ == "__main__":
    args = parse_arguments()
    main(**vars(args))
