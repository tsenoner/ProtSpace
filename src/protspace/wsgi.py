from dotenv import load_dotenv
import os

from protspace.app import ProtSpace

load_dotenv(".env.example")

# Initialize ProtSpace with default JSON data and optional PDB ZIP
protspace = ProtSpace(
    pdb_zip=os.getenv("PDB_ZIP_PATH"),
    default_json_file=os.getenv("DEFAULT_JSON_FILE_PATH"),
)

# Create the Dash app
app = protspace.create_app()

# Expose the Flask server for Gunicorn
server = app.server
