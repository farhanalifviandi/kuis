import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- Konfigurasi ---
# Pastikan nama file Google Sheet Anda sesuai, atau gunakan URL lengkapnya nanti di secrets
SPREADSHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]

def get_data():
    """Mengambil data terbaru dari Google Sheets"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df = conn.read(worksheet="Data", ttl=0) # ttl=0 agar selalu ambil data fresh
        # Pastikan kolom formatnya benar jika sheet masih kosong
        if df.empty:
            df = pd.DataFrame(columns=["Nama", "Skor_Pretest", "Skor_Posttest", "Waktu"])
        return df
    except Exception as e:
        st.error("Gagal membaca database. Pastikan koneksi internet aman.")
        return pd.DataFrame(columns=["Nama", "Skor_Pretest", "Skor_Posttest", "Waktu"])

def update_data(df_baru):
    """Menimpa data di Google Sheets dengan data baru"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet="Data", data=df_baru)

# --- Data Soal ---
kunci_jawaban = {
    "q1": "A", "q2": "B", "q3": "C", "q4": "A", "q5": "D",
    "q6": "B", "q7": "C", "q8": "A", "q9": "D", "q10": "B"
}

def hitung_skor(jawaban_user):
    skor = 0
    for key, val in jawaban_user.items():
        if val and val.startswith(kunci_jawaban[key]):
            skor += 1
    return skor * 10

def tampilkan_soal(prefix):
    st.write("Jawablah pertanyaan berikut:")
    jawaban_user = {}
    # Contoh 3 soal (Silakan lengkapi jadi 10 sesuai kebutuhan)
    jawaban_user["q1"] = st.radio("1. Soal nomor satu?", ["A. Jawaban A", "B. Jawaban B", "C. Jawaban C", "D. Jawaban D"], key=f"{prefix}_1")
    jawaban_user["q2"] = st.radio("2. Soal nomor dua?", ["A. Jawaban A", "B. Jawaban B", "C. Jawaban C", "D. Jawaban D"], key=f"{prefix}_2")
    jawaban_user["q3"] = st.radio("3. Soal nomor tiga?", ["A. Jawaban A", "B. Jawaban B", "C. Jawaban C", "D. Jawaban D"], key=f"{prefix}_3")
    
    # Dummy soal 4-10
    for i in range(4, 11):
         jawaban_user[f"q{i}"] = st.radio(f"{i}. Soal nomor {i}...", ["A. Ops", "B. Ops", "C. Ops", "D. Ops"], key=f"{prefix}_{i}")
    return jawaban_user

# --- Logika Utama ---
def main():
    st.title("Ujian Online SMP")
    
    if 'page' not in st.session_state: st.session_state['page'] = 'login'
    if 'nama_user' not in st.session_state: st.session_state['nama_user'] = ''
    if 'score_pre' not in st.session_state: st.session_state['score_pre'] = 0

    # Halaman Login
    if st.session_state['page'] == 'login':
        st.subheader("Login Siswa")
        nama_input = st.text_input("Masukkan Nama Lengkap Anda:")
        
        if st.button("Masuk"):
            if not nama_input:
                st.warning("Nama tidak boleh kosong.")
                return

            df = get_data()
            
            # Cek apakah nama sudah ada (Case insensitive)
            if not df.empty and nama_input.lower() in df['Nama'].str.lower().values:
                st.error("Nama ini sudah terdaftar! Harap gunakan nama lain atau hubungi guru.")
            else:
                st.session_state['nama_user'] = nama_input
                st.session_state['page'] = 'pretest'
                st.rerun()

    # Halaman Pre-Test
    elif st.session_state['page'] == 'pretest':
        st.subheader(f"Pre-Test: {st.session_state['nama_user']}")
        jawaban = tampilkan_soal("pre")
        
        if st.button("Kirim Jawaban Pre-Test"):
            skor = hitung_skor(jawaban)
            st.session_state['score_pre'] = skor
            
            # Simpan Data Awal ke Google Sheet
            df = get_data()
            new_row = pd.DataFrame([{
                "Nama": st.session_state['nama_user'],
                "Skor_Pretest": skor,
                "Skor_Posttest": 0, # Belum post test
                "Waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            df_combined = pd.concat([df, new_row], ignore_index=True)
            update_data(df_combined)
            
            st.session_state['page'] = 'materi'
            st.rerun()

    # Halaman Materi
    elif st.session_state['page'] == 'materi':
        st.subheader(f"Hasil Pre-Test Anda: {st.session_state['score_pre']}")
        st.markdown("---")
        st.info("Silakan pelajari materi di bawah ini sebelum lanjut ke Post-Test.")
        st.write("ISI MATERI PEMBELAJARAN DISINI...")
        
        if st.button("Lanjut ke Post-Test"):
            st.session_state['page'] = 'posttest'
            st.rerun()

    # Halaman Post-Test
    elif st.session_state['page'] == 'posttest':
        st.subheader("Post-Test")
        jawaban = tampilkan_soal("post")
        
        if st.button("Kirim Jawaban Post-Test"):
            skor_akhir = hitung_skor(jawaban)
            
            # Update Nilai Post-Test di Google Sheets
            df = get_data()
            # Cari baris dengan nama user, lalu update skor posttest
            idx = df.index[df['Nama'] == st.session_state['nama_user']].tolist()
            if idx:
                df.at[idx[0], 'Skor_Posttest'] = skor_akhir
                update_data(df)
            
            st.session_state['score_post'] = skor_akhir
            st.session_state['page'] = 'final'
            st.rerun()

    # Halaman Final
    elif st.session_state['page'] == 'final':
        st.success("Terima kasih telah mengerjakan!")
        st.write(f"Nama: {st.session_state['nama_user']}")
        st.write(f"Pre-Test: {st.session_state['score_pre']}")
        st.write(f"Post-Test: {st.session_state['score_post']}")
        if st.button("Selesai (Kembali ke Awal)"):
            st.session_state.clear()
            st.rerun()

if __name__ == '__main__':
    main()