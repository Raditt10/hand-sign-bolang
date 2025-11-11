import cv2 
import mediapipe as mp 
import numpy as np 
import pyttsx3
import os 
import threading 
import time
import queue
import difflib

# Inisialisasi TTS
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150) 
tts_engine.setProperty('volume', 0.9) 

# Kamus kata umum
KATA_UMUM = [
    "HALO", "HAI", "TERIMA", "KASIH", "TOLONG", "MAAF", "YA", "TIDAK",
    "BANTU", "BAIK", "BURUK", "PAGI", "SIANG", "SORE", "MALAM",
    "SELAMAT", "TINGGAL", "SAMPAI", "JUMPA", "NAMA", "SAYA", "KAMU",
    "APA", "SIAPA", "DIMANA", "KAPAN", "MENGAPA", "BAGAIMANA",
    "BISA", "MAU", "PERLU", "PUNYA", "AKAN", "SUDAH",
    "PERGI", "DATANG", "LIHAT", "DENGAR", "BICARA", "KATA",
    "MAKAN", "MINUM", "TIDUR", "KERJA", "MAIN", "BELAJAR",
    "SENANG", "SEDIH", "MARAH", "LELAH", "LAPAR", "HAUS",
    "PANAS", "DINGIN", "BESAR", "KECIL", "CEPAT", "LAMBAT", "BARU", "LAMA"
]

# ===========================================
# 📝 Prediktor Kata
# ===========================================
class PrediktorKata:
    def __init__(self, kamus):
        self.kamus = sorted(kamus)
        self.kata_sekarang = []
        self.kata_prediksi = []
        
    def tambah_huruf(self, huruf):
        """Menambahkan huruf dan memprediksi kata"""
        if huruf.isalpha():
            self.kata_sekarang.append(huruf.upper())
            self._perbarui_prediksi()
    
    def hapus_huruf(self):
        """Menghapus huruf terakhir"""
        if self.kata_sekarang:
            self.kata_sekarang.pop()
            self._perbarui_prediksi()
    
    def _perbarui_prediksi(self):
        """Update prediksi kata berdasarkan huruf saat ini"""
        saat_ini = ''.join(self.kata_sekarang)
        if not saat_ini:
            self.kata_prediksi = []
            return
        
        # Cari kata yang dimulai dengan huruf yang diketik
        cocok = [kata for kata in self.kamus if kata.startswith(saat_ini)]
        
        # Jika tidak ada yang cocok, cari yang mirip
        if not cocok and len(saat_ini) > 2:
            cocok = difflib.get_close_matches(saat_ini, self.kamus, n=3, cutoff=0.6)
        
        self.kata_prediksi = cocok[:5]  # 5 prediksi teratas
    
    def ambil_kata_sekarang(self):
        """Mendapatkan kata yang sedang diketik"""
        return ''.join(self.kata_sekarang)
    
    def ambil_prediksi(self):
        """Mendapatkan prediksi kata"""
        return self.kata_prediksi
    
    def lengkapi_kata(self, kata=None):
        """Melengkapi kata dengan prediksi pertama atau kata tertentu"""
        if kata:
            self.kata_sekarang = list(kata)
        elif self.kata_prediksi:
            self.kata_sekarang = list(self.kata_prediksi[0])
        self._perbarui_prediksi()
        return ''.join(self.kata_sekarang)
    
    def bersihkan(self):
        """Bersihkan kata saat ini"""
        self.kata_sekarang = []
        self.kata_prediksi = []

