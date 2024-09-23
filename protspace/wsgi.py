from protspace.app import ProtSpace

# Initialize ProtSpace with default JSON data
protspace = ProtSpace(
    # pdb_dir="data/3FTx/pdb",
    default_json_file="data/3FTx/3FTx_customized.json"
)

# Create the Dash app
app = protspace.create_app()

# Expose the Flask server for Gunicorn
server = app.server