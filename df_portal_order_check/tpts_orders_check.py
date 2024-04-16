# Import 
import pandas as pd, numpy as np
import time, shutil, os, glob, xlwings as xw, argparse
from pathlib import Path
from datetime import date, timedelta
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options


# Define arguments
parser = argparse.ArgumentParser()
parser.add_argument('--check_date', type=str, default='', help='Order\'s date to check, format= dd_mm_yy')
parser.add_argument('--order_store', action='store_true', help='True to export list of store with order on checking date')
parser.add_argument('--no_order_store',action='store_true', help='True to export list of store without order on checking date')
parser.add_argument('--store_list', nargs='+', type=int, help='List of store to check order list on checking date' )
args = parser.parse_args()

# Function to download report files from Portal
def download_report(login_page,
                    report_page,
                    xls_filename,
                    download_dir,
                    dir_to_save):
    # Delete file in Download dir if exist a file with the same file name
    if os.path.isfile(os.path.join(download_dir, xls_filename)):
        os.remove(os.path.join(download_dir, xls_filename))
    
    # Config options for the browser
    options = Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")

    # Create browser session
    DRIVER = webdriver.Firefox(options=options)

    # Navigate to login_page and log in
    DRIVER.get(login_page)
    try:
        user_field = DRIVER.find_element(By.ID,"inputUserName")
        password_field = DRIVER.find_element(By.ID,"inputPassword")
    except NoSuchElementException:
        print('Failed to Login! Cannot locate user or password field')
        return
    user_field.send_keys('truong-vp')
    password_field.send_keys('DFp2023')
    password_field.send_keys(Keys.RETURN)   

    time.sleep(3)
    #  Navigate to report_page and download file
    DRIVER.get(report_page)

    time.sleep(5)
    try:
        download_button = DRIVER.find_element(By.ID,"dataTable3_wrapper")\
                                .find_element(By.CLASS_NAME,"dt-buttons")\
                                .find_element(By.ID,'btnExportFFS')
    except NoSuchElementException:
        print('Fail to download report! Cannot locate download button!')
        DRIVER.quit()
        return
    download_button.click()
    while not os.path.exists(f"{download_dir}/{xls_filename}"):
        time.sleep(1)
    print('Downloaded successfully')
    try:
        downloaded_files = glob.glob(download_dir + '\\*')
        report_file = max(downloaded_files, key=os.path.getctime)
        file_name = report_file[24:]
        shutil.copy(report_file, os.path.join(dir_to_save,file_name))
    except:
        print('Failed to copy downloaded report to destination directory')
        DRIVER.quit()
        return
    print('Successfully download and save report files to destination directory')
    DRIVER.quit()
    return

# Read xls file then convert it into xlsx file
def convert_xls(input_path, output_path):
    try:
        try:
            app = xw.App(visible=False)
            wb = app.books.open(input_path)
        except:
            print('Cannot open file')
        # Save the file as xlsx
        wb.save(output_path)

        # Close the workbook and quit Excel
        wb.close()
        app.quit()
        return True
    except:
        return False
    
# Rewrite the header
""""
This function is used to transfrom the original dataframe with 
inapproriate columns name and structure.

Input: raw df read from excel files. See excel files to explore the structure
Output: df with columns that has been renamed, and

"""
def clean_df(df):
    col_rename = df.loc[0].to_list()[:8]
    for i, col in enumerate(df.columns):
        if i == 8:
            break
        df.rename(columns={col: col_rename[i]},inplace=True)
    df = df.drop(index=0)
    df_melt = pd.melt(df, id_vars=df.columns[0:8], value_vars=df.columns[8:],
                  var_name = 'Store', value_name='Order_Qty')
    return df_melt

# Function to get order list of an input store
def order_list(store,df):
    return df[(df['Store'] == store) & \
              (~df['Order_Qty'].isna())]

# Số SKU mỗi store đặt
def store_group(df):
    nSKU_by_Store = df.groupby(by='Store')['Order_Qty'].count().sort_values(ascending=False).reset_index()
    stores_ordered_today = nSKU_by_Store[nSKU_by_Store['Order_Qty']>0].rename(columns={'Order_Qty': 'Số lượng SKU đã đặt'})
    stores_has_no_order = nSKU_by_Store[nSKU_by_Store['Order_Qty']==0].rename(columns={'Order_Qty': 'Số lượng SKU đã đặt'})
    return stores_ordered_today, stores_has_no_order

