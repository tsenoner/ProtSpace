from protspace.app import ProtSpace

# Initialize ProtSpace with default JSON data and optional PDB ZIP
protspace = ProtSpace(
    # pdb_zip="data/3FTx/3FTx_pdb.zip",
    # default_json_file="data/3FTx/3FTx_customized.json"
    pdb_zip="data/Pla2g2/Pla2g2_pdb.zip",
    default_json_file="data/Pla2g2/protspace_files/Pla2g2_noTransperancy.json"

)

# Create the Dash app
app = protspace.create_app()

# Expose the Flask server for Gunicorn
server = app.server
