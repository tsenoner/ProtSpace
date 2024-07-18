import numpy as np
import pandas as pd

from .data_loader import JsonReader


def prepare_dataframe(reader: JsonReader, selected_projection: str, selected_feature: str) -> pd.DataFrame:
    projection_data = reader.get_projection_data(selected_projection)
    df = pd.DataFrame(projection_data)
    df["x"] = df["coordinates"].apply(lambda x: x["x"])
    df["y"] = df["coordinates"].apply(lambda x: x["y"])
    if reader.get_projection_info(selected_projection)["dimensions"] == 3:
        df["z"] = df["coordinates"].apply(lambda x: x["z"])

    df[selected_feature] = df["identifier"].apply(
        lambda x: reader.get_protein_features(x).get(selected_feature)
    )
    df[selected_feature] = df[selected_feature].replace({np.nan: "<NaN>", None: "<NaN>"})

    if df[selected_feature].dtype in ["float64", "int64"]:
        df[selected_feature] = df[selected_feature].astype(str)

    return df