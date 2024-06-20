import pandas as pd


def get_update_packing(filepath, sourcing_filepath):
    """
    Bo sung sau
    """
    raw_data = pd.read_excel(filepath,
                             sheet_name='QUY CACH SKU',
                             skiprows=2)
    sourcing = pd.read_csv(sourcing_filepath, encoding = 'iso-8859-1')
    # Bỏ 3 cột không sử dụng: Tên sản phẩm, QC C.Mart, QC CF, và 1 dòng không sử dụng.
    clean_data = raw_data.drop(index=0,
                               columns=['Unnamed: 2', 'Unnamed: 3', 'STORE'])
    # Đổi tên 2 cột đầu tiên
    new_name_list = ['*Source', '*Item']
    for i, col in enumerate(raw_data.columns[:2]):
        clean_data = clean_data.rename(columns={col: new_name_list[i]})

    transformed_packing = clean_data.melt(id_vars=['*Source', '*Item'],
                                          value_vars=clean_data.columns[2:],
                                          var_name='*Dest',
                                          value_name='MajorShipQty')
    transformed_packing.dropna(inplace=True)
    transformed_packing = transformed_packing[transformed_packing['MajorShipQty'] != 0]
    transformed_packing['MinorShipQty'] = transformed_packing['MajorShipQty']

    merge = pd.merge(transformed_packing,sourcing, on=['*Source', '*Item','*Dest'], how='left')
    merge.drop(columns=['MajorShipQty_x', 'MinorShipQty_x'], inplace=True)
    merge.rename(columns={'MajorShipQty_y': 'MajorShipQty', 'MinorShipQty_y': 'MinorShipQty'}, inplace=True)
    return merge[sourcing.columns]