# ===========================================
# 📝 Pembuat Kalimat dengan Tanda Baca Otomatis
# ===========================================
class PembuatKalimat:
    def __init__(self):
        self.kata_kata = []
        self.kalimat_sekarang = ""
        
    def tambah_kata(self, kata):
        """Menambahkan kata ke kalimat"""
        if kata.strip():
            self.kata_kata.append(kata.upper())
            self._bangun_kalimat()
    
    def _bangun_kalimat(self):
        """Membangun kalimat dengan tanda baca otomatis"""
        if not self.kata_kata:
            self.kalimat_sekarang = ""
            return
        
        # Buat kalimat
        kalimat = ' '.join(self.kata_kata)
        
        # Kapitalisasi otomatis
        kalimat = kalimat.capitalize()
        
        # Tanda baca otomatis berdasarkan kata terakhir
        kata_terakhir = self.kata_kata[-1].upper()
        
        # Kata tanya
        kata_tanya = ["APA", "SIAPA", "DIMANA", "KAPAN", "MENGAPA", "BAGAIMANA", "BISA"]
        if self.kata_kata[0].upper() in kata_tanya:
            if not kalimat.endswith('?'):
                kalimat += '?'
        # Salam/perpisahan
        elif kata_terakhir in ["HALO", "HAI", "SELAMAT", "TINGGAL", "TERIMA", "KASIH", "MAAF"]:
            if not kalimat.endswith('!'):
                kalimat += '!'
        # Pernyataan biasa
        else:
            if not kalimat.endswith('.'):
                kalimat += '.'
        
        self.kalimat_sekarang = kalimat
    
    def ambil_kalimat(self):
        """Mendapatkan kalimat saat ini"""
        return self.kalimat_sekarang
    
    def hapus_kata_terakhir(self):
        """Menghapus kata terakhir"""
        if self.kata_kata:
            self.kata_kata.pop()
            self._bangun_kalimat()
    
    def bersihkan(self):
        """Bersihkan kalimat"""
        self.kata_kata = []
        self.kalimat_sekarang = ""

# ===========================================
# 🗣 Manajemen Antrian Suara
# ===========================================
antrian_suara = queue.Queue()
sedang_berbicara = False

nama_pengguna = "Pengguna"
huruf_terdeteksi_terakhir = ""
waktu_konfirmasi_huruf = 0
durasi_konfirmasi_huruf = 1.5

# Inisialisasi prediktor kata dan pembuat kalimat
prediktor_kata = PrediktorKata(KATA_UMUM)
pembuat_kalimat = PembuatKalimat()

# ===========================================
# 🗣 Fungsi Text-to-Speech
# ===========================================
def pekerja_suara():
    """Worker thread untuk text-to-speech menggunakan pyttsx3"""
    global sedang_berbicara
    while True:
        teks = antrian_suara.get()
        if teks is None:
            break
        try:
            sedang_berbicara = True
            print(f"🔊 Berbicara: '{teks}'")
            tts_engine.say(teks)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"❌ Error TTS: {e}")
        finally:
            sedang_berbicara = False
            antrian_suara.task_done()

teks_terakhir = ""
waktu_bicara_terakhir = 0

def mungkin_bicara(teks):
    """Bicara dengan TTS jika diperlukan"""
    global teks_terakhir, waktu_bicara_terakhir
    if teks != teks_terakhir and teks != "-":
        sekarang = time.time()
        if sekarang - waktu_bicara_terakhir > 1.5:
            try:
                print(f"📢 Menambah ke antrian TTS: '{teks}'")
                antrian_suara.put(teks)
                waktu_bicara_terakhir = sekarang
                teks_terakhir = teks
            except Exception as e:
                print(f"❌ Error menambah antrian TTS: {e}")

# ===========================================
# ✋ Inisialisasi Mediapipe
# ===========================================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# ===========================================
# 🎨 Fungsi Pembantu UI
# ===========================================
def buat_background_sekolah(lebar=1280, tinggi=720):
    """Membuat background dengan nuansa pendidikan"""
    bg = np.ones((tinggi, lebar, 3), dtype=np.uint8)
    
    # Gradient background
    for i in range(tinggi):
        rasio = i / tinggi
        b = int(180 - (rasio * 80))
        g = int(140 + (rasio * 60))
        r = int(50 + (rasio * 30))
        bg[i, :] = [b, g, r]
    
    # Grid pattern
    for i in range(0, lebar, 40):
        cv2.line(bg, (i, 0), (i, tinggi), (255, 255, 255), 1, cv2.LINE_AA)
    for i in range(0, tinggi, 40):
        cv2.line(bg, (0, i), (lebar, i), (255, 255, 255), 1, cv2.LINE_AA)
    
    # Overlay semi-transparan
    overlay = bg.copy()
    cv2.rectangle(overlay, (0, 0), (lebar, tinggi), (20, 40, 60), -1)
    bg = cv2.addWeighted(bg, 0.7, overlay, 0.3, 0)
    
    # Header bar
    cv2.rectangle(bg, (0, 0), (lebar, 80), (50, 150, 255), -1)
    cv2.line(bg, (0, 80), (lebar, 80), (100, 180, 255), 5)
    
    # Footer bar
    cv2.rectangle(bg, (0, tinggi-60), (lebar, tinggi), (255, 180, 50), -1)
    cv2.line(bg, (0, tinggi-60), (lebar, tinggi-60), (255, 200, 100), 5)
    
    return bg

