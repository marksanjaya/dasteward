import streamlit as st
import pandas as pd
from datetime import date
import sheets
import config

st.set_page_config(page_title="DASTEWARD", page_icon="💰", layout="centered")

st.title("💰 DASTEWARD")
st.caption("Personal Finance Tracker")

sheets.init_sheet()

# --- AMBIL DATA (cache biar ga bolak-balik request) ---
@st.cache_data(ttl=30)
def load_data():
    data_keluar = sheets.get_all_pengeluaran()
    data_masuk = sheets.get_all_pemasukan()
    return data_keluar, data_masuk

data_pengeluaran, data_pemasukan = load_data()

df_keluar = pd.DataFrame(data_pengeluaran) if data_pengeluaran else pd.DataFrame(columns=config.COLUMNS)
df_masuk = pd.DataFrame(data_pemasukan) if data_pemasukan else pd.DataFrame(columns=config.COLUMNS)

if not df_keluar.empty:
    df_keluar["Nominal"] = pd.to_numeric(df_keluar["Nominal"])
if not df_masuk.empty:
    df_masuk["Nominal"] = pd.to_numeric(df_masuk["Nominal"])

total_masuk = df_masuk["Nominal"].sum() if not df_masuk.empty else 0
total_keluar = df_keluar["Nominal"].sum() if not df_keluar.empty else 0
balance = total_masuk - total_keluar

# --- METRIC CARDS ---
st.subheader("Ringkasan")
col1, col2, col3 = st.columns(3)
col1.metric("Total Pemasukan", f"Rp {total_masuk:,.0f}".replace(",", "."))
col2.metric("Total Pengeluaran", f"Rp {total_keluar:,.0f}".replace(",", "."))
col3.metric("Balance", f"Rp {balance:,.0f}".replace(",", "."))

st.divider()

# --- INPUT FORM ---
def format_nominal(value):
    return f"{int(value):,}".replace(",", ".")

tab_input1, tab_input2 = st.tabs(["➕ Catat Pengeluaran", "💵 Catat Pemasukan"])

with tab_input1:
    col1, col2 = st.columns(2)
    with col1:
        tgl_keluar = st.date_input("Tanggal", value=date.today(), key="tgl_keluar")
        kat_keluar = st.selectbox("Kategori", config.CATEGORIES_PENGELUARAN)
    with col2:
        nom_keluar = st.number_input(
            "Nominal (IDR)",
            min_value=0,
            step=1000,
            key="nom_keluar",
            format="%d",
            help="Contoh: 50000 = Rp 50.000"
        )
        if nom_keluar > 0:
            st.caption(f"Rp {format_nominal(nom_keluar)}")
        cat_keluar = st.text_input("Catatan", placeholder="Opsional", key="cat_keluar")

    if st.button("Simpan Pengeluaran", use_container_width=True, type="primary"):
        if nom_keluar == 0:
            st.warning("Nominal tidak boleh 0")
        else:
            sheets.add_pengeluaran(str(tgl_keluar), kat_keluar, nom_keluar, cat_keluar)
            st.cache_data.clear()
            st.success(f"Pengeluaran Rp {format_nominal(nom_keluar)} berhasil disimpan!")
            st.rerun()

with tab_input2:
    col1, col2 = st.columns(2)
    with col1:
        tgl_masuk = st.date_input("Tanggal", value=date.today(), key="tgl_masuk")
        kat_masuk = st.selectbox("Kategori", config.CATEGORIES_PEMASUKAN)
    with col2:
        nom_masuk = st.number_input(
            "Nominal (IDR)",
            min_value=0,
            step=1000,
            key="nom_masuk",
            format="%d",
            help="Contoh: 50000 = Rp 50.000"
        )
        if nom_masuk > 0:
            st.caption(f"Rp {format_nominal(nom_masuk)}")
        cat_masuk = st.text_input("Catatan", placeholder="Opsional", key="cat_masuk")

    if st.button("Simpan Pemasukan", use_container_width=True, type="primary"):
        if nom_masuk == 0:
            st.warning("Nominal tidak boleh 0")
        else:
            sheets.add_pemasukan(str(tgl_masuk), kat_masuk, nom_masuk, cat_masuk)
            st.cache_data.clear()
            st.success(f"Pemasukan Rp {format_nominal(nom_masuk)} berhasil disimpan!")
            st.rerun()

st.divider()

