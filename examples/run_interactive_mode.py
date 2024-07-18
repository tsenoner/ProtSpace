from protspace import ProtSpace


def main():
    # Path to the JSON file
    json_file = "data/3FTx/3FTx.json"

    # Path to the pdb files
    pdb_dir = "data/3FTx/pdb"

    # Initialize the ProtSpaceApp (both with or without PDB files)
    #protspace = ProtSpace(json_file)
    protspace = ProtSpace(json_file, pdb_dir)

    # Run the interactive Dash server
    protspace.run_server(port=8050)


if __name__ == "__main__":
    main()
