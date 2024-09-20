from protspace import ProtSpace


def main():
    # Path to the JSON file
    json_file = "data/3FTx/3FTx.json"

    # Initialize the ProtSpaceApp
    app = ProtSpace(json_file)

    # Generate images for specific projections and features
    projections = ["PCA2", "PCA3", "UMAP2", "UMAP3"]
    features = ["group", "major_group"]

    for projection in projections:
        for feature in features:
            app.generate_images(
                projection=projection,
                feature=feature,
                output_dir="examples/3FTx/out",
                width=1600,
                height=1000,
            )
            print(f"Generated image for {projection} - {feature}")


if __name__ == "__main__":
    main()
