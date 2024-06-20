from src.config import ITEM_DATA_FILE
import pandas as pd


def get_SKU_update(filepath, nhom_hang):

    print("Start getting SKU update")
    item_df = pd.read_csv(ITEM_DATA_FILE, encoding='iso-8859-1',
                          dtype={'UDC_ARTT1': object,
                                 'UDC_ARTT2': object})
    item_df = item_df[item_df['UDC_ARTT2'] == nhom_hang]
    item_df['UnitPrice'] = item_df['UnitPrice'].astype('str').str.replace(',', '').astype('float64')
    item_df['*Item'] = item_df['*Item'].astype('int64')

    input_sku_update = pd.read_excel(filepath, sheet_name='GIA VON SKU').iloc[:, 3:7]
    clean_input = input_sku_update.rename(columns={input_sku_update.columns[0]: '*Item',
                                                   input_sku_update.columns[1]: 'Descr',
                                                   input_sku_update.columns[2]: 'UDC_SEQ_ITEM',
                                                   input_sku_update.columns[3]: 'UnitPrice'})
    clean_input['UnitPrice'] = clean_input['UnitPrice'].astype('str').str.replace(',', '').astype('float64')

    if (clean_input.isna().sum()[0] == 0) or (clean_input['UnitPrice'].dtype.isin(['float64', 'int64'])):
        # sys.exit(clean_data['UnitPrice'].dtype)
        pass

    item_update = pd.merge(clean_input, item_df, on='*Item', how='left')
    item_update['Descr'] = item_update.apply(lambda x: x['Descr_y'] if x['Descr_y'] != '' else x['Descr_x'], axis=1)
    item_update.drop(columns=['Descr_x', 'Descr_y'], inplace=True)
    item_update = item_update[(item_update['UDC_SEQ_ITEM_x'] != item_update['UDC_SEQ_ITEM_y']) |
                              (item_update['UnitPrice_x'] - item_update['UnitPrice_y'] != 0)]

    item_update = item_update.drop(columns=['UDC_SEQ_ITEM_y', 'UnitPrice_y']).rename(
        columns={'UDC_SEQ_ITEM_x': 'UDC_SEQ_ITEM', 'UnitPrice_x': 'UnitPrice'})

    print("End of getting SKU update")
    return item_update[item_df.columns]