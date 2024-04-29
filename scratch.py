import requests
import feedparser
import gspread
from gspread import spreadsheet

gs = gspread.service_account(filename="gs_service_account.json")
# ss = gs.create('new_sheet')
ss = gs.open_by_url(
    "https://docs.google.com/spreadsheets/d/1JmoHh9nAdJRz_F9jnNDpydUk2NYSkw739Oahf0-270M")
data = ss.sheet1.get_all_values()

print(data)
# data = ss.export(spreadsheet.ExportFormat.EXCEL)
# with open('out.xlsx', 'wb') as f:
# f.write(data)
# ws = ss.add_worksheet("1233", 1, 1)
# print(ws)