def tambah_teks_dengan_background(frame, teks, posisi, skala_font=0.8, warna=(255, 255, 255), 
                                   warna_bg=(50, 50, 50), padding=10, ketebalan=2):
    """Menambahkan teks dengan background"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (lebar_teks, tinggi_teks), baseline = cv2.getTextSize(teks, font, skala_font, ketebalan)
    
    x, y = posisi
    pt1 = (x - padding, y - tinggi_teks - padding)
    pt2 = (x + lebar_teks + padding, y + baseline + padding)
    
    overlay = frame.copy()
    cv2.rectangle(overlay, pt1, pt2, warna_bg, -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
    cv2.rectangle(frame, pt1, pt2, warna, 2)
    cv2.putText(frame, teks, (x, y), font, skala_font, warna, ketebalan, cv2.LINE_AA)
    
    return frame

# ===========================================
# ✋ Fungsi Deteksi Tangan
# ===========================================
def ambil_status_jari(landmark_tangan):
    """Mendapatkan status jari (terbuka/tertutup)"""
    jari = []
    
    # Jempol
    if landmark_tangan.landmark[4].x < landmark_tangan.landmark[3].x:
        jari.append(1)
    else:
        jari.append(0)
    
    # Jari lainnya
    for ujung in [8, 12, 16, 20]:
        if landmark_tangan.landmark[ujung].y < landmark_tangan.landmark[ujung - 2].y:
            jari.append(1)
        else:
            jari.append(0)
    
    return jari

def hitung_jarak(p1, p2):
    """Menghitung jarak euclidean"""
    return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

def hitung_sudut(p1, p2, p3):
    """Menghitung sudut antara tiga titik"""
    v1 = np.array([p1.x - p2.x, p1.y - p2.y])
    v2 = np.array([p3.x - p2.x, p3.y - p2.y])
    
    cos_sudut = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
    sudut = np.arccos(np.clip(cos_sudut, -1.0, 1.0))
    return np.degrees(sudut)

# ===========================================
# 🔤 Klasifikasi Huruf
# ===========================================
def klasifikasi_huruf(jari, landmarks):
    """Klasifikasi gesture bahasa isyarat menjadi huruf"""
    
    # A - Semua jari tertutup, jempol di samping
    if jari == [0, 0, 0, 0, 0]:
        jempol_samping = landmarks[4].x < landmarks[2].x or landmarks[4].x > landmarks[17].x
        if jempol_samping:
            return "A"
    
    # B - Jari tengah, manis, kelingking terbuka, jempol dan telunjuk tertutup
    if jari == [0, 0, 1, 1, 1]:
        jempol_tertekuk = landmarks[4].y > landmarks[3].y
        if jempol_tertekuk:
            return "B"
    
    # C - Jempol dan jari membentuk huruf C
    if jari == [1, 0, 0, 0, 0]:
        jarak_kurva = hitung_jarak(landmarks[4], landmarks[8])
        if 0.08 < jarak_kurva < 0.15:
            return "C"
    
    # D - Telunjuk dan jempol membentuk lingkaran
    if jari == [1, 1, 0, 0, 0]:
        cek_lingkaran = hitung_jarak(landmarks[4], landmarks[12]) < 0.05
        if cek_lingkaran:
            return "D"
    
    # E - Semua jari tertutup, jempol di depan
    if jari == [0, 0, 0, 0, 0]:
        jempol_depan = landmarks[4].x > landmarks[5].x and landmarks[4].x < landmarks[17].x
        if jempol_depan:
            return "E"
    
    # F - Jempol dan telunjuk membentuk lingkaran, jari lain terbuka
    if jari == [0, 0, 1, 1, 1] or jari == [1, 0, 1, 1, 1]:
        tanda_ok = hitung_jarak(landmarks[4], landmarks[8]) < 0.05
        if tanda_ok:
            return "F"
    
    # G - Telunjuk dan jempol horizontal menunjuk ke samping
    if jari == [1, 1, 0, 0, 0]:
        horizontal = abs(landmarks[8].y - landmarks[4].y) < 0.05
        menunjuk_samping = abs(landmarks[8].x - landmarks[0].x) > 0.1
        if horizontal and menunjuk_samping:
            return "G"
    
    # H - Telunjuk dan jari tengah horizontal, berdekatan
    if jari == [0, 1, 1, 0, 0]:
        horizontal = abs(landmarks[8].y - landmarks[12].y) < 0.03
        dekat = abs(landmarks[8].x - landmarks[12].x) < 0.03
        if horizontal and dekat:
            return "H"
    
    # I - Hanya kelingking terbuka
    if jari == [0, 0, 0, 0, 1]:
        lainnya_tertutup = all([
            landmarks[8].y > landmarks[6].y,
            landmarks[12].y > landmarks[10].y,
            landmarks[16].y > landmarks[14].y
        ])
        if lainnya_tertutup:
            return "I"
    
    # K - Telunjuk, jempol, jari tengah dengan sudut tertentu
    if jari == [1, 1, 1, 0, 0]:
        sudut_tengah = hitung_sudut(landmarks[12], landmarks[11], landmarks[9])
        if 30 < sudut_tengah < 60:
            return "K"
    
    # L - Jempol horizontal, telunjuk vertikal
    if jari == [1, 1, 0, 0, 0]:
        jempol_horizontal = abs(landmarks[4].y - landmarks[2].y) < 0.05
        telunjuk_vertikal = landmarks[8].y < landmarks[6].y
        if jempol_horizontal and telunjuk_vertikal:
            return "L"
    
    # M - Tiga jari di atas jempol
    if jari == [1, 0, 0, 0, 0]:
        tiga_di_atas = all([
            landmarks[8].y < landmarks[4].y,
            landmarks[12].y < landmarks[4].y,
            landmarks[16].y < landmarks[4].y
        ])
        if tiga_di_atas:
            return "M"
    
    # N - Dua jari di atas jempol
    if jari == [1, 0, 0, 0, 0]:
        dua_di_atas = (landmarks[8].y < landmarks[4].y and 
                       landmarks[12].y < landmarks[4].y and
                       landmarks[16].y > landmarks[4].y)
        if dua_di_atas:
            return "N"
    
    # O - Semua jari membentuk lingkaran
    if jari == [1, 1, 1, 1, 1]:
        jarak_lingkaran = hitung_jarak(landmarks[4], landmarks[8])
        if jarak_lingkaran < 0.06:
            return "O"
    
    # P - Telunjuk, jempol, jari tengah menunjuk ke bawah
    if jari == [1, 1, 1, 0, 0]:
        menunjuk_bawah = landmarks[8].y > landmarks[5].y
        if menunjuk_bawah:
            return "P"
    
    # Q - Telunjuk dan jempol menunjuk ke bawah
    if jari == [1, 1, 0, 0, 0]:
        menunjuk_bawah = landmarks[8].y > landmarks[5].y
        if menunjuk_bawah:
            return "Q"
    
    # R - Telunjuk dan jari tengah bersilangan
    if jari == [0, 1, 1, 0, 0]:
        bersilang = abs(landmarks[8].x - landmarks[12].x) < 0.02
        if bersilang:
            return "R"
    
    # S - Kepalan dengan jempol di depan
    if jari == [0, 0, 0, 0, 0]:
        jempol_depan = landmarks[4].z < landmarks[8].z
        if jempol_depan:
            return "S"
    
    # T - Jempol di antara telunjuk dan jari tengah
    if jari == [1, 0, 0, 0, 0]:
        jempol_diantara = (landmarks[4].y > landmarks[8].y and 
                           landmarks[4].y < landmarks[5].y)
        if jempol_diantara:
            return "T"
    
    # U - Telunjuk dan jari tengah berdekatan, vertikal
    if jari == [0, 1, 1, 0, 0]:
        bersama = abs(landmarks[8].x - landmarks[12].x) < 0.03
        vertikal = landmarks[8].y < landmarks[6].y
        if bersama and vertikal:
            return "U"
    
    # V - Telunjuk dan jari tengah terpisah membentuk V
    if jari == [0, 1, 1, 0, 0]:
        terpisah = abs(landmarks[8].x - landmarks[12].x) > 0.05
        if terpisah:
            return "V"
    
    # W - Tiga jari (telunjuk, tengah, manis) terbuka
    if jari == [0, 1, 1, 1, 0]:
        semua_atas = all([
            landmarks[8].y < landmarks[6].y,
            landmarks[12].y < landmarks[10].y,
            landmarks[16].y < landmarks[14].y
        ])
        if semua_atas:
            return "W"
    
    # X - Telunjuk menekuk seperti kait
    if jari == [0, 1, 0, 0, 0]:
        menekuk = landmarks[8].y > landmarks[6].y
        if menekuk:
            return "X"
    
    # Y - Jempol dan kelingking terbuka
    if jari == [1, 0, 0, 0, 1]:
        kelingking_atas = landmarks[20].y < landmarks[18].y
        jempol_keluar = landmarks[4].x < landmarks[2].x or landmarks[4].x > landmarks[17].x
        if kelingking_atas and jempol_keluar:
            return "Y"
    
    # Z - Telunjuk terbuka untuk menggambar Z
    if jari == [0, 1, 0, 0, 0]:
        telunjuk_terbuka = landmarks[8].y < landmarks[6].y
        if telunjuk_terbuka:
            return "Z"
    
    return "-"

def tambah_huruf_ke_kata(huruf):
    """Menambahkan huruf ke prediktor kata"""
    global huruf_terdeteksi_terakhir, waktu_konfirmasi_huruf
    
    waktu_sekarang = time.time()
    
    if huruf == huruf_terdeteksi_terakhir:
        if waktu_sekarang - waktu_konfirmasi_huruf >= durasi_konfirmasi_huruf:
            prediktor_kata.tambah_huruf(huruf)
            mungkin_bicara(huruf)
            print(f"✅ Huruf ditambahkan: {huruf} | Kata: {prediktor_kata.ambil_kata_sekarang()}")
            waktu_konfirmasi_huruf = waktu_sekarang + 2
    else:
        huruf_terdeteksi_terakhir = huruf
        waktu_konfirmasi_huruf = waktu_sekarang

# ===========================================
# 🎯 Aplikasi Utama
# ===========================================
def main():
    """Fungsi utama aplikasi"""
    global nama_pengguna

    print("\n" + "="*60)
    print("🤟 PENGENALAN BAHASA ISYARAT - PEMBUAT KATA & KALIMAT OTOMATIS")
    print("="*60)
    
    input_pengguna = input("Masukkan nama Anda: ").strip()
    if input_pengguna:
        nama_pengguna = input_pengguna
    print(f"👋 Halo {nama_pengguna}! Mari kita mulai...\n")
    print("📝 Kontrol:")
    print("  - Q: Keluar")
    print("  - SPASI: Selesaikan kata & tambahkan ke kalimat")
    print("  - TAB: Lengkapi otomatis dengan prediksi")
    print("  - BACKSPACE: Hapus huruf terakhir")
    print("  - DELETE: Hapus kata terakhir")
    print("  - ENTER: Ucapkan kalimat dan simpan")
    print("  - C: Bersihkan semua")
    print("  - 1-5: Pilih prediksi kata\n")

    thread_suara = threading.Thread(target=pekerja_suara, daemon=True)
    thread_suara.start()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Tidak dapat mengakses kamera")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    template_bg = buat_background_sekolah(1280, 720)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error: Tidak dapat membaca frame")
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            if template_bg.shape[:2] != (h, w):
                background = cv2.resize(template_bg, (w, h))
            else:
                background = template_bg.copy()
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            alpha = 0.6
            frame = cv2.addWeighted(frame, alpha, background, 1-alpha, 0)

            huruf_terdeteksi = "-"
            
            if results.multi_hand_landmarks:
                for landmark_tangan in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(
                        frame, 
                        landmark_tangan, 
                        mp_hands.HAND_CONNECTIONS,
                        mp_draw.DrawingSpec(color=(0, 255, 128), thickness=3, circle_radius=5),
                        mp_draw.DrawingSpec(color=(255, 128, 0), thickness=3)
                    )
                    
                    jari = ambil_status_jari(landmark_tangan)
                    huruf_terdeteksi = klasifikasi_huruf(jari, landmark_tangan)
                    
                    if huruf_terdeteksi != "-":
                        tambah_huruf_ke_kata(huruf_terdeteksi)

            # Header
            tambah_teks_dengan_background(frame, "PEMBUAT KATA & KALIMAT OTOMATIS", 
                                          (w//2 - 350, 50), 1.2, (255, 255, 255), 
                                          (255, 150, 50), 15, 3)

            # Kotak Huruf Terdeteksi
            if huruf_terdeteksi != "-":
                lebar_kotak, tinggi_kotak = 150, 150
                x_kotak, y_kotak = w - lebar_kotak - 30, 100
                
                overlay = frame.copy()
                cv2.rectangle(overlay, (x_kotak, y_kotak), 
                            (x_kotak + lebar_kotak, y_kotak + tinggi_kotak), 
                            (0, 255, 128), -1)
                cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
                cv2.rectangle(frame, (x_kotak, y_kotak), 
                            (x_kotak + lebar_kotak, y_kotak + tinggi_kotak), 
                            (255, 255, 255), 4)
                
                cv2.putText(frame, huruf_terdeteksi, (x_kotak + 30, y_kotak + 90), 
                          cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 6)

            # Kotak Kata Saat Ini
            kata_sekarang = prediktor_kata.ambil_kata_sekarang()
            y_kata = 280
            
            overlay = frame.copy()
            cv2.rectangle(overlay, (20, y_kata - 50), (w - 20, y_kata + 30), 
                        (40, 40, 80), -1)
            cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
            cv2.rectangle(frame, (20, y_kata - 50), (w - 20, y_kata + 30), 
                        (100, 200, 255), 3)
            
            cv2.putText(frame, "KATA SAAT INI:", (30, y_kata - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 200, 255), 2)
            
            tampil_kata = kata_sekarang if kata_sekarang else "[mengetik...]"
            cv2.putText(frame, tampil_kata, (30, y_kata + 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            # Kotak Prediksi Kata
            prediksi = prediktor_kata.ambil_prediksi()
            if prediksi:
                y_prediksi = y_kata + 70
                tambah_teks_dengan_background(frame, "PREDIKSI KATA:", 
                                              (30, y_prediksi - 30), 0.7, (100, 200, 255), 
                                              (40, 40, 80), 8, 2)
                for i, kata_prediksi in enumerate(prediksi):
                    teks_prediksi = f"{i+1}. {kata_prediksi}"
                    tambah_teks_dengan_background(frame, teks_prediksi, 
                                                  (50, y_prediksi + i*40), 0.7, (255, 255, 255), 
                                                  (60, 60, 100), 6, 2)
            # Kotak Kalimat Saat Ini
            quote_kalimat = pembuat_kalimat.ambil_kalimat()
            y_kalimat = h - 100
            overlay = frame.copy()
            cv2.rectangle(overlay, (20, y_kalimat - 50), (w - 20, y_kalimat + 30), 
                        (80, 40, 40), -1)
            cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
            cv2.rectangle(frame, (20, y_kalimat - 50), (w - 20, y_kalimat + 30), 
                        (255, 180, 100), 3)
            cv2.putText(frame, "KALIMAT SAAT INI:", (30, y_kalimat - 20),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 180, 100), 2)
            tampil_kalimat = quote_kalimat if quote_kalimat else "[kosong]"
            cv2.putText(frame, tampil_kalimat, (30, y_kalimat + 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
            cv2.imshow("Pengenalan Bahasa Isyarat - Pembuat Kata & Kalimat Otomatis", frame)
            key = cv2.waitKey(1) & 0xFF