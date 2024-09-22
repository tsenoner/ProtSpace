from protspace.app import ProtSpace

# Initialize ProtSpace with the homo sapiens example JSON file
# protspace = ProtSpace("data/h_sapiens/h_sapiens_rbgaColored.json")
protspace = ProtSpace("data/3FTx/3FTx_customized.json")

# Create the Dash app
app = protspace.create_app()

# Expose the Flask server for Gunicorn
server = app.server
