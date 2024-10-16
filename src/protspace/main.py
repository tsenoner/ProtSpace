import argparse
import warnings
from typing import Optional

from .app import ProtSpace
from .config import DEFAULT_PORT

warnings.filterwarnings("ignore", category=SyntaxWarning)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ProtSpace")
    parser.add_argument(
        "--json",
        required=False,
        help="Path to the default JSON file",
    )
    parser.add_argument(
        "--pdb_zip",
        required=False,
        help="Path to the ZIP file containing PDB files",
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
    pdb_zip: Optional[str] = None,
    json: Optional[str] = None,
) -> None:
    protspace = ProtSpace(pdb_zip=pdb_zip, default_json_file=json)
    protspace.run_server(debug=True, port=port)


def run():
    args = parse_arguments()
    main(**vars(args))


if __name__ == "__main__":
    run()
