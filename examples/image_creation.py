from protspace.app import ProtSpace
from pathlib import Path


def main():
    # Path to the JSON file
    json_file = "data/gfp/protspace/gfp_style.json"

    # Initialize the ProtSpaceApp
    protspace = ProtSpace(default_json_file=json_file)

    # Generate images for specific projections and features
    projections = [
        "prott5_umap2",
        "prott5_umap3",
        "seq_sim_umap2",
        "seq_sim_mds2",
        "struct_sim_umap2",
        "struct_sim_mds2",
    ]
    features = ["nr_mutations", "brightness_category"]

    for projection in projections:
        for feature in features:
            protspace.generate_plot(
                projection=projection,
                feature=feature,
                filename=Path("examples/out/gfp") / f"{projection}_{feature}",
                width=1600,
                height=1000,
            )
            print(f"Generated image for {projection} - {feature}")


if __name__ == "__main__":
    main()
