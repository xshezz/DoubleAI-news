import sys
import os
import threading
import time
import json
import urllib.request
import urllib.parse
import webbrowser
import subprocess
import customtkinter as ctk
from PIL import Image, ImageDraw
import speech_recognition as sr
import pyautogui

# --- AYARLAR VE DOSYALAR ---
MEMORY_FILE = "double_memory.json"
CONFIG_FILE = "double_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except:
        pass

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {"selam": "Aleykümselam hoş geldin!"}

def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=4)
    except:
        pass

# --- GEMINI MODEL BAŞLATICI (google.generativeai altyapısı) ---
def get_gemini_model():
    config = load_config()
    api_key = config.get("gemini_api_key")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        print("Gemini model hatası:", e)
        return None

# --- DİL MODLARI ---
CURRENT_LANG = "tr"  # tr, ru, en

TRANSLATIONS = {
    "tr": {
        "hello": "Efendim?",
        "processing": "İşleniyor...",
        "unknown": "Bunu bilmiyorum",
        "updated": "Güncelleme tamamlandı, yeniden başlatılıyor.",
        "api_saved": "Gemini API anahtarı başarıyla kaydedildi.",
    },
    "ru": {
        "hello": "Слушаю вас?",
        "processing": "Обработка...",
        "unknown": "Я этого не знаю",
        "updated": "Обновление завершено, перезагрузка...",
        "api_saved": "API ключ Gemini успешно сохранен.",
    },
    "en": {
        "hello": "Yes?",
        "processing": "Processing...",
        "unknown": "I don't know that",
        "updated": "Update complete, restarting...",
        "api_saved": "Gemini API key successfully saved.",
    }
}

def t(key):
    return TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["tr"]).get(key, key)

# --- SES MOTORU ---
last_speech_time = 0

def speak(text):
    global last_speech_time
    current_time = time.time()
    if current_time - last_speech_time < 1.0:
        return
    last_speech_time = current_time

    try:
        powershell_command = f'''
        Add-Type -AssemblyName System.speech;
        $synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer;
        $synthesizer.Rate = 1;
        $synthesizer.Speak("{text}");
        '''
        subprocess.Popen(["powershell", "-Command", powershell_command], creationflags=subprocess.CREATE_NO_WINDOW)
    except:
        pass

# --- EKRANIN ALTINDA İNCE SİYAH-GRİ-BEYAZ ÇENTİK (HUD) ---
class SleekHUD(ctk.CTkToplevel):
    def __init__(self, parent, text="..."):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.94)
        
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 380, 44
        x = (sw - w) // 2
        y = sh - 80
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.frame = ctk.CTkFrame(self, fg_color="#141414", corner_radius=22, border_width=1, border_color="#333333")
        self.frame.pack(fill="both", expand=True)
        
        self.label = ctk.CTkLabel(self.frame, text=f"👾  {text}", font=("Consolas", 11, "bold"), text_color="#E0E0E0")
        self.label.pack(expand=True, padx=15)

    def update_text(self, new_text):
        try:
            self.label.configure(text=f"👾  {new_text}")
        except:
            pass

# --- ASCII LOGO YAZDIRMA ---
def print_logo():
    logo = r"""
        ██████╗  ██████╗ ██╗   ██╗██████╗ ██╗     ███████╗ █████╗ ██╗
        ██╔══██╗██╔═══██╗██║   ██║██╔══██╗██║     ██╔════╝██╔══██╗██║
        ██║  ██║██║   ██║██║   ██║██████╔╝██║     █████╗  ███████║██║
        ██║  ██║██║   ██║██║   ██║██╔══██╗██║     ██╔══╝  ██╔══██║██║
        ██████╔╝╚██████╔╝╚██████╔╝██████╔╝███████╗███████╗██║  ██║██║
        ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝
    """
    print(logo)
    print("================================================================")
    print("  DoubleAI Çekirdek Aktif - Sesli Komut ve Terminal Modu        ")
    print("  Komutlar: /api gemini \"KEY\" | /russia | /eng | /updates | /uninstall")
    print("================================================================\n")

