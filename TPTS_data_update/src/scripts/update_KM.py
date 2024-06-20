import pandas as pd
import numpy as np
import sys
from datetime import datetime
from src.config import DEAL_DATA_FILE


def read_KM_input(filepath):
    """
    Bo sung sau
    """

    print("Start reading KM data")
    raw_data = pd.read_excel(filepath, sheet_name='Nội dung KM', skiprows=2)

    # Drop dòng chứa tên Store (index=0), và cột Store chứa tên sản phẩm
    clean_data = raw_data.drop(index=0, columns=['STORE'])

    # Đổi tên 2 cột đầu tiên
    new_name_list = ['*SOURCE', '*ITEM']
    for i, col in enumerate(raw_data.columns[:2]):
        clean_data = clean_data.rename(columns={col: new_name_list[i]})

    # Melt bảng dữ liệu ma trận
    KM_melt = clean_data.melt(id_vars=['*SOURCE', '*ITEM'],
                              value_vars=clean_data.columns[2:],
                              var_name='*DEST',
                              value_name='*DEAL')

    KM_melt.dropna(inplace=True)

    KM_date = pd.read_excel(filepath, sheet_name='Ngày KM')
    if KM_date.isna().sum()['CTKM'] > 0:
        sys.exit("Exist Duplicated!")

    KM_with_date = pd.merge(KM_melt,
                            KM_date.rename(columns={'CTKM': '*DEAL'}),
                            how='left',
                            on='*DEAL')

    KM_with_date.rename(columns={'Start date': '*EFF',
                                 'End date': '*DISC'}, inplace=True)

    KM_with_date['*EFF'] = pd.to_datetime(KM_with_date['*EFF'], format="%d/%m/%Y")
    KM_with_date['*DISC'] = pd.to_datetime(KM_with_date['*DISC'], format="%d/%m/%Y")
    KM_update = KM_with_date[KM_with_date['*DISC'] >= datetime.today()]

    # Transform date format into mm/dd/yyyy
    KM_update['*EFF'] = KM_update['*EFF'].dt.strftime("%m/%d/%Y")
    KM_update['*DISC'] = KM_update['*DISC'].dt.strftime("%m/%d/%Y")
    KM_update['NOTE_KM'] = KM_update['*DEAL']

    output_col = ['*DEAL', '*SOURCE', '*DEST', '*ITEM', '*EFF', '*DISC', 'NOTE_KM']
    print("End of reading KM data")
    return KM_update[output_col]


def get_KM_update(KM_input_df):
    """
    Bo sung sau
    """

    print("Start extracting KM data to update")
    today = datetime.today()
    # Read DEAL data from D&F
    deal_data = pd.read_csv(DEAL_DATA_FILE, encoding='iso-8859-1')

    # Get only active DEAL data and SKU in Update Input
    deal_data['*DISC'] = pd.to_datetime(deal_data['*DISC'], format="%m/%d/%Y")
    deal_data = deal_data[(deal_data['*DISC'] >= datetime.today()) &
                          (deal_data['*ITEM'].isin(KM_input_df['*ITEM'].unique()))]
    deal_data['*DISC'] = deal_data['*DISC'].dt.strftime("%m/%d/%Y")
    print(f"Len of deal data: {len(deal_data)}")
    print(f"Len of input data: {len(KM_input_df)}")

    # Merge input data and DEAL data
    KM_merge = pd.merge(KM_input_df, deal_data, how='outer',
                        on=['*DEAL', '*SOURCE', '*DEST', '*ITEM'])

    # Filter only data with update or remove NOTE_KM
    KM_update = KM_merge[KM_merge['NOTE_KM_x'] != KM_merge['NOTE_KM_y']]
    print(f"KM to update: {len(KM_update)}")

    # Eff and Disc will be copy from update input, if null, copy from DF
    KM_update['*EFF'] = np.where(pd.isnull(KM_update['*EFF_x']), KM_update['*EFF_y'], KM_update['*EFF_x'])
    KM_update['*DISC'] = KM_update.apply(lambda row: today.strftime("%m/%d/%Y") if pd.isnull(row['*DISC_x']) else row['*DISC_x'],
                                         axis=1)
    KM_update['NOTE_KM'] = KM_update['*DEAL']

    # Rename to match the output format
    KM_update.drop(columns=['NOTE_KM_y', 'NOTE_KM_x', '*EFF_x', '*EFF_y', '*DISC_x', '*DISC_y'], inplace=True)
    # KM_update.rename(columns={'NOTE_KM_x': 'NOTE_KM'}, inplace=True)
    KM_update['*DEST'] = KM_update['*DEST'].astype('int64')

    print("End of getting KM data update")

    return KM_update[deal_data.columns]
