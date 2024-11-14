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
    subtitle_fontsize: int = 14,
    border_color: str = 'black',
    border_width: float = 2
) -> None:
    """Add an image to a subplot with a label, subtitle, and border."""
    png_data = svg_to_png(image_config.path)
    img = plt.imread(png_data)

    # Display image
    ax.imshow(img)
    ax.axis("on")  # Turn axis on to show border

    # Remove ticks but keep the border
    ax.set_xticks([])
    ax.set_yticks([])

    # Set border properties
    for spine in ax.spines.values():
        spine.set_color(border_color)
        spine.set_linewidth(border_width)

    # Create a text box for both label and subtitle
    text_box = f"{label}. {image_config.subtitle}"
    ax.set_title(text_box, fontsize=subtitle_fontsize,
                 fontweight='bold', pad=20, loc='left')


def create_image_grid(
    config_file: Union[str, Path],
    fig_width: int = 16,
    min_height_per_row: int = 6,
    dpi: int = 300,
    border_color: str = 'black',
    border_width: float = 2,
    h_spacing: float = 0.2,
    v_spacing: float = 0.3,
) -> None:
    """
    Create a grid of SVG images based on a configuration file.

    Args:
        config_file: Path to YAML or JSON configuration file
        fig_width: Width of the figure in inches
        min_height_per_row: Minimum height per row in inches
        num_columns: Number of columns in the grid
        dpi: DPI for the output image
        border_color: Color of the border around images
        border_width: Width of the border in points
        h_spacing: Horizontal spacing between plots (smaller = less whitespace)
        v_spacing: Vertical spacing between plots (smaller = less whitespace)
    """
    # Load configuration
    config_path = Path(config_file)
    if config_path.suffix.lower() in {'.yaml', '.yml'}:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    elif config_path.suffix.lower() == '.json':
        with open(config_path) as f:
            config = json.load(f)
    else:
        raise ValueError("Configuration file must be YAML or JSON")

    num_columns = config["num_columns"]

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
    num_rows = math.ceil(num_images / num_columns)
    fig_height = num_rows * min_height_per_row

    # Create figure and gridspec with specified spacing
    fig = plt.figure(figsize=(fig_width, fig_height))
    gs = fig.add_gridspec(num_rows, num_columns,
                         hspace=h_spacing,
                         wspace=v_spacing)

    # Generate labels (A, B, C, ...)
    labels = [chr(65 + i) for i in range(num_images)]

    # Add images to subplots
    for idx, (img_config, label) in enumerate(zip(image_configs, labels)):
        row = idx // num_columns
        col = idx % num_columns
        ax = fig.add_subplot(gs[row, col])
        add_image_to_plot(ax, img_config, label,
                         border_color=border_color,
                         border_width=border_width)

    # Remove empty subplots if number of images is not a multiple of num_columns
    if num_images < num_rows * num_columns:
        for idx in range(num_images, num_rows * num_columns):
            row = idx // num_columns
            col = idx % num_columns
            fig.delaxes(fig.add_subplot(gs[row, col]))

    # Adjust the layout with tighter spacing
    plt.tight_layout()

    # Save the figure if output path is provided
    if config['out_path']:
        plt.savefig(config['out_path'], dpi=dpi, bbox_inches="tight",
                   pad_inches=0.1)
        plt.close()
    else:
        plt.show()

def main():
    base_path = Path("scripts/figures_script")
    config_paths = [
        base_path / "imag_config.yaml",
        base_path / "imag_config1.yaml",
        base_path / "imag_config2.yaml",
    ]
    for config_file in config_paths:
        print(config_file)
        create_image_grid(
            config_file=config_file,
            fig_width=20,
            min_height_per_row=6,
            dpi=600,
            border_color='black',
            border_width=1,
            h_spacing=0.0,
            v_spacing=0.0
        )
    print(f"Plot created using config: {config_file}")

if __name__ == "__main__":
    main()