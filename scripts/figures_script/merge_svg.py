from pathlib import Path
import matplotlib.pyplot as plt
import cairosvg
import io

def svg_to_png(svg_path):
    png_data = cairosvg.svg2png(url=str(svg_path))
    return io.BytesIO(png_data)

# Function to create a subplot with an image, a label, and a header
def add_image_to_plot(ax, image_path, label):
    png_data = svg_to_png(image_path)
    img = plt.imread(png_data)
    ax.imshow(img)
    ax.axis("off")

    # Add label to top-left corner
    ax.text(0.05, 1.125, label, transform=ax.transAxes,
            fontsize=16, fontweight='bold', va='top', ha='left',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

    # Add header (file name without extension)
    header = image_path.stem
    ax.set_title(header, fontsize=14, fontweight='bold', pad=20)

# Create the figure and subplots
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(2, 4)

# Add images to subplots
base_path = Path("examples/out/h_sapiens")
add_image_to_plot(fig.add_subplot(gs[0, 0:2]), base_path / "ProtTucker.svg", "A")
add_image_to_plot(fig.add_subplot(gs[0, 2:]), base_path / "CLEAN.svg", "B")
add_image_to_plot(fig.add_subplot(gs[1, 1:3]), base_path / "LightAttention.svg", "C")

# Adjust the layout and save the figure
plt.tight_layout()
plt.savefig(base_path / "Merge.png", dpi=300, bbox_inches="tight")
plt.show()