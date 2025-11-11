import cv2 
import mediapipe as mp 
import numpy as np 
from gtts import gTTS 
try:
    from playsound import playsound
    playsound_available = True
except Exception:
    # playsound may be installed but still fail at runtime; keep flag and fallback later
    playsound_available = False
    def playsound(_):
        raise RuntimeError("playsound not available")
import os 
import threading 
import time
import queue
import subprocess
# note: flask was previously imported but not used; removed to avoid unnecessary import


# ===========================================
# 🌍 Daftar Bahasa yang Didukung
# ===========================================
bahasa_map = {
    "1": ("id", "indonesia", "🇮🇩"),
    "2": ("en", "english", "🇺🇸"),
    "3": ("ja", "japanese", "🇯🇵"),
    "4": ("es", "spanish", "🇪🇸"),
    "5": ("jw", "javanese", "🏴"),
    "6": ("su", "sundanese", "🏴"),
    "7": ("it", "italian", "🇮🇹"),
    "8": ("zh-CN", "chinese", "🇨🇳"),
    "9": ("th", "thai", "🇹🇭"),
    "10": ("ar", "arabic", "🇸🇦"),
    "11": ("ko", "korean", "🇰🇷"),
    "12": ("hi", "hindi", "🇮🇳")
}

# Queue untuk manajemen suara
speech_queue = queue.Queue()
is_speaking = False

# Module-level defaults (will be set in main())
bahasa = None
mode = None
bendera = None
user_name = "Teman Hebat"

def tampilkan_menu():
    print("\n" + "="*50)
    print("🌍 PILIH BAHASA SUARA")
    print("="*50)
    for key, val in bahasa_map.items():
        print(f"{key}. {val[1].capitalize()} {val[2]}")
    print()

def pilih_bahasa():
    tampilkan_menu()
    while True:
        pilihan = input("Masukkan nomor bahasa (1-12): ").strip()
        if pilihan in bahasa_map:
            return bahasa_map[pilihan]
        else:
            print("❌ Pilihan tidak valid. Silakan pilih 1-12.")

# NOTE: Language selection and user input are moved into main() so importing this
# module doesn't start interactive prompts or access the camera automatically.

# ===========================================
# 🗣 Fungsi bicara dengan penghapusan cache
# ===========================================
def speech_worker():
    """Worker thread untuk memutar suara dan menghapus cache"""
    global is_speaking
    while True:
        filename = speech_queue.get()
        if filename is None:  # Signal to stop
            break
        try:
            is_speaking = True
            # Try primary playback
            playsound(filename)
            # Hapus file cache setelah diputar (hanya jika playback succeeded)
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                    print(f"🗑 Cache dihapus: {filename}")
                except Exception as e_del:
                    print(f"⚠️ Gagal menghapus cache: {e_del}")
        except Exception as e:
            # Primary playback failed. Try graceful fallback to open with system default player
            print(f"❌ Error saat memutar suara: \n    {e}")
            try:
                if os.name == 'nt':
                    # On Windows, open with default associated application (non-blocking)
                    os.startfile(filename)
                    print(f"ℹ️ Fallback: membuka {filename} dengan aplikasi default. File tidak dihapus otomatis.")
                else:
                    # Try xdg-open (Linux) or open (macOS)
                    opener = 'xdg-open' if os.name == 'posix' else 'open'
                    subprocess.Popen([opener, filename])
                    print(f"ℹ️ Fallback: membuka {filename} dengan '{opener}'. File tidak dihapus otomatis.")
            except Exception as e2:
                print(f"⚠️ Fallback playback juga gagal: {e2}")
        finally:
            is_speaking = False
            speech_queue.task_done()

# The speech worker thread will be started inside main().

last_text = ""
last_speak_time = 0

