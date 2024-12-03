import os
from plotly.validators.scatter.marker import SymbolValidator

# https://plotly.com/python/marker-style/
def extract_marker_strings(input_list):
    # Filter out integers and string representations of numbers
    return [item for item in input_list if isinstance(item, str) and not item.isdigit()]

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
NAN_COLOR = "rgba(200, 200, 200, 0.4)"
HIGHLIGHT_COLOR = "rgba(255, 255, 0, 0.7)"
HIGHLIGHT_BORDER_COLOR = "red"

# Marker shapes
MARKER_SHAPES = [
    'circle', 'circle-open', 'cross', 'diamond',
    'diamond-open', 'square', 'square-open', 'x'
]

MARKER_SHAPES_2D = sorted(extract_marker_strings(SymbolValidator().values))