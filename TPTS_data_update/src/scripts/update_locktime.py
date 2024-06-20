import pandas as pd
import numpy as np
import sys


def wrangle_locktime_input(filepath):
    """
    Hàm đọc và tiền xử lý thông tin giờ khóa đơn hàng, chuyển đổi giờ khóa đơn hàng từ dạng ma trận thành dạng records

    Input: filepath của file excel update data theo form mẫu
    Output: dataframe theo dạng bảng với primary key = Store + THU, attributes columns là: thứ: THU, giờ lock: GIOLOCK
    """
    # Load data vào dataframe
    try:
        locktime_raw = pd.read_excel(filepath, sheet_name='TIME STORE', skiprows=1)
    except Exception:
        sys.exit("Cant read raw file")

    headers = ['Store_Name', 'Store', 'Tuesday', 'Tuesday.1',
               'Wednesday', 'Wednesday.1', 'Thursday', 'Thursday.1',
               'Friday', 'Friday.1', 'Saturday', 'Saturday.1',
               'Sunday', 'Sunday.1', 'Monday', 'Monday.1']
    try:
        for i, col in enumerate(locktime_raw.columns):
            locktime_raw.rename(columns={col: headers[i]}, inplace=True)
    except Exception:
        sys.exit("Cannot rename raw dataframe")

    # Bỏ cột Store_Name
    locktime_raw.drop(columns='Store_Name', inplace=True)

    # Kiểm tra missing values
    if locktime_raw.isna().sum().sum() > 0:
        sys.exit("Exist Missing Values!")

    # Tách df locktime thành df_lockday: chứa ngày khóa đơn hàng, và df_hour: giờ khóa đơn hàng
    df_lockday = locktime_raw.drop(columns=locktime_raw.columns[1::2])
    df_lockhour = locktime_raw.drop(columns=locktime_raw.columns[2::2])

    # Đổi lại tên df_lockhour (Monday.1 -> Monday, Tuesday.1 -> Tuesday,...)
    for col in df_lockday.columns[1:]:
        df_lockday = df_lockday.rename(columns={col: col[:-2]})

    try:
        df_lockday_melt = df_lockday.melt(id_vars=['Store'],
                                          value_vars=df_lockday.columns[1:],
                                          var_name='THU',
                                          value_name='NGAYDONHANG')
        df_lockhour_melt = df_lockhour.melt(id_vars=['Store'],
                                            value_vars=df_lockhour.columns[1:],
                                            var_name='THU',
                                            value_name='GIOLOCK')
    except Exception:
        sys.exit("Cannot melt dataframe")

    # Merge df_locktime và df_lockhour thành 1 df duy nhất
    locktime_merge = pd.merge(df_lockhour_melt,
                              df_lockday_melt,
                              on=['Store', 'THU'],
                              how='left')
    return locktime_merge


def get_update_locktime(locktime_df, transmode):
    """
    Hàm chỉnh sửa format dataframe đã transform khớp với format D&F

    Input: Dataframe đã transform, gồm:
    - primary key: Store + THU
    - attribute columns: GIOLOCK, NGAYDONHANG

    Output: Dataframe với format chuẩn theo yêu cầu D&F, có bổ sung Transmode phù hợp với nhóm hàng
    """
    # Đổi tên cột Store thành *Dest
    locktime_df.rename(columns={'Store': '*DEST'}, inplace=True)

    # Thêm cột transmode
    locktime_df['*TRANSMODE'] = transmode

    # Xóa các ký tự AM, PM khỏi cột GIOLOCK
    locktime_df['GIOLOCK'] = locktime_df['GIOLOCK'] \
        .astype('str') \
        .str.replace(' PM', '') \
        .str.replace(' AM', '') \
        .apply(lambda x: x[:-3])
    # Loại bỏ ký tự 'D' khỏi NGAYDONHANG
    locktime_df['NGAYDONHANG'] = locktime_df['NGAYDONHANG'].apply(lambda x: x[:-1])
    # Chuyển weekday sang dạng số
    dayofweek_dict = {'Monday': '1', 'Tuesday': '2',
                      'Wednesday': '3', 'Thursday': '4',
                      'Friday': '5', 'Saturday': '6', 'Sunday': '7'}
    for weekday_string, weekday_int in dayofweek_dict.items():
        locktime_df['THU'] = locktime_df['THU'].astype('str') \
            .str.replace(weekday_string, weekday_int)

    # Sort lại theo Dest
    locktime_df = locktime_df.sort_values(by='*DEST', ascending=True)

    return locktime_df[['*TRANSMODE', '*DEST', 'THU', 'GIOLOCK', 'NGAYDONHANG']]