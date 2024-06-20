import pandas as pd
from datetime import date

from src.config import ONOFF_DATA_FILE


def read_onoff_input(filepath):
    """
    Bo sung sau
    """
    raw_data = pd.read_excel(filepath,
                             sheet_name='ON OFF SKU',
                             skiprows=2)
    # Bỏ 3 cột không sử dụng: Tên sản phẩm, QC C.Mart, QC CF, và 1 dòng không sử dụng.
    clean_data = raw_data.drop(index=0,
                               columns=['Unnamed: 2', 'Unnamed: 3', 'STORE'])
    # Đổi tên 2 cột đầu tiên
    new_name_list = ['*Source', '*Item']
    for i, col in enumerate(raw_data.columns[:2]):
        clean_data = clean_data.rename(columns={col: new_name_list[i]})

    onoff_update = clean_data.melt(id_vars=['*Source', '*Item'],
                                   value_vars=clean_data.columns[2:],
                                   var_name='*Dest',
                                   value_name='UDC_TPTS_LOCK')
    onoff_update['UDC_TPTS_LOCK'] = onoff_update['UDC_TPTS_LOCK'].map(lambda x:
                                                                      True if pd.isnull(x) else False)
    return onoff_update


def get_onoff_update(onoff_update):
    today = date.today().strftime('%m/%d/%y') + ' 12:00 AM'

    # Read current D&F onoff table:
    onoff_data = pd.read_csv(ONOFF_DATA_FILE, encoding='iso-8859-1')
    onoff_data_wrong = onoff_data[onoff_data['UDC_TPTS_LOCK'] != onoff_data['ONOFF']]

    if len(onoff_data_wrong) > 0:
        print("Exist onoff data with ONOFF not equal UDC_TPTS_LOCK")
        return 1, onoff_data_wrong
    print(f"Count of Production ONOFF record: {len(onoff_data)}")
    print(f"Count of Input ONOFF record: {len(onoff_update)}")
    # Merge onoff_update with current DF onoff table:
    onoff_merge = pd.merge(onoff_update, onoff_data,
                           on=['*Item', '*Source', '*Dest'],
                           how='left')

    # print(f"Count of records after merging Production ONOFF and Update ONOFF: {len(onoff_merge)}")
    # onoff_merge = onoff_merge[onoff_merge['UDC_TPTS_LOCK_y'] == onoff_merge['ONOFF']]

    onoff_update_merge = onoff_merge[onoff_merge['UDC_TPTS_LOCK_x'] != onoff_merge['ONOFF']]
    print(f"Count of ONOFF to update: {len(onoff_update_merge)}")

    # Replace UDC_TPTS_LOCK of current ONOFF table with new UDC_TPTS_LOCK
    onoff_update_merge = (onoff_update_merge.drop(columns='UDC_TPTS_LOCK_y'))
    onoff_update_merge.rename(columns={'UDC_TPTS_LOCK_x': 'UDC_TPTS_LOCK'}, inplace=True)

    # Update ONOFF and Disc
    onoff_update_merge['ONOFF'] = onoff_update_merge['UDC_TPTS_LOCK']
    onoff_update_merge.loc[onoff_update_merge['ONOFF'] == True, 'Disc'] = today
    onoff_update_merge.loc[onoff_update_merge['ONOFF'] == False, 'Disc'] = ''
    onoff_update_merge_with_sourcing = onoff_update_merge[~onoff_update_merge['*Sourcing'].isna()]
    onoff_update_merge_without_sourcing = onoff_update_merge[onoff_update_merge['*Sourcing'].isna()]
    print(f"Count of ONOFF-to-update with no sourcing data: ", f"{len(onoff_update_merge_without_sourcing)}")
    print(f"Count of ONOFF-to-update with sourcing data: {len(onoff_update_merge_with_sourcing)}")
    return (0, onoff_update_merge_with_sourcing[onoff_data.columns],
            onoff_update_merge_without_sourcing[onoff_data.columns])