# --- MONTHLY SUMMARY ---
st.subheader("📅 Summary Bulanan")

if not df_keluar.empty or not df_masuk.empty:
    bulan_list = []
    if not df_keluar.empty:
        df_keluar["Bulan"] = pd.to_datetime(df_keluar["Tanggal"]).dt.to_period("M").astype(str)
        bulan_list += df_keluar["Bulan"].unique().tolist()
    if not df_masuk.empty:
        df_masuk["Bulan"] = pd.to_datetime(df_masuk["Tanggal"]).dt.to_period("M").astype(str)
        bulan_list += df_masuk["Bulan"].unique().tolist()

    bulan_options = sorted(list(set(bulan_list)), reverse=True)
    selected_bulan = st.selectbox("Pilih Bulan", bulan_options)

    df_keluar_bulan = df_keluar[df_keluar["Bulan"] == selected_bulan] if not df_keluar.empty else pd.DataFrame()
    df_masuk_bulan = df_masuk[df_masuk["Bulan"] == selected_bulan] if not df_masuk.empty else pd.DataFrame()

    total_masuk_bulan = df_masuk_bulan["Nominal"].sum() if not df_masuk_bulan.empty else 0
    total_keluar_bulan = df_keluar_bulan["Nominal"].sum() if not df_keluar_bulan.empty else 0
    balance_bulan = total_masuk_bulan - total_keluar_bulan

    col1, col2, col3 = st.columns(3)
    col1.metric("Pemasukan", f"Rp {total_masuk_bulan:,.0f}".replace(",", "."))
    col2.metric("Pengeluaran", f"Rp {total_keluar_bulan:,.0f}".replace(",", "."))
    col3.metric("Balance Bulan Ini", f"Rp {balance_bulan:,.0f}".replace(",", "."))

    if not df_keluar_bulan.empty:
        st.write("**Pengeluaran per Kategori**")
        summary = df_keluar_bulan.groupby("Kategori")["Nominal"].sum()
        st.bar_chart(summary)
else:
    st.info("Belum ada data.")

st.divider()

# --- RIWAYAT & DELETE ---
st.subheader("📋 Riwayat Transaksi")

tab1, tab2 = st.tabs(["Pengeluaran", "Pemasukan"])

with tab1:
    if df_keluar.empty:
        st.info("Belum ada pengeluaran.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            filter_kat = st.multiselect("Filter Kategori", config.CATEGORIES_PENGELUARAN, key="filter_kat_keluar")
        with col2:
            filter_tgl = st.date_input("Filter Tanggal", value=None, key="filter_tgl_keluar")

        df_view = df_keluar.copy()
        if filter_kat:
            df_view = df_view[df_view["Kategori"].isin(filter_kat)]
        if filter_tgl:
            df_view = df_view[df_view["Tanggal"] == str(filter_tgl)]

        for i, row in df_view.iterrows():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"**{row['Tanggal']}** | {row['Kategori']} | Rp {int(row['Nominal']):,}".replace(",", ".") + f" | {row['Catatan']}")
            with col2:
                if st.button("🗑️", key=f"del_keluar_{i}"):
                    sheets.delete_row_pengeluaran(i)
                    st.cache_data.clear()
                    st.success("Transaksi dihapus!")
                    st.rerun()

with tab2:
    if df_masuk.empty:
        st.info("Belum ada pemasukan.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            filter_kat_masuk = st.multiselect("Filter Kategori", config.CATEGORIES_PEMASUKAN, key="filter_kat_masuk")
        with col2:
            filter_tgl_masuk = st.date_input("Filter Tanggal", value=None, key="filter_tgl_masuk")

        df_view_masuk = df_masuk.copy()
        if filter_kat_masuk:
            df_view_masuk = df_view_masuk[df_view_masuk["Kategori"].isin(filter_kat_masuk)]
        if filter_tgl_masuk:
            df_view_masuk = df_view_masuk[df_view_masuk["Tanggal"] == str(filter_tgl_masuk)]

        for i, row in df_view_masuk.iterrows():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"**{row['Tanggal']}** | {row['Kategori']} | Rp {int(row['Nominal']):,}".replace(",", ".") + f" | {row['Catatan']}")
            with col2:
                if st.button("🗑️", key=f"del_masuk_{i}"):
                    sheets.delete_row_pemasukan(i)
                    st.cache_data.clear()
                    st.success("Transaksi dihapus!")
                    st.rerun()