def maybe_speak(text):
    global last_text, last_speak_time
    if text != last_text and text != "-":
        now = time.time()
        if now - last_speak_time > 3:  # jeda minimal 3 detik
            try:
                # Buat nama file cache yang unik
                filename = f"cache_{bahasa}_{hash(text) & 0xFFFFFFFF}.mp3"
                
                # Jika file belum ada, buat dulu
                if not os.path.exists(filename):
                    tts = gTTS(text=text, lang=bahasa)
                    tts.save(filename)
                    print(f"💾 Cache disimpan: {filename}")
                
                # Tambahkan ke queue untuk diputar
                speech_queue.put(filename)
                last_speak_time = now
                last_text = text
                
            except Exception as e:
                print(f"❌ Error membuat TTS: {e}")

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
# ✋ Deteksi Jari
# ===========================================
def get_finger_states(hand_landmarks):
    tips = [4, 8, 12, 16, 20]  # ujung jari: thumb, index, middle, ring, pinky
    fingers = []
    
    # Deteksi thumb (berbeda karena orientasinya horizontal)
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        fingers.append(1)  # thumb terbuka
    else:
        fingers.append(0)  # thumb tertutup
    
    # Deteksi jari lainnya (berdasarkan posisi Y)
    for tip in [8, 12, 16, 20]:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers.append(1)  # jari terbuka
        else:
            fingers.append(0)  # jari tertutup
    
    return fingers