# Function of exporting a df to csv file
def export_df(df, filename):
    # today = datetime.now().strftime(format='%d-%m')
    df.to_excel('output_files/' + filename + '.xlsx', index=False)

# Function to get date with apporiate format
def get_date(check_date, ):
    if check_date == '':
        # If no specific date is provided, use tomorrow's date for file naming
        date_string = (date.today() + timedelta(1)).strftime(format='%d_%m_%Y')
        print("Default Date: Tomorrow - Created")
    else:
        # Use the provided date for file naming
        date_string = check_date
        print(f'Used input date: {check_date}')
    return date_string

def main(check_date='', 
         order_store=False, 
         no_order_store=False, 
         store_list=[]):
    """
    This is the main fucntion of the script. 

    It includes following tasks:
        - Get list of stores with order on a specific date.
        - Get list of stores without order on a specific date.
        - Get list of ordered SKUs of a store or list of stores on a specific date.
    
    Parameters:
        - check_date (datetype): the checking date, format = dd_mm_yy. Default is today's date.
        - order_store (Boolean): If True, return list of store with order on checking date. 
        - no_order_store (Boolean): If True, return list of stores without order on checking date.
        - store_list: List of store to check ordered SKUs on checking date.

    Returns:
        - If order_store: Export an excel file to /output_files/date_store_with_order.xlsx
        - If no_order_store: Export an excel file to /output_files/date_no_store_with_order.xlsx
        - For each store in store_list: Export an excel file /output_files/date_store.xlsx
    """

    # Get date with approriate format
    date_string = get_date(check_date)

    # Specify the Excel file name with the determined date
    xls_filename = f'DFP_FreshFood_Order_{date_string}.xls'

    # Get the path to the downloaded XLS file
    xls_file_path = os.path.join(os.getcwd(), 'daily_xls', xls_filename)
    print(f'xls file path: {xls_file_path}')

    # Generate the path to the intended output with XLSX extension
    xlsx_file_path = xls_file_path.replace('xls', 'xlsx')
    print(f'xlsx file path: {xlsx_file_path}')

    # Check if xls file exist, and download if the check_date is blank, because Portal only save data of tomorrow's order.
    if check_date == '' and not (os.path.isfile(xls_file_path)):
        download_report(login_page = "https://sgcdfportal.southeastasia.cloudapp.azure.com/",
                        xls_filename = xls_filename,
                        download_dir = str(Path.home() / "Downloads"),
                        report_page = f"https://sgcdfportal.southeastasia.cloudapp.azure.com/order/freshfoods?category=che-bien-nau-chin&ordered_day={(date.today() + timedelta(1)).strftime(format='%d/%m/%y')}&transport_method=tat-ca",
                        dir_to_save = os.path.join(os.getcwd(), 'daily_xls'))


    # Convert .xls file to .xlsx file
    if not convert_xls(input_path=xls_file_path, output_path=xlsx_file_path):
        print(xlsx_file_path)
        print(xls_file_path)
        print('Fail to convert xls file')
        return
    
    # If .xls file has been successfully converted, clean and perform tasks
    else:
        print('Successfully convert xls file. Start analyzing now.')
        # Clean the DataFrame
        df = clean_df(pd.read_excel(xlsx_file_path))
        # Extract the date from the file path
        # Perform tasks based on provided options
        if order_store:
            try:
                # Group stores with and without orders
                store_with_orders, store_without_orders = store_group(df)
                # Export DataFrame of stores with orders
                export_df(store_with_orders, date_string + '_store_có_đặt')
                print('Successfuly perform task: order_store')
            except:
                print('Failed to perform task: order_store')
        if no_order_store:
            try:
                # Group stores with and without orders
                store_with_orders, store_without_orders = store_group(df)
                # Export DataFrame of stores without orders
                export_df(store_without_orders, date_string + '_store_không_đặt')
                print('Successfuly perform task: no_order_store')
            except:
                print('Failed to perform task: no_order_store')
        if store_list:  # Check if store_list is not empty
            # Loop over each store in the list
            for store in store_list:
                try:
                    # Extract orders for the current store
                    order_by_store = order_list(store, df)
                    # Export DataFrame of orders for the current store
                    export_df(order_by_store, date_string + '_' + str(store))
                    print(f"Successfully get order list of {store}")
                except:
                    print(f'Failed to get store list of {store}')

if __name__ == "__main__":
    main(check_date=args.check_date,
         order_store=args.order_store,
         no_order_store=args.no_order_store,
         store_list=args.store_list)