"""
python script/prepare_json.py --hdf data/3FTx/3FTx_prott5.h5 --csv data/3FTx/3FTx.csv --methods pca2 pca3 umap2 umap3 tsne2 tsne3 -o data/3FTx/3FTx.json --n_neighbors 25 --min_dist 0.5 --learning_rate 1000 -v
"""
import subprocess

def run_prepare_json_script():
    command = [
        "poetry", "run", "python", "script/prepare_json.py",
        "--hdf", "data/3FTx/3FTx_prott5.h5",
        "--csv", "data/3FTx/3FTx.csv",
        "--methods", "pca2", "pca3", "umap2", "umap3", "tsne2", "tsne3",
        "-o", "data/3FTx/3FTx.json",
        "--n_neighbors", "25",
        "--min_dist", "0.5",
        "--learning_rate", "1000",
        "-v"
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        print("Script executed successfully!")
        print(result.stdout)
    else:
        print("Script execution failed!")
        print(result.stderr)

if __name__ == "__main__":
    run_prepare_json_script()
