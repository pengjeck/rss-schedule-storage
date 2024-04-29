import logging
import gspread
from gspread import Spreadsheet, spreadsheet
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

GS_SERVICE_ACCOUNT_FILE = "gs_service_account.json"

logging.info("begin to connect google spread sheet")
index_ss_url = "https://docs.google.com/spreadsheets/d/1JmoHh9nAdJRz_F9jnNDpydUk2NYSkw739Oahf0-270M"
gs_client = gspread.service_account(GS_SERVICE_ACCOUNT_FILE)
index_ss = gs_client.open_by_url(index_ss_url)

values = index_ss.sheet1.get_all_values()
for item in values:
    logging.info(f"begin to export ss={item}")
    ss = gs_client.open_by_url(item[1])

    data = ss.export(spreadsheet.ExportFormat.EXCEL)
    filename = "rss_" + item[0] + ".xlsx"
    with open(filename, 'wb') as f:
        f.write(data)
    logging.info(f"success export {item} to file={filename}")