# --- ANA KONSOL & ASİSTAN UYGULAMASI ---
class DoubleAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DoubleAI")
        self.geometry("250x250")
        self.withdraw()  # Arayüz penceresini gizler, arka planda HUD ve terminal ile çalışır

        self.memory = load_memory()
        self.is_running = True
        self.hud = None

        print_logo()

        # Sesli dinleme döngüsü
        threading.Thread(target=self.master_listener_loop, daemon=True).start()
        
        # Terminal komut satırı döngüsü
        self.terminal_input_loop()

    def show_hud(self, text):
        try:
            if not self.hud:
                self.hud = SleekHUD(self, text)
            else:
                self.hud.update_text(text)
        except:
            pass

    def hide_hud(self):
        try:
            if self.hud:
                self.hud.destroy()
                self.hud = None
        except:
            pass

    def terminal_input_loop(self):
        while self.is_running:
            try:
                cmd = input("DoubleAI> ").strip()
                if cmd.startswith("/"):
                    self.handle_system_command(cmd.lower())
                elif cmd:
                    self.execute_command(cmd.lower())
            except:
                break

    def handle_system_command(self, cmd):
        global CURRENT_LANG

        if cmd.startswith("/api gemini"):
            parts = cmd.split(" ", 2)
            if len(parts) >= 3:
                api_key = parts[2].strip('"').strip("'")
                config = load_config()
                config["gemini_api_key"] = api_key
                save_config(config)
                print("[+] Gemini API anahtarı başarıyla kaydedildi.")
                speak(t("api_saved"))
            else:
                print("[-] Hatalı kullanım! Örnek: /api gemini \"SENİN_API_ANAHTARIN\"")
            return

        if "/russia" in cmd:
            CURRENT_LANG = "ru"
            print("[+] Rusça moda geçildi.")
            speak("Режим активирован")
        elif "/eng" in cmd:
            CURRENT_LANG = "en"
            print("[+] İngilizce moda geçildi.")
            speak("English mode activated")
        elif "/updates" in cmd:
            print("[!] Güncellemeler kontrol ediliyor ve indiriliyor...")
            speak(t("updated"))
            try:
                raw_url = "https://raw.githubusercontent.com/xshezz/DoubleAI-news/main/main.py"
                req = urllib.request.urlopen(raw_url)
                new_code = req.read().decode("utf-8")
                current_script = sys.argv[0] if sys.argv[0].endswith(".py") else "double_ai.py"
                with open(current_script, "w", encoding="utf-8") as f:
                    f.write(new_code)
                print("[+] Güncelleme tamamlandı, yeniden başlatılıyor...")
                os._exit(0)
            except Exception as e:
                print("[-] Güncelleme hatası:", e)
        elif "/uninstall" in cmd:
            print("[!] Kaldırma ve temizlik işlemi başlatılıyor...")
            try:
                if os.path.exists(MEMORY_FILE):
                    os.remove(MEMORY_FILE)
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)
            except:
                pass
            os._exit(0)

    def master_listener_loop(self):
        while self.is_running:
            try:
                recognizer = sr.Recognizer()
                recognizer.energy_threshold = 300
                recognizer.dynamic_energy_threshold = True

                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    while self.is_running:
                        try:
                            audio = recognizer.listen(source, timeout=4, phrase_time_limit=4)
                            lang_code = "ru-RU" if CURRENT_LANG == "ru" else ("en-US" if CURRENT_LANG == "en" else "tr-TR")
                            text = recognizer.recognize_google(audio, language=lang_code).lower()

                            if "double" in text or "duble" in text:
                                self.after(0, lambda: self.show_hud(t("hello")))
                                speak(t("hello"))
                                
                                time.sleep(0.5)
                                
                                with sr.Microphone() as cmd_source:
                                    audio_cmd = recognizer.listen(cmd_source, timeout=6, phrase_time_limit=6)
                                
                                cmd = recognizer.recognize_google(audio_cmd, language=lang_code).lower()
                                self.after(0, lambda: self.show_hud(t("processing")))
                                
                                self.execute_command(cmd)
                                time.sleep(1.0)
                                self.after(0, self.hide_hud)

                        except sr.WaitTimeoutError:
                            continue
                        except sr.UnknownValueError:
                            continue
                        except:
                            break
            except:
                time.sleep(2)

    def execute_command(self, cmd):
        # 1. Özel Öğretilen Hafıza
        for trigger, response in self.memory.items():
            if trigger in cmd:
                print(f"[Yanıt]: {response}")
                speak(response)
                return

        # 2. Spotify Şarkı Açma
        if "spotify" in cmd or "şarkı" in cmd or "müzik" in cmd or "song" in cmd:
            song_query = cmd.replace("spotify", "").replace("şarkı", "").replace("aç", "").strip()
            if song_query:
                print(f"[Spotify]: {song_query} açılıyor.")
                speak(song_query)
                try:
                    encoded_query = urllib.parse.quote(song_query)
                    os.system(f"start spotify:search:{encoded_query}")
                except:
                    pass
            return

        # 3. Gemini API Entegrasyonu (google.generativeai)
        model = get_gemini_model()
        if model:
            try:
                response = model.generate_content(cmd)
                answer = response.text.strip().replace("\n", " ")
                if len(answer) > 150:
                    answer = answer[:150]
                print(f"[Gemini Yanıtı]: {answer}")
                speak(answer)
                return
            except Exception as e:
                print("Gemini hata:", e)
        else:
            print("[Bilgi] Gemini API anahtarı girilmemiş. /api gemini \"KEY\" komutunu kullanabilirsin.")

        print(f"[Bilinmeyen Komut]: {cmd}")
        speak(t("unknown"))

if __name__ == "__main__":
    app = DoubleAIApp()
    app.mainloop()
