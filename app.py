import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="MNS Document Tracking System", 
    layout="wide", 
    page_icon="📑",
    initial_sidebar_state="expanded"
)

# --- INJEKSI KUSTOM CSS UNTUK TAMPILAN PROFESIONAL ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8f9fa;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #1e293b;
    }
    div.stForm, div[data-testid="stDataFrame"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        border: 1px solid #e2e8f0;
    }
    div.stButton > button {
        background-color: #0f172a !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #1e293b !important;
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. KONEKSI KE SUPABASE ---
@st.cache_resource
def init_connection():
    raw_url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    clean_url = raw_url.split("/rest/v1")[0].strip().rstrip("/")
    return create_client(clean_url, key)

supabase: Client = init_connection()

def get_users():
    response = supabase.table("users").select("*").execute()
    return pd.DataFrame(response.data)

def get_dokumen():
    response = supabase.table("dokumen").select("*").order("id", desc=True).execute()
    return pd.DataFrame(response.data)

# --- FUNGSI PEWARNAAN TABEL (PANDAS STYLER) ---
def style_dataframe(df):
    def highlight_status(val):
        val_str = str(val).upper().strip()
        if val_str == 'DITERIMA':
            return 'background-color: #ffffff; color: #000000;'
        elif val_str == 'DALAM PROSES SIGN BUH':
            return 'background-color: #fff3cd; color: #664d03; font-weight: 600;'
        elif val_str == 'REVISI (DETAIL REVISI HUBUNGI SEKRETARIS)':
            return 'background-color: #f8d7da; color: #842029; font-weight: 600;'
        elif val_str == 'SIAP DIAMBIL':
            return 'background-color: #d1e7dd; color: #0f5132; font-weight: 600;'
        elif val_str == 'SELESAI':
            return 'background-color: #cce5ff; color: #084298; font-weight: 600;'
        return ''
    
    try:
        return df.style.map(highlight_status, subset=['status'])
    except AttributeError:
        return df.style.applymap(highlight_status, subset=['status'])

# --- FUNGSI TAMPILAN DROPDOWN (FORMAT_FUNC) ---
def format_status_opsi(opsi):
    if opsi == "Diterima": return "⚪ Diterima"
    elif opsi == "Dalam Proses Sign BUH": return "🟡 Dalam Proses Sign BUH"
    elif opsi == "Revisi (Detail Revisi Hubungi Sekretaris)": return "🔴 Revisi"
    elif opsi == "Siap diambil": return "🟢 Siap diambil"
    elif opsi == "Selesai": return "🔵 Selesai"
    return opsi

# --- MASTER DATA ---
DAFTAR_DEPARTEMEN = sorted([
    "ACCOUNTING", "BIODIESEL", "CC", "CONSUMER PACK", "CRUSHING", 
    "EFFLUENT", "EHS", "ELECTRICAL", "FINANCE", "HRGA", 
    "LOGISTIC", "MHE", "PPIC", "PROJECT", "PURCHASING", 
    "QA", "QC", "QPE", "REF", "SECURITY & HUMAS", 
    "SHIPPING", "SOLVENT", "STORE", "TANK FARM", 
    "TRADING", "UTILITY", "WB"
])

# --- KONFIGURASI DESAIN TABEL INTERAKTIF ---
CONFIG_TABEL = {
    "department": st.column_config.TextColumn("🏢 Departemen", help="Departemen pemilik berkas", width="medium"),
    "pic": st.column_config.TextColumn("👤 Nama PIC", width="medium"),
    "dokumen": st.column_config.TextColumn("📄 Nama Dokumen", width="large"),
    "tanggal_masuk": st.column_config.DateColumn("📅 Tanggal Masuk", format="DD MMM YYYY"),
    "tanggal_ambil": st.column_config.DateColumn("📦 Tanggal Ambil", format="DD MMM YYYY"),
    "urgency": st.column_config.SelectboxColumn("🚨 Urgency", options=["Normal", "High", "Urgent"], required=True),
    "status": st.column_config.SelectboxColumn(
        "⚙️ Status Berkas", 
        options=["Diterima", "Dalam Proses Sign BUH", "Revisi (Detail Revisi Hubungi Sekretaris)", "Siap diambil", "Selesai"], 
        required=True
    ),
    "remark": st.column_config.TextColumn("💬 Catatan / Remark", width="large")
}

# --- 3. MANAJEMEN LOGIN ---
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
    st.session_state.session_dept = None
    st.session_state.session_role = None

# Header Korporat
st.markdown("<h1 style='color: #0f172a; margin-bottom: 0px;'>📑 Document Tracking Portal</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 15px;'>Multi Nabati Sulawesi — Independent BUH Sign Monitoring System</p>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# --- 4. PORTAL LOGIN ---
if not st.session_state.is_logged_in:
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        with st.form("login_box"):
            st.markdown("<h3 style='text-align: center; color: #0f172a;'>🔑 Login System</h3>", unsafe_allow_html=True)
            try:
                db_users = get_users()
                if not db_users.empty:
                    list_dept = db_users['dept_name'].tolist()
                    dept_input = st.selectbox("Pilih Departemen", ["-- Silakan Pilih Departemen --"] + list_dept)
                    password_input = st.text_input("Sandi Akses", type="password")
                    
                    if st.form_submit_button("Autentikasi Masuk", use_container_width=True):
                        match = db_users[(db_users['dept_name'] == dept_input) & (db_users['password'] == password_input)]
                        if not match.empty:
                            st.session_state.is_logged_in = True
                            st.session_state.session_dept = dept_input
                            st.session_state.session_role = match.iloc[0]['role']
                            st.rerun()
                        else:
                            st.error("Kombinasi departemen dan sandi tidak cocok!")
                else:
                    st.error("Koneksi database aman, namun data pengguna kosong.")
            except Exception as e:
                st.error(f"Gagal memuat sistem login: {e}")

# --- 5. DASHBOARD UTAMA PORTAL ---
else:
    current_dept = st.session_state.session_dept
    current_role = st.session_state.session_role
    
    st.sidebar.markdown("### 🏢 Sesi Aktif")
    st.sidebar.info(f"**Departemen:**\n{current_dept}\n\n**Otoritas:**\n{current_role.upper()}")
    st.sidebar.markdown("---")
    if st.sidebar.button("🔴 Keluar (Log Out)", use_container_width=True):
        st.session_state.is_logged_in = False
        st.session_state.session_dept = None
        st.session_state.session_role = None
        st.rerun()

    df_docs = get_dokumen()

    if current_role == 'admin':
        st.subheader("🛠️ Konsol Kendali Sekretaris (Admin Master)")
        
        if not df_docs.empty:
            m_total = len(df_docs)
            m_out = len(df_docs[~df_docs['status'].str.upper().isin(['SELESAI', 'SIAP DIAMBIL'])])
            m_rev = len(df_docs[df_docs['status'].str.upper() == 'REVISI (DETAIL REVISI HUBUNGI SEKRETARIS)'])
            m_done = len(df_docs[df_docs['status'].str.upper().isin(['SELESAI', 'SIAP DIAMBIL'])])
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📦 Total Semua Berkas", m_total)
            c2.metric("⏳ Outstanding di BUH", m_out, delta_color="inverse")
            c3.metric("⚠️ Perlu Tindakan Revisi", m_rev, delta_color="inverse")
            c4.metric("✅ Selesai / Siap Diambil", m_done)
            st.markdown("<br>", unsafe_allow_html=True)

        tab_tambah, tab_update, tab_database = st.tabs(["➕ Registrasi Berkas Baru", "📝 Pembaharuan Status & Catatan", "🗂️ Master Database Global"])
        
        with tab_tambah:
            with st.form("form_tambah"):
                st.markdown("##### 📥 Penginputan Berkas Baru Masuk")
                col1, col2 = st.columns(2)
                with col1:
                    # BERHASIL DIUBAH DI SINI 👇
                    i_dept = st.selectbox("Departemen", ["-- Pilih Departemen --"] + DAFTAR_DEPARTEMEN)
                    i_pic = st.text_input("Nama PIC Berkas")
                    i_dokumen = st.text_input("Judul / Nama Dokumen Resmi")
                with col2:
                    i_tgl_masuk = st.date_input("Tanggal Berkas Diterima")
                    i_urgency = st.selectbox("Prioritas Kecepatan", ["Normal", "High", "Urgent"])
                
                if st.form_submit_button("Simpan Dokumen Baru"):
                    if i_dept != "-- Pilih Departemen --" and i_dokumen:
                        supabase.table("dokumen").insert({
                            "department": i_dept, 
                            "pic": i_pic.strip(), 
                            "dokumen": i_dokumen.strip(),
                            "tanggal_masuk": str(i_tgl_masuk), 
                            "urgency": i_urgency, 
                            "status": "Diterima"
                        }).execute()
                        st.success("Dokumen berhasil dimasukkan ke sistem cloud!")
                        st.rerun()
                    else:
                        st.error("Kolom Departemen (wajib dipilih) dan Nama Dokumen bersyarat wajib diisi!")

        with tab_update:
            if not df_docs.empty:
                def format_dropdown_label(row):
                    stat = str(row['status']).upper().strip()
                    base_text = f"{row['id']} - {row['dokumen']} [{row['department']}]"
                    if stat == 'DITERIMA': return f"{base_text} ➔ ⚪ Diterima"
                    elif stat == 'DALAM PROSES SIGN BUH': return f"{base_text} ➔ 🟡 Proses BUH"
                    elif stat == 'REVISI (DETAIL REVISI HUBUNGI SEKRETARIS)': return f"{base_text} ➔ 🔴 Revisi"
                    elif stat == 'SIAP DIAMBIL': return f"{base_text} ➔ 🟢 Siap Diambil"
                    elif stat == 'SELESAI': return f"{base_text} ➔ 🔵 Selesai"
                    else: return f"{base_text} ➔ ⏳ {row['status']}"

                df_docs['dropdown_label'] = df_docs.apply(format_dropdown_label, axis=1)
                pilihan_dokumen = st.selectbox("Pilih berkas yang ingin diubah kinerjanya:", df_docs['dropdown_label'])
                
                if pilihan_dokumen:
                    doc_id = int(pilihan_dokumen.split(" - ")[0])
                    doc_terpilih = df_docs[df_docs['id'] == doc_id].iloc[0]
                    
                    with st.form("form_update"):
                        st.markdown(f"##### 📋 Formulir Evaluasi: `{doc_terpilih['dokumen']}`")
                        col_u1, col_u2 = st.columns(2)
                        with col_u1:
                            status_arr = [
                                "Diterima", 
                                "Dalam Proses Sign BUH", 
                                "Revisi (Detail Revisi Hubungi Sekretaris)", 
                                "Siap diambil", 
                                "Selesai"
                            ]
                            u_status = st.selectbox(
                                "Status Operasional Terbaru:", 
                                status_arr, 
                                index=status_arr.index(doc_terpilih['status']) if doc_terpilih['status'] in status_arr else 0,
                                format_func=format_status_opsi
                            )
                            u_remark = st.text_input("Catatan Tambahan Sekretaris (Remark):", value=doc_terpilih['remark'] if pd.notna(doc_terpilih['remark']) else "")
                        with col_u2:
                            tgl_db = doc_terpilih.get('tanggal_ambil')
                            tgl_awal = pd.to_datetime(tgl_db).date() if pd.notna(tgl_db) and tgl_db != "" else None
                            u_tgl_ambil = st.date_input("Tanggal Selesai Diambil Departemen (Silang X jika belum):", value=tgl_awal)
                        
                        if st.form_submit_button("Terapkan Perubahan Data"):
                            tgl_simpan = str(u_tgl_ambil) if u_tgl_ambil is not None else None
                            supabase.table("dokumen").update({
                                "status": u_status, "remark": u_remark.strip(), "tanggal_ambil": tgl_simpan
                            }).eq("id", doc_id).execute()
                            st.success("Database berhasil dimutakhirkan!")
                            st.rerun()
                            
        with tab_database:
            st.markdown("##### 🌍 Seluruh Berkas Lintas Departemen PT Multi Nabati Sulawesi")
            df_to_show = df_docs[['department', 'pic', 'dokumen', 'tanggal_masuk', 'tanggal_ambil', 'urgency', 'status', 'remark']]
            st.dataframe(style_dataframe(df_to_show), use_container_width=True, column_config=CONFIG_TABEL, hide_index=True)

    else:
        st.subheader(f"📊 Dashboard Monitoring Dokumen Internal")
        
        if not df_docs.empty:
            df_docs['dept_clean'] = df_docs['department'].astype(str).str.strip().str.upper()
            df_filtered = df_docs[df_docs['dept_clean'] == current_dept.strip().upper()]
            
            m_user_out = len(df_filtered[~df_filtered['status'].str.upper().isin(['SELESAI', 'SIAP DIAMBIL'])])
            m_user_rev = len(df_filtered[df_filtered['status'].str.upper() == 'REVISI (DETAIL REVISI HUBUNGI SEKRETARIS)'])
            m_user_done = len(df_filtered[df_filtered['status'].str.upper().isin(['SELESAI', 'SIAP DIAMBIL'])])
            
            uc1, uc2, uc3 = st.columns(3)
            uc1.metric("⏳ Berkas Outstanding di Meja BUH", m_user_out)
            uc2.metric("⚠️ Berkas Butuh Revisi Segera", m_user_rev)
            uc3.metric("✅ Berkas Selesai & Siap Diambil", m_user_done)
            st.markdown("<br>", unsafe_allow_html=True)
            
            if df_filtered.empty:
                st.info(f"Belum ada berkas dokumen yang terdaftar atas nama departemen {current_dept}.")
            else:
                kolom_tampilan = ['pic', 'dokumen', 'tanggal_masuk', 'tanggal_ambil', 'urgency', 'status', 'remark']
                df_filtered['status_clean'] = df_filtered['status'].astype(str).str.strip().str.upper()
                df_completed = df_filtered[df_filtered['status_clean'].isin(['SELESAI', 'SIAP DIAMBIL'])]
                df_outstanding = df_filtered[~df_filtered['status_clean'].isin(['SELESAI', 'SIAP DIAMBIL'])]
                
                tab_out, tab_comp = st.tabs(["⏳ Berkas Outstanding (Prioritas Pantau)", "✅ Berkas Completed (Arsip Riwayat)"])
                
                with tab_out:
                    if df_outstanding.empty: 
                        st.success("Luar biasa! Tidak ada berkas outstanding. Seluruh dokumen Anda bersih bersertifikat.")
                    else: 
                        st.dataframe(style_dataframe(df_outstanding[kolom_tampilan]), use_container_width=True, column_config=CONFIG_TABEL, hide_index=True)
                with tab_comp:
                    if df_completed.empty: 
                        st.info("Belum ada rekam jejak berkas berstatus selesai ditandatangani untuk departemen Anda.")
                    else: 
                        st.dataframe(style_dataframe(df_completed[kolom_tampilan]), use_container_width=True, column_config=CONFIG_TABEL, hide_index=True)
        else:
            st.warning("Gagal memproses sinkronisasi master data.")
