import sys

import pandas as pd
import numpy as np
from src.config import *
from . import update_onoff
from .update_onoff import *
from .DF_data_refresher import *
from .exporter import *


def validate_onoff(onoff_data: str):
    """
    Function to validate D&F ONOFF data, including 2 option:
    - Validate Production ONOFF data
    - Validate ONOFF data after an update
    Input:

    """
    # Check argument
    if not isinstance(onoff_data, str):
        raise TypeError('ONOFF data type must be a string')
    if onoff_data not in ('production', 'update'):
        raise ValueError('ONOFF data must be either \"production\" or \"update\"')

    # If onoff data to validate is production, simply read onoff data file and check for invalid rows
    if onoff_data == 'production':
        try:
            onoff_df = pd.read_csv(ONOFF_DATA_FILE, encoding='iso-8859-1')
            if len(onoff_df[onoff_df['ONOFF'] != onoff_df['UDC_TPTS_LOCK']]) > 0:
                sys.exit('Exist invalid ONOFF data')
        except Exception as e:
            print(f"Failed to get Production ONOFF data from FTP, Error: {e}")

    # If onoff data to validate is after an update, first get the update, then eliminate invalid loc, item.
    # Finally merge with
    elif onoff_data == 'update':
        exist_wrong_onoff, update_data = get_onoff_update(read_onoff_input(UPDATE_INPUT_FILE))
        if exist_wrong_onoff:
            sys.exit('Exist invalid ONOFF data')
        valid_update, invalid_loc, invalid_item = classify_df(update_data, '*Item', '*Loc')
        production_onoff = pd.read(ONOFF_DATA_FILE, encoding='iso-8859-1')

        col_to_use = ['*Item', '*Source', '*Dest', 'ONOFF']

        merge_onoff = pd.merge(production_onoff[col_to_use], valid_update[col_to_use], how='left',
                               on=['*Item', '*Source', '*Dest'])
        merge_onoff['ONOFF'] = merge_onoff.apply(lambda row:
                                                 row['ONOFF_y']
                                                 if row['ONOFF_y'] != row['ONOFF_x']
                                                 else row['ONOFF_x'], axis=1)
        onoff_df = merge_onoff[col_to_use]

    raw_input = read_onoff_input(UPDATE_INPUT_FILE)
    for store in raw_input['*Dest']:
        


