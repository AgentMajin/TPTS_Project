import pandas as pd
import numpy as np
import os
from src.config import LOC_DATA_FILE, ITEM_DATA_FILE, OUTPUT_DIR


def check_item(df, item_col):
    """Bo sung sau"""
    item_to_check = df[item_col].unique()
    item_df = pd.read_csv(ITEM_DATA_FILE, encoding='iso-8859-1')
    item_list = item_df['*Item'].unique()
    new_items = np.setdiff1d(item_to_check, item_list, assume_unique=True)
    if len(new_items) > 0:
        return (df[df[item_col].isin(item_list)],
                df[~df[item_col].isin(item_list)])
    else:
        return df, None


def check_loc(df, loc_col):
    """Bo sung sau"""
    loc_to_check = df[loc_col].unique().astype('str')
    loc_df = pd.read_csv(LOC_DATA_FILE, encoding='iso-8859-1')
    loc_list = loc_df['*Loc'].unique()
    new_loc = np.setdiff1d(loc_to_check, loc_list, assume_unique=True)
    if len(new_loc) > 0:
        return (df[df[loc_col].astype('str').isin(loc_list)],
                df[~df[loc_col].astype('str').isin(loc_list)])
    else:
        return df, None


def classify_df(df, item_col, loc_col):
    if item_col is not None:
        df_valid_item, df_invalid_item = check_item(df, item_col)
    else:
        df_valid_item = df
        df_invalid_item = None

    if loc_col is not None:
        df_valid_final, df_invalid_loc = check_loc(df_valid_item, loc_col)
    else:
        df_valid_final = df_valid_item
        df_invalid_loc = None
    return df_valid_final, df_invalid_loc, df_invalid_item


def export_df(export_name, valid_df, invalid_loc_df=None, invalid_item_df=None):
    if len(valid_df) > 0:
        valid_df.to_csv(os.path.join(OUTPUT_DIR, export_name + '_valid.csv'), index=False)
        print(f"Successfully exported valid {export_name}, total rows: {len(valid_df)}")

    if invalid_item_df is not None:
        invalid_item_df.to_csv(os.path.join(OUTPUT_DIR, export_name + '_invalid_item.csv'), index=False)
        print(f"Successfully exported invalid item of {export_name}, total rows: {len(invalid_item_df)}")

    if invalid_loc_df is not None:
        invalid_loc_df.to_csv(os.path.join(OUTPUT_DIR, export_name + '_invalid_loc.csv'), index=False)
        print(f"Successfully exported invalid location of {export_name}, total rows: {len(invalid_loc_df)}")

    return None
