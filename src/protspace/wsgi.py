from dotenv import dotenv_values

from protspace.app import ProtSpace

config = dotenv_values(".env.example")

# Initialize ProtSpace with default JSON data and optional PDB ZIP
protspace = ProtSpace(
    # pdb_zip=config["PDB_ZIP_PATH"],
    default_json_file=config["DEFAULT_JSON_FILE_PATH"]
)

# Create the Dash app
app = protspace.create_app()

# Expose the Flask server for Gunicorn
server = app.server
