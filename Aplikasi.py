import streamlit as st
import sqlite3
import pandas as pd
import openpyxl
import shutil
import os
from io import BytesIO

def init_db():
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS siswa (
                    id_siswa INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT UNIQUE NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subjek (
                    id_subjek INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama_subjek TEXT UNIQUE NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS relasi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_siswa_penginput INTEGER,
                    id_siswa_target INTEGER,
                    id_subjek INTEGER,
                    status TEXT CHECK(status IN ('suka', 'tidak suka')),
                    alasan TEXT,
                    FOREIGN KEY(id_siswa_penginput) REFERENCES siswa(id_siswa),
                    FOREIGN KEY(id_siswa_target) REFERENCES siswa(id_siswa),
                    FOREIGN KEY(id_subjek) REFERENCES subjek(id_subjek))''')
    # Add alasan column if not exists
    try:
        c.execute("ALTER TABLE relasi ADD COLUMN alasan TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()

# Fungsi untuk mendapatkan data siswa
def get_siswa():
    conn = sqlite3.connect('Database.db')
    df = pd.read_sql_query("SELECT * FROM siswa", conn)
    conn.close()
    return df

# Fungsi untuk mendapatkan data subjek
def get_subjek():
    conn = sqlite3.connect('Database.db')
    df = pd.read_sql_query("SELECT * FROM subjek", conn)
    conn.close()
    return df

# Fungsi untuk mendapatkan data relasi
def get_relasi():
    conn = sqlite3.connect('Database.db')
    df = pd.read_sql_query("SELECT * FROM relasi", conn)
    conn.close()
    return df

# Fungsi untuk menambah siswa
def add_siswa(nama):
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO siswa (nama) VALUES (?)", (nama,))
        conn.commit()
        st.success("Siswa berhasil ditambahkan!")
    except sqlite3.IntegrityError:
        st.error("Nama siswa sudah ada!")
    conn.close()

# Fungsi untuk menambah subjek
def add_subjek(nama_subjek):
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO subjek (nama_subjek) VALUES (?)", (nama_subjek,))
        conn.commit()
        st.success("Subjek berhasil ditambahkan!")
    except sqlite3.IntegrityError:
        st.error("Nama subjek sudah ada!")
    conn.close()

# Fungsi untuk menambah relasi
def add_relasi(id_penginput, id_target, id_subjek, status, alasan=None):
    # Validasi penginput != target
    if id_penginput == id_target:
        st.error("Siswa tidak boleh memilih dirinya sendiri!")
        return
    # Validasi max 1 suka dan 1 tidak suka per siswa per subjek
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    if status == 'suka':
        c.execute("SELECT COUNT(*) FROM relasi WHERE id_siswa_penginput=? AND id_subjek=? AND status='suka'",
                  (id_penginput, id_subjek))
        if c.fetchone()[0] >= 1:
            conn.close()
            st.error("Siswa sudah memilih 1 siswa yang disukai untuk subjek ini!")
            return
    elif status == 'tidak suka':
        c.execute("SELECT COUNT(*) FROM relasi WHERE id_siswa_penginput=? AND id_subjek=? AND status='tidak suka'",
                  (id_penginput, id_subjek))
        if c.fetchone()[0] >= 1:
            conn.close()
            st.error("Siswa sudah memilih 1 siswa yang tidak disukai untuk subjek ini!")
            return
    # Validasi duplikat
    c.execute("SELECT COUNT(*) FROM relasi WHERE id_siswa_penginput=? AND id_siswa_target=? AND id_subjek=? AND status=?",
              (id_penginput, id_target, id_subjek, status))
    if c.fetchone()[0] > 0:
        conn.close()
        st.error("Relasi duplikat ditemukan!")
        return
    c.execute("INSERT INTO relasi (id_siswa_penginput, id_siswa_target, id_subjek, status, alasan) VALUES (?, ?, ?, ?, ?)",
              (id_penginput, id_target, id_subjek, status, alasan))
    conn.commit()
    conn.close()
    st.success("Relasi berhasil ditambahkan!")

# Fungsi untuk menambah relasi batch
def add_relasi_batch(id_penginput, relasi_list, id_subjek):
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    for target_id, status in relasi_list:
        if status != 'netral':
            # Cek duplikat
            c.execute("SELECT COUNT(*) FROM relasi WHERE id_siswa_penginput=? AND id_siswa_target=? AND id_subjek=? AND status=?",
                      (id_penginput, target_id, id_subjek, status))
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO relasi (id_siswa_penginput, id_siswa_target, id_subjek, status) VALUES (?, ?, ?, ?)",
                          (id_penginput, target_id, id_subjek, status))
    conn.commit()
    conn.close()
    st.success("Relasi batch berhasil ditambahkan!")

# Fungsi edit siswa
def edit_siswa(id_siswa, nama_baru):
    if len(nama_baru) < 2:
        st.error("Nama siswa minimal 2 karakter!")
        return
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE siswa SET nama=? WHERE id_siswa=?", (nama_baru, id_siswa))
        conn.commit()
        st.success("Siswa berhasil diedit!")
    except sqlite3.IntegrityError:
        st.error("Nama siswa sudah ada!")
    conn.close()

# Fungsi delete siswa
def delete_siswa(id_siswa):
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    c.execute("DELETE FROM relasi WHERE id_siswa_penginput=? OR id_siswa_target=?", (id_siswa, id_siswa))
    c.execute("DELETE FROM siswa WHERE id_siswa=?", (id_siswa,))
    conn.commit()
    conn.close()
    st.success("Siswa berhasil dihapus!")

# Fungsi edit subjek
def edit_subjek(id_subjek, nama_baru):
    if len(nama_baru) < 2:
        st.error("Nama subjek minimal 2 karakter!")
        return
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE subjek SET nama_subjek=? WHERE id_subjek=?", (nama_baru, id_subjek))
        conn.commit()
        st.success("Subjek berhasil diedit!")
    except sqlite3.IntegrityError:
        st.error("Nama subjek sudah ada!")
    conn.close()

# Fungsi delete subjek
def delete_subjek(id_subjek):
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    c.execute("DELETE FROM relasi WHERE id_subjek=?", (id_subjek,))
    c.execute("DELETE FROM subjek WHERE id_subjek=?", (id_subjek,))
    conn.commit()
    conn.close()
    st.success("Subjek berhasil dihapus!")

# Fungsi delete relasi
def delete_relasi(id_relasi):
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    c.execute("DELETE FROM relasi WHERE id=?", (id_relasi,))
    conn.commit()
    conn.close()
    st.success("Relasi berhasil dihapus!")

# Fungsi ekspor CSV
def export_csv(df, filename):
    csv = df.to_csv(index=False)
    st.download_button(label="Download CSV", data=csv, file_name=filename, mime='text/csv')

# Fungsi ekspor Excel
def export_excel(df, filename):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    buffer.seek(0)
    st.download_button(label="Download Excel", data=buffer, file_name=filename, mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Fungsi impor siswa
def import_siswa(df_import):
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    duplicates = []
    imported = 0
    for _, row in df_import.iterrows():
        nama = row['nama']
        if len(nama) < 2:
            st.error(f"Nama '{nama}' terlalu pendek!")
            continue
        try:
            c.execute("INSERT INTO siswa (nama) VALUES (?)", (nama,))
            imported += 1
        except sqlite3.IntegrityError:
            duplicates.append(nama)
    conn.commit()
    conn.close()
    if imported > 0:
        st.success(f"{imported} siswa berhasil diimpor!")
    if duplicates:
        st.warning(f"Duplikat dilewati: {', '.join(duplicates)}")

# Fungsi reset database
def reset_db():
    conn = sqlite3.connect('Database.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS relasi")
    c.execute("DROP TABLE IF EXISTS subjek")
    c.execute("DROP TABLE IF EXISTS siswa")

# Fungsi backup database
def backup_db():
    if os.path.exists('Database.db'):
        shutil.copy('Database.db', 'Database_backup.db')
        st.success("Database berhasil di-backup sebagai Database_backup.db")
    else:
        st.error("Database tidak ditemukan!")

# Fungsi highlight status untuk styling tabel
def highlight_status(val):
    if val == 'Populer':
        return 'background-color: #90ee90'
    elif val == 'Rentan Dibully':
        return 'background-color: #ffcccb'
    elif val == 'Pembuli Potensial':
        return 'background-color: #ffcccb'
    else:
        return ''

# Fungsi analisis
def analisis(popular_threshold=2, vulnerable_threshold=-2):
    conn = sqlite3.connect('Database.db')
    # Hitung skor diterima per siswa keseluruhan
    df_relasi = pd.read_sql_query("""
        SELECT s.nama, r.status,
               CASE WHEN r.status = 'suka' THEN 1 ELSE -1 END as skor
        FROM relasi r
        JOIN siswa s ON r.id_siswa_target = s.id_siswa
    """, conn)
    # Hitung skor per subjek
    df_relasi_subjek = pd.read_sql_query("""
        SELECT s.nama, sub.nama_subjek, r.status,
               CASE WHEN r.status = 'suka' THEN 1 ELSE -1 END as skor
        FROM relasi r
        JOIN siswa s ON r.id_siswa_target = s.id_siswa
        JOIN subjek sub ON r.id_subjek = sub.id_subjek
    """, conn)
    # Hitung pembuli potensial (siswa yang sering memberi tidak suka)
    df_pembuli = pd.read_sql_query("""
        SELECT s.nama, COUNT(*) as jumlah_tidak_suka
        FROM relasi r
        JOIN siswa s ON r.id_siswa_penginput = s.id_siswa
        WHERE r.status = 'tidak suka'
        GROUP BY s.nama
        ORDER BY jumlah_tidak_suka DESC
    """, conn)
    conn.close()
    if df_relasi.empty:
        st.warning("Belum ada data relasi untuk dianalisis.")
        return None, None, None
    # Analisis keseluruhan
    skor_df = df_relasi.groupby('nama')['skor'].sum().reset_index()
    skor_df = skor_df.sort_values('skor', ascending=False)
    skor_df['status'] = 'Normal'
    skor_df.loc[skor_df['skor'] > popular_threshold, 'status'] = 'Populer'
    skor_df.loc[skor_df['skor'] < vulnerable_threshold, 'status'] = 'Rentan Dibully'
    # Analisis per subjek
    skor_subjek_df = df_relasi_subjek.groupby(['nama_subjek', 'nama'])['skor'].sum().reset_index()
    skor_subjek_df['status'] = 'Normal'
    skor_subjek_df.loc[skor_subjek_df['skor'] > popular_threshold, 'status'] = 'Populer'
    skor_subjek_df.loc[skor_subjek_df['skor'] < vulnerable_threshold, 'status'] = 'Rentan Dibully'
    # Pembuli potensial
    df_pembuli['status'] = 'Normal'
    df_pembuli.loc[df_pembuli['jumlah_tidak_suka'] > 3, 'status'] = 'Pembuli Potensial'  # Threshold sederhana
    return skor_df, skor_subjek_df, df_pembuli

import networkx as nx
import matplotlib.pyplot as plt

# Fungsi untuk menggambar grafik relasi
def draw_relationship_graph():
    conn = sqlite3.connect('Database.db')
    df_relasi = pd.read_sql_query("""
        SELECT s1.nama as penginput, s2.nama as target, r.status, r.alasan
        FROM relasi r
        JOIN siswa s1 ON r.id_siswa_penginput = s1.id_siswa
        JOIN siswa s2 ON r.id_siswa_target = s2.id_siswa
    """, conn)
    conn.close()

    if df_relasi.empty:
        st.warning("Belum ada data relasi untuk ditampilkan.")
        return

    G = nx.DiGraph()

    # Tambah node siswa
    siswa = set(df_relasi['penginput']).union(set(df_relasi['target']))
    for s in siswa:
        G.add_node(s)

    # Tambah edge dengan warna dan label alasan
    for _, row in df_relasi.iterrows():
        color = 'green' if row['status'] == 'suka' else 'red'
        G.add_edge(row['penginput'], row['target'], color=color, label=row['alasan'])

    pos = nx.spring_layout(G, seed=42)
    edge_colors = [G[u][v]['color'] for u,v in G.edges()]
    edge_labels = {(u,v): G[u][v]['label'] for u,v in G.edges()}

    plt.figure(figsize=(10,7))
    nx.draw(G, pos, with_labels=True, edge_color=edge_colors, node_color='lightblue', node_size=2000, arrowsize=20)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='black')

    # Legend
    import matplotlib.patches as mpatches
    green_patch = mpatches.Patch(color='green', label='Suka')
    red_patch = mpatches.Patch(color='red', label='Tidak Suka')
    plt.legend(handles=[green_patch, red_patch])

    st.pyplot(plt)

# Inisialisasi database
init_db()

# Judul aplikasi
st.title("No-Bully App")
st.write("Aplikasi untuk mendeteksi risiko bullying di sekolah.")

# Sidebar navigasi
default_menu = st.session_state.get('menu', 'Dashboard')
menu_options = ["Dashboard", "Input Siswa", "Input Subjek", "Input Relasi", "Analisis", "Pengaturan"]
menu = st.sidebar.radio("Menu", menu_options, index=menu_options.index(default_menu))

if menu == "Dashboard":
    st.header("🏠 Dashboard")
    st.write("Selamat datang di No-Bully App! 🎉")
    st.write("Aplikasi untuk mendeteksi risiko bullying di sekolah.")

    # Quotes
    quotes = [
        "🌟 'Bullying adalah masalah serius yang perlu diatasi bersama.'",
        "🤝 'Mari ciptakan lingkungan sekolah yang aman dan nyaman untuk semua siswa.'",
        "💪 'Setiap siswa berhak merasa aman dan dihargai.'"
    ]
    st.subheader("💬 Kata-Kata Inspiratif")
    st.info(quotes[0])
    st.info(quotes[1])
    st.info(quotes[2])

    # Shortcuts
    st.subheader("🔗 Pintasan Menu")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 Input Siswa"):
            st.session_state.menu = "Input Siswa"
            st.experimental_rerun()
    with col2:
        if st.button("📚 Input Subjek"):
            st.session_state.menu = "Input Subjek"
            st.experimental_rerun()
    with col3:
        if st.button("❤️ Input Relasi"):
            st.session_state.menu = "Input Relasi"
            st.experimental_rerun()

    # Summary stats
    st.subheader("📊 Ringkasan Data")
    df_siswa = get_siswa()
    df_subjek = get_subjek()
    df_relasi = get_relasi()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👨‍🎓 Jumlah Siswa", len(df_siswa))
    with col2:
        st.metric("📖 Jumlah Subjek", len(df_subjek))
    with col3:
        st.metric("🔗 Jumlah Relasi", len(df_relasi))

elif menu == "Input Siswa":
    st.header("📝 Input Data Siswa")
    nama = st.text_input("Nama Siswa")
    if st.button("Tambah Siswa"):
        if nama:
            add_siswa(nama)
        else:
            st.error("Nama siswa tidak boleh kosong!")

    # Import from Excel/CSV
    st.subheader("📤 Impor dari File Excel/CSV")
    uploaded_file = st.file_uploader("Pilih file Excel atau CSV", type=['xlsx', 'csv'])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.xlsx'):
            df_import = pd.read_excel(uploaded_file)
        else:
            df_import = pd.read_csv(uploaded_file)
        st.write("Preview Data:")
        st.dataframe(df_import.head())

        # Allow user to select the column for student names
        col_options = df_import.columns.tolist()
        selected_col = st.selectbox("Pilih kolom yang berisi nama siswa", col_options)

        if st.button("Impor Siswa"):
            if selected_col in df_import.columns:
                df_import_renamed = df_import.rename(columns={selected_col: 'nama'})
                import_siswa(df_import_renamed)
            else:
                st.error(f"Kolom '{selected_col}' tidak ditemukan di file!")

    st.subheader("Daftar Siswa")
    df_siswa = get_siswa()

    # Add edit and delete functionality
    if not df_siswa.empty:
        st.write("Edit / Hapus Siswa:")
        for idx, row in df_siswa.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                new_name = st.text_input(f"Nama siswa {row['id_siswa']}", value=row['nama'], key=f"edit_{row['id_siswa']}")
            with col2:
                if st.button("Simpan", key=f"save_{row['id_siswa']}"):
                    if new_name and new_name != row['nama']:
                        edit_siswa(row['id_siswa'], new_name)
                        st.experimental_rerun()
            with col3:
                if st.button("Hapus", key=f"delete_{row['id_siswa']}"):
                    delete_siswa(row['id_siswa'])
                    st.experimental_rerun()

        st.dataframe(df_siswa)
        export_csv(df_siswa, 'daftar_siswa.csv')
        export_excel(df_siswa, 'daftar_siswa.xlsx')

elif menu == "Input Subjek":
    st.header("Input Data Subjek")
    nama_subjek = st.text_input("Nama Subjek")
    if st.button("Tambah Subjek"):
        if nama_subjek:
            add_subjek(nama_subjek)
        else:
            st.error("Nama subjek tidak boleh kosong!")
    st.subheader("Daftar Subjek")
    df_subjek = get_subjek()

    # Add edit and delete functionality
    if not df_subjek.empty:
        st.write("Edit / Hapus Subjek:")
        for idx, row in df_subjek.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                new_name = st.text_input(f"Nama subjek {row['id_subjek']}", value=row['nama_subjek'], key=f"edit_subjek_{row['id_subjek']}")
            with col2:
                if st.button("Simpan", key=f"save_subjek_{row['id_subjek']}"):
                    if new_name and new_name != row['nama_subjek']:
                        edit_subjek(row['id_subjek'], new_name)
                        st.experimental_rerun()
            with col3:
                if st.button("Hapus", key=f"delete_subjek_{row['id_subjek']}"):
                    delete_subjek(row['id_subjek'])
                    st.experimental_rerun()

        st.dataframe(df_subjek)
        export_csv(df_subjek, 'daftar_subjek.csv')
        export_excel(df_subjek, 'daftar_subjek.xlsx')

elif menu == "Input Relasi":
    st.header("Input Relasi Suka/Tidak Suka")
    df_subjek = get_subjek()
    df_siswa = get_siswa()
    if df_subjek.empty or df_siswa.empty:
        st.warning("Pastikan ada data siswa dan subjek terlebih dahulu.")
    else:
        siswa_options = dict(zip(df_siswa['nama'], df_siswa['id_siswa']))
        subjek_options = dict(zip(df_subjek['nama_subjek'], df_subjek['id_subjek']))

        penginput = st.selectbox("Pilih Siswa Penginput", list(siswa_options.keys()))
        target = st.selectbox("Pilih Siswa Target", [s for s in siswa_options.keys() if s != penginput])
        subjek = st.selectbox("Pilih Subjek", list(subjek_options.keys()))
        status = st.selectbox("Pilih Status", ["suka", "tidak suka"])

        if status == "suka":
            alasan_options = ["Ramah", "Baik Hati", "Membantu"]
        else:
            alasan_options = ["Nakal", "Sombong", "Mengganggu"]

        alasan = st.selectbox("Pilih Alasan", alasan_options)

        if st.button("Tambah Relasi"):
            add_relasi(siswa_options[penginput], siswa_options[target], subjek_options[subjek], status, alasan)

elif menu == "Analisis":
    st.header("Analisis Risiko Bullying")
    popular_threshold = st.sidebar.number_input("Threshold Populer", min_value=1, max_value=10, value=2)
    vulnerable_threshold = st.sidebar.number_input("Threshold Rentan", min_value=-10, max_value=-1, value=-2)
    skor_df, skor_subjek_df, df_pembuli = analisis(popular_threshold, vulnerable_threshold)
    if skor_df is not None:
        # Dashboard ringkasan
        st.subheader("Dashboard Ringkasan")
        populer_count = skor_df[skor_df['status'] == 'Populer'].shape[0]
        rentan_count = skor_df[skor_df['status'] == 'Rentan Dibully'].shape[0]
        pembuli_count = df_pembuli[df_pembuli['status'] == 'Pembuli Potensial'].shape[0]
        st.write(f"- Jumlah Siswa Populer: {populer_count}")
        st.write(f"- Jumlah Siswa Rentan Dibully: {rentan_count}")
        st.write(f"- Jumlah Pembuli Potensial: {pembuli_count}")
        # Analisis keseluruhan
        st.subheader("Analisis Keseluruhan")
        st.dataframe(skor_df.style.apply(lambda x: ['background-color: #90ee90' if v == 'Populer' else ('background-color: #ffcccb' if v == 'Rentan Dibully' else '') for v in x], axis=1))
        st.bar_chart(skor_df.set_index('nama')['skor'])
        # Analisis per subjek
        st.subheader("Analisis Per Subjek")
        subjek_list = skor_subjek_df['nama_subjek'].unique()
        selected_subjek = st.selectbox("Pilih Subjek", subjek_list)
        df_subjek_filtered = skor_subjek_df[skor_subjek_df['nama_subjek'] == selected_subjek]
        status_filter = ['Populer', 'Rentan Dibully', 'Normal']
        df_subjek_filtered = df_subjek_filtered[df_subjek_filtered['status'].isin(status_filter)]
        st.dataframe(df_subjek_filtered.style.applymap(highlight_status, subset=['status']))
        export_csv(df_subjek_filtered, f'analisis_{selected_subjek}.csv')
        export_excel(df_subjek_filtered, f'analisis_{selected_subjek}.xlsx')
        st.bar_chart(df_subjek_filtered.set_index('nama')['skor'])
        # Pembuli potensial
        st.subheader("Pembuli Potensial")
        df_pembuli_filtered = df_pembuli[df_pembuli['status'].isin(['Normal', 'Pembuli Potensial'])]
        st.dataframe(df_pembuli_filtered.style.applymap(lambda val: 'background-color: #ffcccb' if val == 'Pembuli Potensial' else '', subset=['status']))
        export_csv(df_pembuli_filtered, 'pembuli_potensial.csv')
        export_excel(df_pembuli_filtered, 'pembuli_potensial.xlsx')

        # Tambahkan grafik relasi suka/tidak suka
        st.subheader("Grafik Relasi Suka/Tidak Suka")
        draw_relationship_graph()

# Tambahkan menu Pengaturan
elif menu == "Pengaturan":
    st.header("Pengaturan Aplikasi")
    # Reset Database
    if st.button("Reset Database"):
        confirm_reset = st.checkbox("Konfirmasi reset database? Semua data akan hilang!")
        if confirm_reset:
            reset_db()
    # Backup Database
    st.subheader("Backup Database")
    backup_db()
    # About App
    st.subheader("About App")
    st.write("No-Bully App v1.0")
    st.write("Aplikasi untuk mendeteksi risiko bullying di sekolah menggunakan analisis relasi siswa.")
    st.write("Dikembangkan dengan Python + Streamlit + SQLite.")