# ===========================================
# 💬 Klasifikasi Gesture ke Kalimat
# ===========================================
def classify_letter(fingers):
    # 🇮🇩 Bahasa Indonesia
    if mode == "indonesia":
        if fingers == [1, 0, 0, 0, 1]: return f"Nama saya {user_name}"
        elif fingers == [1, 1, 1, 1, 1]: return "Halo"
        elif fingers == [1, 1, 1, 0, 0]: return "Saya"
        elif fingers == [0, 1, 0, 1, 0]: return "Apa kabar"
        elif fingers == [0, 0, 1, 1, 1]: return "Terima kasih"
        elif fingers == [1, 1, 0, 0, 1]: return "Sampai jumpa"
        elif fingers == [1, 0, 1, 1, 0]: return "Selamat pagi"
        elif fingers == [0, 1, 1, 0, 1]: return "Selamat malam"
        elif fingers == [1, 0, 1, 0, 0]: return "Aku senang bertemu kamu"
        elif fingers == [0, 1, 1, 1, 0]: return "Semangat terus!"
        elif fingers == [0, 0, 0, 0, 1]: return "Tolong"
        elif fingers == [1, 0, 0, 0, 0]: return "Ya"
        elif fingers == [0, 1, 0, 0, 0]: return "Tidak"
        elif fingers == [0, 0, 1, 0, 0]: return "Maaf"
        elif fingers == [0, 0, 0, 1, 0]: return "Saya lapar"
    
    # 🇺🇸 English
    elif mode == "english":
        if fingers == [1, 0, 0, 0, 1]: return f"My name is {user_name}"
        elif fingers == [1, 1, 1, 1, 1]: return "Hello"
        elif fingers == [1, 1, 1, 0, 0]: return "I am"
        elif fingers == [0, 1, 0, 1, 0]: return "How are you"
        elif fingers == [0, 0, 1, 1, 1]: return "Thank you"
        elif fingers == [1, 1, 0, 0, 1]: return "Goodbye"
        elif fingers == [1, 0, 1, 1, 0]: return "Good morning"
        elif fingers == [0, 1, 1, 0, 1]: return "Good night"
        elif fingers == [1, 0, 1, 0, 0]: return "Nice to meet you"
        elif fingers == [0, 1, 1, 1, 0]: return "Keep going!"
        elif fingers == [0, 0, 0, 0, 1]: return "Help"
        elif fingers == [1, 0, 0, 0, 0]: return "Yes"
        elif fingers == [0, 1, 0, 0, 0]: return "No"
        elif fingers == [0, 0, 1, 0, 0]: return "Sorry"
        elif fingers == [0, 0, 0, 1, 0]: return "I am hungry"
    
    # 🇯🇵 Japanese
    elif mode == "japanese":
        if fingers == [1, 0, 0, 0, 1]: return f"わたしのなまえは {user_name} です"
        elif fingers == [1, 1, 1, 1, 1]: return "こんにちは"  # Konnichiwa
        elif fingers == [1, 1, 1, 0, 0]: return "わたし"  # Watashi
        elif fingers == [0, 1, 0, 1, 0]: return "おげんきですか"  # Ogenki desu ka
        elif fingers == [0, 0, 1, 1, 1]: return "ありがとう"  # Arigatou
        elif fingers == [1, 1, 0, 0, 1]: return "さようなら"  # Sayonara
        elif fingers == [1, 0, 1, 1, 0]: return "おはよう"  # Ohayou
        elif fingers == [0, 1, 1, 0, 1]: return "おやすみ"  # Oyasumi
        elif fingers == [1, 0, 1, 0, 0]: return "はじめまして"  # Hajimemashite
        elif fingers == [0, 1, 1, 1, 0]: return "がんばって"  # Ganbatte!
        elif fingers == [0, 0, 0, 0, 1]: return "たすけて"  # Tasukete
        elif fingers == [1, 0, 0, 0, 0]: return "はい"  # Hai
        elif fingers == [0, 1, 0, 0, 0]: return "いいえ"  # Iie
        elif fingers == [0, 0, 1, 0, 0]: return "ごめんなさい"  # Gomennasai
        elif fingers == [0, 0, 0, 1, 0]: return "おなかがすきました"  # Onaka ga sukimashita
    
    # 🇪🇸 Spanish
    elif mode == "spanish":
        if fingers == [1, 0, 0, 0, 1]: return f"Mi nombre es {user_name}"
        elif fingers == [1, 1, 1, 1, 1]: return "Hola"
        elif fingers == [1, 1, 1, 0, 0]: return "Yo soy"
        elif fingers == [0, 1, 0, 1, 0]: return "Cómo estás"
        elif fingers == [0, 0, 1, 1, 1]: return "Gracias"
        elif fingers == [1, 1, 0, 0, 1]: return "Adiós"
        elif fingers == [1, 0, 1, 1, 0]: return "Buenos días"
        elif fingers == [0, 1, 1, 0, 1]: return "Buenas noches"
        elif fingers == [1, 0, 1, 0, 0]: return "Encantado de conocerte"
        elif fingers == [0, 1, 1, 1, 0]: return "Sigue adelante"
        elif fingers == [0, 0, 0, 0, 1]: return "Ayuda"
        elif fingers == [1, 0, 0, 0, 0]: return "Sí"
        elif fingers == [0, 1, 0, 0, 0]: return "No"
        elif fingers == [0, 0, 1, 0, 0]: return "Lo siento"
        elif fingers == [0, 0, 0, 1, 0]: return "Tengo hambre"
    
    # 🏴 Javanese
    elif mode == "javanese":
        if fingers == [1, 0, 0, 0, 1]: return f"Jenengku {user_name}"
        elif fingers == [1, 1, 1, 1, 1]: return "Halo"
        elif fingers == [1, 1, 1, 0, 0]: return "Aku"
        elif fingers == [0, 1, 0, 1, 0]: return "Kabar apik ora"
        elif fingers == [0, 0, 1, 1, 1]: return "Matur nuwun"
        elif fingers == [1, 1, 0, 0, 1]: return "Pamitan"
        elif fingers == [1, 0, 1, 1, 0]: return "Sugeng enjing"
        elif fingers == [0, 1, 1, 0, 1]: return "Sugeng dalu"
        elif fingers == [1, 0, 1, 0, 0]: return "Seneng ketemu kowe"
        elif fingers == [0, 1, 1, 1, 0]: return "Semangat yo!"
        elif fingers == [0, 0, 0, 0, 1]: return "Tulung"
        elif fingers == [1, 0, 0, 0, 0]: return "Iya"
        elif fingers == [0, 1, 0, 0, 0]: return "Ora"
        elif fingers == [0, 0, 1, 0, 0]: return "Nuwun sewu"
        elif fingers == [0, 0, 0, 1, 0]: return "Aku luwe"
    
    # 🏴 Sundanese
    elif mode == "sundanese":
        if fingers == [1, 0, 0, 0, 1]: return f"Ngaran abdi {user_name}"
        elif fingers == [1, 1, 1, 1, 1]: return "Halo"
        elif fingers == [1, 1, 1, 0, 0]: return "Abdi"
        elif fingers == [0, 1, 0, 1, 0]: return "Kumaha damang"
        elif fingers == [0, 0, 1, 1, 1]: return "Hatur nuhun"
        elif fingers == [1, 1, 0, 0, 1]: return "Dugi ka engke"
        elif fingers == [1, 0, 1, 1, 0]: return "Wilujeng enjing"
        elif fingers == [0, 1, 1, 0, 1]: return "Wilujeng wengi"
        elif fingers == [1, 0, 1, 0, 0]: return "Reueus patepang"
        elif fingers == [0, 1, 1, 1, 0]: return "Sumanget terus"
        elif fingers == [0, 0, 0, 0, 1]: return "Tolong"
        elif fingers == [1, 0, 0, 0, 0]: return "Enya"
        elif fingers == [0, 1, 0, 0, 0]: return "Henteu"
        elif fingers == [0, 0, 1, 0, 0]: return "Hapunten"
        elif fingers == [0, 0, 0, 1, 0]: return "Abdi lapar"
    
    # 🇮🇹 Italian
    elif mode == "italian":
        if fingers == [1, 0, 0, 0, 1]: return f"Mi chiamo {user_name}"
        elif fingers == [1, 1, 1, 1, 1]: return "Ciao"
        elif fingers == [1, 1, 1, 0, 0]: return "Io sono"
        elif fingers == [0, 1, 0, 1, 0]: return "Come stai"
        elif fingers == [0, 0, 1, 1, 1]: return "Grazie"
        elif fingers == [1, 1, 0, 0, 1]: return "Arrivederci"
        elif fingers == [1, 0, 1, 1, 0]: return "Buongiorno"
        elif fingers == [0, 1, 1, 0, 1]: return "Buonanotte"
        elif fingers == [1, 0, 1, 0, 0]: return "Piacere di conoscerti"
        elif fingers == [0, 1, 1, 1, 0]: return "Forza!"
        elif fingers == [0, 0, 0, 0, 1]: return "Aiuto"
        elif fingers == [1, 0, 0, 0, 0]: return "Sì"
        elif fingers == [0, 1, 0, 0, 0]: return "No"
        elif fingers == [0, 0, 1, 0, 0]: return "Scusa"
        elif fingers == [0, 0, 0, 1, 0]: return "Ho fame"
    
    # 🇨🇳 Chinese
    elif mode == "chinese":
        if fingers == [1, 0, 0, 0, 1]: return f"我的名字是 {user_name}"  # Wo de mingzi shi
        elif fingers == [1, 1, 1, 1, 1]: return "你好"  # Ni hao
        elif fingers == [1, 1, 1, 0, 0]: return "我是"  # Wo shi
        elif fingers == [0, 1, 0, 1, 0]: return "你好吗"  # Ni hao ma
        elif fingers == [0, 0, 1, 1, 1]: return "谢谢"  # Xiexie
        elif fingers == [1, 1, 0, 0, 1]: return "再见"  # Zaijian
        elif fingers == [1, 0, 1, 1, 0]: return "早上好"  # Zaoshang hao
        elif fingers == [0, 1, 1, 0, 1]: return "晚安"  # Wan an
        elif fingers == [1, 0, 1, 0, 0]: return "很高兴见到你"  # Hen gaoxing jiandao ni
        elif fingers == [0, 1, 1, 1, 0]: return "加油!"  # Jiayou!
        elif fingers == [0, 0, 0, 0, 1]: return "帮助"  # Bangzhu
        elif fingers == [1, 0, 0, 0, 0]: return "是的"  # Shide
        elif fingers == [0, 1, 0, 0, 0]: return "不"  # Bu
        elif fingers == [0, 0, 1, 0, 0]: return "对不起"  # Duibuqi
        elif fingers == [0, 0, 0, 1, 0]: return "我饿了"  # Wo ele
    
    # 🇹🇭 Thai
    elif mode == "thai":
        if fingers == [1, 0, 0, 0, 1]: return f"ฉันชื่อ {user_name}"
        elif fingers == [1, 1, 1, 1, 1]: return "สวัสดี"  # Sawasdee
        elif fingers == [1, 1, 1, 0, 0]: return "ฉันคือ"
        elif fingers == [0, 1, 0, 1, 0]: return "สบายดีไหม"
        elif fingers == [0, 0, 1, 1, 1]: return "ขอบคุณ"  # Khob khun
        elif fingers == [1, 1, 0, 0, 1]: return "ลาก่อน"  # La gon
        elif fingers == [1, 0, 1, 1, 0]: return "สวัสดีตอนเช้า"
        elif fingers == [0, 1, 1, 0, 1]: return "ราตรีสวัสดิ์"
        elif fingers == [1, 0, 1, 0, 0]: return "ยินดีที่ได้รู้จัก"
        elif fingers == [0, 1, 1, 1, 0]: return "สู้ต่อไป!"
        elif fingers == [0, 0, 0, 0, 1]: return "ช่วยด้วย"  # Chuay duay
        elif fingers == [1, 0, 0, 0, 0]: return "ใช่"  # Chai
        elif fingers == [0, 1, 0, 0, 0]: return "ไม่"  # Mai
        elif fingers == [0, 0, 1, 0, 0]: return "ขอโทษ"  # Kho thot
        elif fingers == [0, 0, 0, 1, 0]: return "ฉันหิว"  # Chan hiu
    
    # 🇸🇦 Arabic
    elif mode == "arabic":
        if fingers == [1, 0, 0, 0, 1]: return f"اسمي {user_name}"  # Ismi {user_name}
        elif fingers == [1, 1, 1, 1, 1]: return "مرحبا"  # Marhaban
        elif fingers == [1, 1, 1, 0, 0]: return "أنا"  # Ana
        elif fingers == [0, 1, 0, 1, 0]: return "كيف حالك"  # Kaifa haluk
        elif fingers == [0, 0, 1, 1, 1]: return "شكرا"  # Shukran
        elif fingers == [1, 1, 0, 0, 1]: return "مع السلامة"  # Ma'a as-salama
        elif fingers == [0, 1, 1, 1, 0]: return "الله أكبر"  # Allahu Akbar
        elif fingers == [1, 0, 1, 1, 0]: return "صباح الخير"  # Sabah al-khair
        elif fingers == [0, 1, 1, 0, 1]: return "مساء الخير"  # Masaa al-khair
        elif fingers == [1, 0, 1, 0, 0]: return "تبارك الله"  # Tabarakallah
        elif fingers == [0, 0, 0, 0, 1]: return "مساعدة"  # Musaeada
        elif fingers == [1, 0, 0, 0, 0]: return "نعم"  # Naam
        elif fingers == [0, 1, 0, 0, 0]: return "لا"  # La
        elif fingers == [0, 0, 1, 0, 0]: return "آسف"  # Aasif
        elif fingers == [0, 0, 0, 1, 0]: return "أنا جائع"  # Ana jae
    
    # 🇰🇷 Korean
    elif mode == "korean":
        if fingers == [1, 0, 0, 0, 1]: return f"제 이름은 {user_name}입니다"  # Je ireumeun {user_name} imnida
        elif fingers == [1, 1, 1, 1, 1]: return "안녕하세요"  # Annyeonghaseyo
        elif fingers == [1, 1, 1, 0, 0]: return "저는"  # Jeoneun
        elif fingers == [0, 1, 0, 1, 0]: return "어떻게 지내세요"  # Eotteoke jinaeseyo
        elif fingers == [0, 0, 1, 1, 1]: return "감사합니다"  # Gamsahamnida
        elif fingers == [1, 1, 0, 0, 1]: return "안녕히 가세요"  # Annyeonghi gaseyo
        elif fingers == [1, 0, 1, 1, 0]: return "좋은 아침입니다"  # Joeun achim imnida
        elif fingers == [0, 1, 1, 0, 1]: return "안녕히 주무세요"  # Annyeonghi jumuseyo
        elif fingers == [1, 0, 1, 0, 0]: return "만나서 반갑습니다"  # Mannaseo bangapseumnida
        elif fingers == [0, 1, 1, 1, 0]: return "화이팅!"  # Hwaiting!
        elif fingers == [0, 0, 0, 0, 1]: return "도와주세요"  # Dowajuseyo
        elif fingers == [1, 0, 0, 0, 0]: return "네"  # Ne
        elif fingers == [0, 1, 0, 0, 0]: return "아니요"  # Aniyo
        elif fingers == [0, 0, 1, 0, 0]: return "미안합니다"  # Mianhamnida
        elif fingers == [0, 0, 0, 1, 0]: return "배고파요"  # Baegopayo
    
    # 🇮🇳 Hindi
    elif mode == "hindi":
        if fingers == [1, 0, 0, 0, 1]: return f"मेरा नाम {user_name} है"  # Mera naam {user_name} hai
        elif fingers == [1, 1, 1, 1, 1]: return "नमस्ते"  # Namaste
        elif fingers == [1, 1, 1, 0, 0]: return "मैं"  # Main
        elif fingers == [0, 1, 0, 1, 0]: return "आप कैसे हैं"  # Aap kaise hain
        elif fingers == [0, 0, 1, 1, 1]: return "धन्यवाद"  # Dhanyavaad
        elif fingers == [1, 1, 0, 0, 1]: return "अलविदा"  # Alvida
        elif fingers == [1, 0, 1, 1, 0]: return "शुभ प्रभात"  # Shubh prabhaat
        elif fingers == [0, 1, 1, 0, 1]: return "शुभ रात्रि"  # Shubh raatri
        elif fingers == [1, 0, 1, 0, 0]: return "आपसे मिलकर खुशी हुई"  # Aapse milkar khushi hui
        elif fingers == [0, 1, 1, 1, 0]: return "जारी रखो!"  # Jaari rakho!
        elif fingers == [0, 0, 0, 0, 1]: return "मदद"  # Madad
        elif fingers == [1, 0, 0, 0, 0]: return "हाँ"  # Haan
        elif fingers == [0, 1, 0, 0, 0]: return "नहीं"  # Nahin
        elif fingers == [0, 0, 1, 0, 0]: return "माफ़ कीजिए"  # Maaf kijiye
        elif fingers == [0, 0, 0, 1, 0]: return "मुझे भूख लगी है"  # Mujhe bhookh lagi hai
    
    return "-"

