import os

# App settings
DEFAULT_PORT = 8050

# Output settings
IMAGE_OUTPUT_DIR = os.getenv('PROTSPACE_IMAGE_OUTPUT_DIR', 'out/images')

# Plotting settings
DEFAULT_MARKER_SIZE = 10
HIGHLIGHT_MARKER_SIZE = 20
DEFAULT_LINE_WIDTH = 0.5
HIGHLIGHT_LINE_WIDTH = 3

# Color settings
NAN_COLOR = "lightgrey"
HIGHLIGHT_COLOR = "rgba(255, 255, 0, 0.7)"
HIGHLIGHT_BORDER_COLOR = "red"