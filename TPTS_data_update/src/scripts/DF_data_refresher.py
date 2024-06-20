from src.config import *
from ftplib import FTP
import pandas as pd
import warnings

warnings.filterwarnings('ignore')


def get_file_from_ftp(file_save_path, file_name):
    try:
        ftp = FTP('10.200.254.54')
        ftp.connect(port=2121)
        ftp.login(user='Truong', passwd='DF@@75224')
        ftp.cwd('/Truong/outbound')
        print("Successfully connected to FTP server and redirect to Outbound Folder")
    except Exception as e:
        print("Cannot connect to FTP server")
    with open(file_save_path, 'wb') as f:
        ftp.retrbinary('RETR ' + file_name, f.write)
    ftp.close()


def refresh_DF_data():
    filename = {ONOFF_DATA_FILE: 'TRAICAY_ONOFF.csv',
                ITEM_DATA_FILE: 'TRAICAY_ITEM.csv',
                DEAL_DATA_FILE: 'TRAICAY_KM.csv'}

    for file_to_download in filename:
        get_file_from_ftp(file_to_download, filename[file_to_download])
        print(f"Sucessfully download: {filename[file_to_download]}")

    print("\nCleaning format for the next step of Processing\n")
    onoff_new_col = ['*Item', '*Source', '*Dest', '*Sourcing', 'Disc', 'ShipCal', 'TransMode', 'ONOFF',
                     'UDC_TPTS_LOCK', 'UDC_NOTE_DISC']
    onoff_data = pd.read_csv(ONOFF_DATA_FILE, encoding='iso-8859-1')
    for i, col in enumerate(onoff_new_col):
        onoff_data.rename(columns={onoff_data.columns[i]: col}, inplace=True)
    onoff_data.to_csv(ONOFF_DATA_FILE, index=False)

    item_new_col = ['*Item', 'Descr', 'UDC_SEQ_ITEM', 'UDC_ARTT2', 'UnitPrice', 'UDC_Artt1', 'UDC_GOLIVE']
    item_data = pd.read_csv(ITEM_DATA_FILE)
    for i, col in enumerate(item_new_col):
        item_data.rename(columns={item_data.columns[i]: col}, inplace=True)
    item_data.to_csv(ITEM_DATA_FILE, index=False)

    deal_new_col = ['*DEAL', '*SOURCE', '*DEST', '*ITEM', '*EFF', '*DISC', 'NOTE_KM']
    deal_data = pd.read_csv(DEAL_DATA_FILE, encoding='iso-8859-1')
    for i, col in enumerate(deal_new_col):
        deal_data.rename(columns={deal_data.columns[i]: col}, inplace=True)
    deal_data.to_csv(DEAL_DATA_FILE, index=False)
    print("Done cleaning format! Input files are now ready for processing!\n\n")