def main():
    """Main entry: choose language, get user name, start speech worker and camera loop."""
    global bahasa, mode, bendera, user_name

    # Pilih bahasa dan nama pengguna
    bahasa, mode, bendera = pilih_bahasa()
    print(f"🗣 Bahasa awal: {mode.capitalize()} {bendera}")

    user_input = input("Masukkan nama kamu: ").strip()
    if user_input:
        user_name = user_input
    print(f"👋 Halo {user_name}! Mari mulai...")

    # Start speech worker thread
    speech_thread = threading.Thread(target=speech_worker, daemon=True)
    speech_thread.start()

    # Buka kamera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Tidak dapat mengakses kamera")
        return

    print("\n📸 Kamera aktif — tekan Q untuk keluar, B untuk ganti bahasa")
    print("🤟 Tunjukkan gesture tangan di depan kamera...\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error: Tidak dapat membaca frame dari kamera")
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            text = "-"
            confidence = 0

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    fingers = get_finger_states(hand_landmarks)
                    text = classify_letter(fingers)

                    # Tampilkan status jari di frame
                    finger_names = ["Jempol", "Telunjuk", "Tengah", "Manis", "Kelingking"]
                    for i, (name, state) in enumerate(zip(finger_names, fingers)):
                        color = (0, 255, 0) if state == 1 else (0, 0, 255)
                        cv2.putText(frame, f"{name}: {'Terbuka' if state == 1 else 'Tertutup'}",
                                   (20, 150 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Tampilkan teks terdeteksi
            if text != "-":
                cv2.putText(frame, f"Terdeteksi: {text}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                maybe_speak(text)
            else:
                cv2.putText(frame, "Gesture tidak dikenali", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # Info bahasa dan pengguna
            cv2.putText(frame, f"Bahasa: {mode.capitalize()} {bendera}", (20, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Pengguna: {user_name}", (20, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Petunjuk kontrol
            cv2.putText(frame, "Q: Keluar  B: Ganti Bahasa", (20, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            cv2.imshow("🤟 Pengenalan Bahasa Isyarat Multi-Bahasa", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('b'):
                bahasa, mode, bendera = pilih_bahasa()
                speak_text = f"Bahasa diubah ke {mode}"
                maybe_speak(speak_text)
                print(f"🔄 Bahasa diubah ke {mode.capitalize()} {bendera}")

    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        # Signal speech worker to stop
        speech_queue.put(None)
        speech_thread.join()

        # Hapus semua file cache yang tersisa
        for file in os.listdir():
            if file.startswith("cache_"):
                try:
                    os.remove(file)
                    print(f"🗑 Cache dibersihkan: {file}")
                except Exception:
                    pass

        print("\n👋 Aplikasi ditutup. Terima kasih!")


if __name__ == "__main__":
    main()