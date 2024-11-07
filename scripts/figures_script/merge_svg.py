from pathlib import Path
import matplotlib.pyplot as plt
import cairosvg
import io
import math
from typing import List, Optional, Tuple, Union, Dict
import yaml
import json

class ImageConfig:
    """Class to handle image configuration and validation."""
    def __init__(self, path: Union[str, Path], subtitle: Optional[str] = None):
        self.path = Path(path)
        self.subtitle = subtitle if subtitle else self.path.stem

        if not self.path.exists():
            raise FileNotFoundError(f"Image file not found: {self.path}")
        if not self.path.suffix.lower() == '.svg':
            raise ValueError(f"File must be SVG format: {self.path}")

def svg_to_png(svg_path: Union[str, Path]) -> io.BytesIO:
    """Convert SVG file to PNG data in memory."""
    png_data = cairosvg.svg2png(url=str(svg_path))
    return io.BytesIO(png_data)

def add_image_to_plot(
    ax: plt.Axes,
    image_config: ImageConfig,
    label: str,
    label_fontsize: int = 16,
    subtitle_fontsize: int = 14
) -> None:
    """Add an image to a subplot with a label and subtitle."""
    png_data = svg_to_png(image_config.path)
    img = plt.imread(png_data)
    ax.imshow(img)
    ax.axis("off")

    # Add label to top-left corner
    ax.text(0.05, 1.125, label, transform=ax.transAxes,
            fontsize=label_fontsize, fontweight='bold', va='top', ha='left',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

    # Add subtitle
    ax.set_title(image_config.subtitle, fontsize=subtitle_fontsize,
                fontweight='bold', pad=20)

def create_image_grid(
    config_file: Union[str, Path],
    output_path: Optional[Path] = None,
    fig_width: int = 16,
    min_height_per_row: int = 6,
    dpi: int = 300
) -> None:
    """
    Create a grid of SVG images based on a configuration file.

    Args:
        config_file: Path to YAML or JSON configuration file
        output_path: Path to save the output PNG
        fig_width: Width of the figure in inches
        min_height_per_row: Minimum height per row in inches
        dpi: DPI for the output image
    """
    # Load configuration
    config_path = Path(config_file)
    if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
        with open(config_path) as f:
            config = yaml.safe_load(f)
    elif config_path.suffix.lower() == '.json':
        with open(config_path) as f:
            config = json.load(f)
    else:
        raise ValueError("Configuration file must be YAML or JSON")

    # Convert configuration to ImageConfig objects
    image_configs = []
    for img in config['images']:
        if isinstance(img, dict):
            image_configs.append(ImageConfig(
                path=Path(config['base_path']) / img['path'],
                subtitle=img.get('subtitle')
            ))
        else:
            image_configs.append(ImageConfig(
                path=Path(config['base_path']) / img
            ))

    num_images = len(image_configs)
    num_rows = math.ceil(num_images / 2)  # Two columns
    fig_height = num_rows * min_height_per_row

    # Create figure and gridspec
    fig = plt.figure(figsize=(fig_width, fig_height))
    gs = fig.add_gridspec(num_rows, 2)

    # Generate labels (A, B, C, ...)
    labels = [chr(65 + i) for i in range(num_images)]

    # Add images to subplots
    for idx, (img_config, label) in enumerate(zip(image_configs, labels)):
        row = idx // 2
        col = idx % 2
        ax = fig.add_subplot(gs[row, col])
        add_image_to_plot(ax, img_config, label)

    # Adjust the layout
    plt.tight_layout()

    # Save the figure if output path is provided
    if output_path:
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
        plt.close()
    else:
        plt.show()

def main():
    """Example usage of the script."""

    # Use the configuration to create the grid
    create_image_grid(
        config_file='scripts/figures_script/imag_config.yaml',
        output_path=Path('examples/out/final/merged_grid.png'),
        fig_width=16,
        min_height_per_row=6,
        dpi=300
    )

if __name__ == "__main__":
    main()