import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_workbook():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open(config.SHEET_NAME)

def init_sheet():
    wb = get_workbook()
    sheet1 = wb.sheet1
    sheet1.update_title("Pengeluaran")
    if sheet1.row_values(1) == []:
        sheet1.append_row(config.COLUMNS)
    existing = [s.title for s in wb.worksheets()]
    if "Pemasukan" not in existing:
        sheet2 = wb.add_worksheet(title="Pemasukan", rows=1000, cols=4)
        sheet2.append_row(config.COLUMNS)

def get_sheet_pengeluaran():
    return get_workbook().worksheet("Pengeluaran")

def get_sheet_pemasukan():
    return get_workbook().worksheet("Pemasukan")

def add_pengeluaran(tanggal, kategori, nominal, catatan):
    get_sheet_pengeluaran().append_row([tanggal, kategori, nominal, catatan])

def add_pemasukan(tanggal, kategori, nominal, catatan):
    get_sheet_pemasukan().append_row([tanggal, kategori, nominal, catatan])

def get_all_pengeluaran():
    return get_sheet_pengeluaran().get_all_records()

def get_all_pemasukan():
    return get_sheet_pemasukan().get_all_records()

def delete_row_pengeluaran(row_index):
    get_sheet_pengeluaran().delete_rows(row_index + 2)

def delete_row_pemasukan(row_index):
    get_sheet_pemasukan().delete_rows(row_index + 2)