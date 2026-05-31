import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import random
import queue
import sys
import os
import ctypes
from ctypes import wintypes

# Защита от сбоев (движение мыши в угол остановит скрипт, если используется мышь)
import pyautogui
pyautogui.FAILSAFE = True

# Импортируем дополнительные библиотеки с обработкой ошибок
try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    import keyboard
except ImportError:
    keyboard = None

# ==========================================
#  ХАРДВЕРНАЯ ЭМУЛЯЦИЯ КЛАВИАТУРЫ (ctypes)
# ==========================================
SendInput = ctypes.windll.user32.SendInput

# Скан-коды клавиш (DirectInput / Hardware scan codes)
KEY_W = 0x11
KEY_S = 0x1F
KEY_A = 0x1E
KEY_D = 0x20
KEY_SPACE = 0x39

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD),
                ("ii", Input_I)]

KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002

def press_key(hexKeyCode):
    extra = ctypes.c_void_p(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, KEYEVENTF_SCANCODE, 0, extra)
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def release_key(hexKeyCode):
    extra = ctypes.c_void_p(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, extra)
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


# ==========================================
#            ИНТЕРФЕЙС И ЛОГИКА
# ==========================================
BG_MAIN = "#121214"
BG_CARD = "#1a1a1e"
ACCENT_CYAN = "#00f0ff"
ACCENT_GREEN = "#00ff88"
ACCENT_RED = "#ff3366"
TEXT_MAIN = "#ffffff"
TEXT_MUTED = "#8a8a9a"
BG_LOG = "#0e0e10"

# ==========================================
#  КЛАССЫ ДЛЯ КРАСИВЫХ ЧЕКБОКСОВ (Toggle Switch)
# ==========================================
class ToggleSwitch(tk.Canvas):
    def __init__(self, parent, variable, command=None, bg_parent=BG_CARD):
        # Ширина: 60, Высота: 26.
        super().__init__(parent, width=60, height=26, bg=bg_parent, highlightthickness=0, cursor="hand2")
        self.variable = variable
        self.command = command
        
        # Текущее состояние и координаты бегунка
        self.is_checked = self.variable.get()
        self.current_x = 38.0 if self.is_checked else 4.0
        self.is_animating = False
        
        # Отрисовка скругленного фона переключателя
        self.bg_rect = self.draw_rounded_rect(2, 2, 58, 24, radius=11, fill="#2a2a30")
        
        # Отрисовка круглого бегунка
        self.knob = self.create_oval(self.current_x, 4, self.current_x + 18, 22, fill="#505058", outline="")
        
        self.bind("<Button-1>", self.toggle)
        self.update_state()

    def draw_rounded_rect(self, x1, y1, x2, y2, radius=8, **kwargs):
        points = [x1+radius, y1,
                  x2-radius, y1,
                  x2, y1,
                  x2, y1+radius,
                  x2, y2-radius,
                  x2, y2,
                  x2-radius, y2,
                  x1+radius, y2,
                  x1, y2,
                  x1, y2-radius,
                  x1, y1+radius,
                  x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def toggle(self, event=None):
        self.is_checked = not self.is_checked
        self.variable.set(self.is_checked)
        
        # Запускаем плавную анимацию
        self.is_animating = True
        self.animate_step()
        
        if self.command:
            self.command()

    def update_state(self):
        self.is_checked = self.variable.get()
        self.current_x = 38.0 if self.is_checked else 4.0
        self.is_animating = False
        
        # Мгновенная отрисовка исходного состояния
        self.coords(self.knob, self.current_x, 4, self.current_x + 18, 22)
        if self.is_checked:
            self.itemconfig(self.bg_rect, fill="#1c3b1e")
            self.itemconfig(self.knob, fill="#6EB54E")
        else:
            self.itemconfig(self.bg_rect, fill="#2a2a30")
            self.itemconfig(self.knob, fill="#505058")

    def animate_step(self):
        if not self.is_animating:
            return
            
        current_x = self.current_x
        target_x = 38.0 if self.is_checked else 4.0
        
        # Формула плавного затухания (Lerp/Easing) для мягкого скольжения
        diff = target_x - current_x
        if abs(diff) < 0.2:
            self.current_x = target_x
            self.is_animating = False
        else:
            self.current_x += diff * 0.35 # Скорость скольжения
            
        # Обновляем координаты бегунка
        self.coords(self.knob, self.current_x, 4, self.current_x + 18, 22)
        
        # Плавное смешивание цветов (интерполяция цвета)
        progress = (self.current_x - 4.0) / 34.0
        progress = max(0.0, min(1.0, progress)) # Безопасный зажим в диапазон [0, 1]
        
        # Интерполяция фона: от #2a2a30 (42, 42, 48) к #1c3b1e (28, 59, 30)
        r_bg = int(42 + (28 - 42) * progress)
        g_bg = int(42 + (59 - 42) * progress)
        b_bg = int(48 + (30 - 48) * progress)
        
        # Интерполяция бегунка: от #505058 (80, 80, 88) к #6EB54E (110, 181, 78)
        r_kn = int(80 + (110 - 80) * progress)
        g_kn = int(80 + (181 - 80) * progress)
        b_kn = int(88 + (78 - 88) * progress)
        
        self.itemconfig(self.bg_rect, fill=f"#{r_bg:02x}{g_bg:02x}{b_bg:02x}")
        self.itemconfig(self.knob, fill=f"#{r_kn:02x}{g_kn:02x}{b_kn:02x}")
        
        if self.is_animating:
            self.after(10, self.animate_step)

class ToggleRow(tk.Frame):
    def __init__(self, parent, text, variable, command=None):
        super().__init__(parent, bg=BG_CARD)
        # Увеличили вертикальный отступ до 9px для идеальной центровки и заполнения всей плитки!
        self.pack(fill=tk.X, pady=(9, 9), anchor=tk.W)
        
        # Кастомный красивый переключатель
        self.switch = ToggleSwitch(self, variable, command=command)
        self.switch.pack(side=tk.LEFT, padx=(0, 10))
        
        # Текстовое описание справа
        self.label = tk.Label(self, text=text, font=("Segoe UI", 9), fg=TEXT_MAIN, bg=BG_CARD, cursor="hand2")
        self.label.pack(side=tk.LEFT, pady=2)
        
        # При клике на текст переключатель тоже срабатывает!
        self.label.bind("<Button-1>", lambda event: self.switch.toggle())

class AntiAFKApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Anti-AFK")
        self.root.geometry("760x700")  # Увеличили высоту до 700 для просторного отображения логов без срезания строк
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(False, False)
        
        # Установка красивой иконки окна (поддерживает и исходный запуск, и сборку PyInstaller)
        try:
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
            icon_path = os.path.join(base_path, "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass
        
        # Состояние приложения
        self.is_running = False
        self.seconds_left = 0
        self.actions_count = 0
        self.start_time = None
        self.afk_thread = None
        self.log_queue = queue.Queue()
        self.toggle_requested = False
        
        # Переменные настроек
        self.min_interval = tk.IntVar(value=60)
        self.max_interval = tk.IntVar(value=180)
        
        self.action_jump = tk.BooleanVar(value=True)
        self.action_walk = tk.BooleanVar(value=True)
        self.action_turn = tk.BooleanVar(value=True)
        self.auto_focus = tk.BooleanVar(value=True)
        
        # Создаем элементы интерфейса
        self.create_widgets()
        
        # Запускаем глобальные горячие клавиши
        self.setup_hotkeys()
        
        # Запускаем цикл обновления интерфейса
        self.root.after(100, self.update_gui_loop)
        
        self.log("Приложение успешно запущено.")
        if not keyboard:
            self.log("⚠️ Клавиша F8 недоступна: библиотека 'keyboard' требует прав администратора.")
        else:
            self.log("⌨️ Горячая клавиша F8 активна! Нажмите её в игре для старта/стопа.")

    def create_widgets(self):
        # --- HEADER PANEL (Увеличили высоту до 75 для свободного рендеринга букв с хвостиками) ---
        header_frame = tk.Frame(self.root, bg=BG_CARD, height=75)
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        header_frame.pack_propagate(False)
        
        # Заголовок (пакуем слева в header_frame)
        title_label = tk.Label(header_frame, text="Roblox Anti-AFK", font=("Segoe UI", 14, "bold"), fg=TEXT_MAIN, bg=BG_CARD)
        title_label.pack(side=tk.LEFT, padx=(25, 0), pady=15)
        
        # Индикатор статуса и надпись статуса (пакуем справа в header_frame)
        self.status_indicator = tk.Canvas(header_frame, width=16, height=16, bg=BG_CARD, highlightthickness=0)
        self.status_indicator.pack(side=tk.RIGHT, padx=(0, 25), pady=29)
        self.draw_status_dot(ACCENT_RED)
        
        self.status_label = tk.Label(header_frame, text="ОСТАНОВЛЕН", font=("Segoe UI", 9, "bold"), fg=ACCENT_RED, bg=BG_CARD)
        self.status_label.pack(side=tk.RIGHT, padx=5, pady=25)
        
        # Никнейм (пакуем по центру, заполняя всё свободное место между заголовком и статусом)
        nick_label = tk.Label(header_frame, text="zap", font=("Segoe UI", 14, "bold"), fg="#20f3b3", bg=BG_CARD, anchor=tk.CENTER)
        nick_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- CONFIG PANEL ---
        config_frame = tk.Frame(self.root, bg=BG_CARD)
        config_frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Левая колонка: Интервалы времени
        left_config = tk.Frame(config_frame, bg=BG_CARD)
        left_config.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        interval_title = tk.Label(left_config, text="Интервал срабатывания:", font=("Segoe UI", 10, "bold"), fg=TEXT_MAIN, bg=BG_CARD)
        interval_title.pack(anchor=tk.W, pady=(0, 3))
        
        interval_desc = tk.Label(left_config, text="Бот делает случайную паузу (секунды)\nиз этого диапазона перед каждым действием:", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_CARD, justify=tk.LEFT)
        interval_desc.pack(anchor=tk.W, pady=(0, 8))
        
        # Регистрируем валидатор ввода (разрешены только цифры)
        val_digit = self.root.register(self.validate_digit)

        inputs_frame = tk.Frame(left_config, bg=BG_CARD)
        inputs_frame.pack(anchor=tk.W, pady=(0, 10))
        
        tk.Label(inputs_frame, text="От:", fg=TEXT_MUTED, bg=BG_CARD, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.min_entry = tk.Entry(inputs_frame, textvariable=self.min_interval, width=6, bg=BG_MAIN, fg=TEXT_MAIN, insertbackground=TEXT_MAIN, bd=0, highlightthickness=1, highlightbackground="#33333b", highlightcolor=ACCENT_CYAN, font=("Segoe UI", 10), justify=tk.CENTER, validate="key", validatecommand=(val_digit, "%S"))
        self.min_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Label(inputs_frame, text="До:", fg=TEXT_MUTED, bg=BG_CARD, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.max_entry = tk.Entry(inputs_frame, textvariable=self.max_interval, width=6, bg=BG_MAIN, fg=TEXT_MAIN, insertbackground=TEXT_MAIN, bd=0, highlightthickness=1, highlightbackground="#33333b", highlightcolor=ACCENT_CYAN, font=("Segoe UI", 10), justify=tk.CENTER, validate="key", validatecommand=(val_digit, "%S"))
        self.max_entry.pack(side=tk.LEFT)
        
        # Разделитель
        separator = tk.Frame(config_frame, bg="#2a2a30", width=1)
        separator.pack(side=tk.LEFT, fill=tk.Y, pady=10)
        
        # Правая колонка: Настройки действий (Увеличили padx до 20 для предотвращения обрезки текста слева)
        right_config = tk.Frame(config_frame, bg=BG_CARD)
        right_config.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        actions_title = tk.Label(right_config, text="Настройки и Действия:", font=("Segoe UI", 10, "bold"), fg=TEXT_MAIN, bg=BG_CARD)
        actions_title.pack(anchor=tk.W, pady=(0, 5))
        
        # Используем новые анимированные переключатели (Toggle switches),
        # стилизованные под присланный вами макет, с поддержкой кликов по тексту!
        ToggleRow(right_config, "Прыжок (Space)", self.action_jump)
        ToggleRow(right_config, "Шаг вперед-назад (W/S)", self.action_walk)
        ToggleRow(right_config, "Поворот влево-вправо (A/D)", self.action_turn)
        ToggleRow(right_config, "Авто-фокус окна Roblox", self.auto_focus)

        # --- STATS PANEL ---
        stats_frame = tk.Frame(self.root, bg=BG_CARD)
        stats_frame.pack(fill=tk.X, padx=15, pady=5)
        
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        
        self.timer_display = tk.Label(stats_frame, text="До действия: --", font=("Segoe UI", 9, "bold"), fg=ACCENT_CYAN, bg=BG_CARD)
        self.timer_display.grid(row=0, column=0, sticky=tk.W, padx=15, pady=10)
        
        self.stats_display = tk.Label(stats_frame, text="Действий: 0 | Время сессии: 00:00:00", font=("Segoe UI", 9, "bold"), fg=TEXT_MUTED, bg=BG_CARD)
        self.stats_display.grid(row=0, column=1, sticky=tk.E, padx=15, pady=10)

        # --- CONTROLS PANEL ---
        controls_frame = tk.Frame(self.root, bg=BG_MAIN)
        controls_frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Кнопка СТАРТ
        self.btn_start = tk.Button(controls_frame, text="СТАРТ (F8)", font=("Segoe UI", 11, "bold"), bg="#1e3d2f", fg=ACCENT_GREEN, activebackground=ACCENT_GREEN, activeforeground=BG_MAIN, bd=0, highlightthickness=1, highlightbackground=ACCENT_GREEN, cursor="hand2", command=self.start)
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), pady=5)
        
        # Кнопка СТОП
        self.btn_stop = tk.Button(controls_frame, text="СТОП (F8)", font=("Segoe UI", 11, "bold"), bg="#3d1e25", fg=ACCENT_RED, activebackground=ACCENT_RED, activeforeground=TEXT_MAIN, bd=0, highlightthickness=1, highlightbackground=ACCENT_RED, cursor="hand2", command=self.stop)
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0), pady=5)

        # --- LOGS PANEL (Увеличили высоту и растягиваемость) ---
        logs_frame = tk.Frame(self.root, bg=BG_CARD)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))
        
        log_title = tk.Label(logs_frame, text="ЛОГ АКТИВНОСТИ", font=("Segoe UI", 9, "bold"), fg=TEXT_MUTED, bg=BG_CARD)
        log_title.pack(anchor=tk.W, padx=15, pady=(6, 3))
        
        # Высота 13 строк - теперь в логе гарантированно поместится 5-6 последних записей действий одновременно
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=13, wrap=tk.WORD, bg=BG_LOG, fg=TEXT_MAIN, insertbackground=TEXT_MAIN, font=("Consolas", 9), bd=0, highlightthickness=1, highlightbackground="#222228")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 12))

    def draw_status_dot(self, color):
        self.status_indicator.delete("all")
        self.status_indicator.create_oval(2, 2, 14, 14, fill=color, outline="")

    def validate_digit(self, char):
        # Разрешаем ввод только цифр или пустой строки (для стирания)
        return char.isdigit() or char == ""

    def log(self, message):
        timestamp = time.strftime("[%H:%M:%S]")
        self.log_queue.put(f"{timestamp} {message}")

    def setup_hotkeys(self):
        if keyboard:
            try:
                keyboard.add_hotkey('F8', lambda: setattr(self, 'toggle_requested', True))
            except Exception as e:
                print(f"Ошибка бинда клавиш: {e}")

    def start(self):
        if self.is_running:
            return
            
        # Снимаем фокус с полей ввода, чтобы клавиатурные нажатия не шли в них
        self.root.focus()
        
        try:
            min_val = self.min_interval.get()
            max_val = self.max_interval.get()
            if min_val < 3:
                self.log("⚠️ Минимальный интервал должен быть не менее 3 сек. Установлено: 3")
                self.min_interval.set(3)
                min_val = 3
            if max_val < min_val:
                self.log(f"⚠️ Максимальный интервал не может быть меньше минимального. Установлено: {min_val}")
                self.max_interval.set(min_val)
                max_val = min_val
        except Exception:
            self.log("❌ Ошибка: Введены некорректные числа в поля интервалов!")
            return
        
        self.is_running = True
        self.start_time = time.time()
        self.actions_count = 0
        
        self.draw_status_dot(ACCENT_GREEN)
        self.status_label.config(text="РАБОТАЕТ", fg=ACCENT_GREEN)
        self.log("🟢 Бот Anti-AFK активирован.")
        self.log("🕒 Первое действие сработает через 3 секунды...")
        
        self.afk_thread = threading.Thread(target=self.afk_loop, daemon=True)
        self.afk_thread.start()

    def stop(self):
        if not self.is_running:
            return
        
        self.is_running = False
        
        self.draw_status_dot(ACCENT_RED)
        self.status_label.config(text="ОСТАНОВЛЕН", fg=ACCENT_RED)
        self.timer_display.config(text="До действия: --")
        self.log("🔴 Бот Anti-AFK остановлен.")

    def find_roblox_window(self):
        if not gw:
            return None
        
        windows = gw.getAllWindows()
        for w in windows:
            if "roblox" in w.title.lower():
                return w
        return None

    def is_roblox_active(self, roblox_window):
        if not gw:
            return True
        
        try:
            active_w = gw.getActiveWindow()
            if active_w and roblox_window:
                return active_w._hWnd == roblox_window._hWnd
        except Exception:
            pass
        return False

    def focus_window(self, window):
        try:
            if window.isMinimized:
                window.restore()
            window.activate()
            time.sleep(0.5)
            return True
        except Exception as e:
            self.log(f"⚠️ Не удалось развернуть окно Roblox: {e}")
            return False

    def perform_action(self):
        available_actions = []
        if self.action_jump.get():
            available_actions.append("jump")
        if self.action_walk.get():
            available_actions.append("walk")
        if self.action_turn.get():
            available_actions.append("turn")
            
        if not available_actions:
            self.log("⚠️ Действие пропущено: не выбрано ни одного действия в настройках.")
            return False
            
        action = random.choice(available_actions)
        
        try:
            if action == "jump":
                self.log("🚀 Выполняю: Прыжок (Space)")
                press_key(KEY_SPACE)
                time.sleep(0.2)
                release_key(KEY_SPACE)
            elif action == "walk":
                # Математически точная случайная прогулка (2-3 шага) с возвратом в исходную точку
                opposites = {KEY_W: KEY_S, KEY_S: KEY_W, KEY_A: KEY_D, KEY_D: KEY_A}
                available_keys = [KEY_W, KEY_S, KEY_A, KEY_D]
                num_steps = random.randint(2, 3)
                self.log(f"🚶 Прогулка ({num_steps} шагов) с возвратом:")
                
                forward_path = []
                for _ in range(num_steps):
                    key = random.choice(available_keys)
                    duration = round(random.uniform(0.15, 0.3), 2)
                    forward_path.append((key, duration))
                    
                # Выполняем путь вперед
                for key, duration in forward_path:
                    key_name = {KEY_W: 'W', KEY_S: 'S', KEY_A: 'A', KEY_D: 'D'}[key]
                    self.log(f"  └─ Движение: {key_name} ({duration} сек)")
                    press_key(key)
                    time.sleep(duration)
                    release_key(key)
                    time.sleep(0.05)
                    
                time.sleep(0.15)
                
                # Точный зеркальный возврат (LIFO) для сохранения исходной точки
                self.log("  └─ Зеркальный возврат в исходную точку...")
                for key, duration in reversed(forward_path):
                    opp_key = opposites[key]
                    press_key(opp_key)
                    time.sleep(duration)
                    release_key(opp_key)
                    time.sleep(0.05)
            elif action == "turn":
                duration = round(random.uniform(0.15, 0.3), 2)
                self.log(f"🔄 Поворот влево-вправо ({duration} сек)")
                press_key(KEY_A)
                time.sleep(duration)
                release_key(KEY_A)
                time.sleep(0.1)
                press_key(KEY_D)
                time.sleep(duration)
                release_key(KEY_D)
            
            self.actions_count += 1
            return True
        except Exception as e:
            self.log(f"❌ Ошибка при эмуляции ввода: {e}")
            return False

    def afk_loop(self):
        # 1. Первое быстрое действие через 3 секунды
        self.seconds_left = 3
        while self.seconds_left > 0 and self.is_running:
            time.sleep(1)
            self.seconds_left -= 1
            
        if self.is_running:
            self.check_and_act()
            
        # 2. Основной рандомный цикл
        while self.is_running:
            min_s = self.min_interval.get()
            max_s = self.max_interval.get()
            interval = random.randint(min_s, max_s)
            
            self.seconds_left = interval
            
            while self.seconds_left > 0 and self.is_running:
                time.sleep(1)
                self.seconds_left -= 1
                
            if not self.is_running:
                break
                
            self.check_and_act()

    def check_and_act(self):
        roblox_win = self.find_roblox_window()
        
        if not roblox_win:
            self.log("🔍 Окно Roblox не найдено в запущенных процессах! Ожидаю игру...")
            return
            
        is_active = self.is_roblox_active(roblox_win)
        
        if not is_active:
            if self.auto_focus.get():
                self.log("🔔 Окно Roblox неактивно. Разворачиваю игру...")
                if self.focus_window(roblox_win):
                    self.perform_action()
                else:
                    self.log("⏸️ Пропуск: не удалось развернуть окно Roblox.")
            else:
                self.log("⏸️ Пропуск: Roblox неактивен (авто-фокус выключен).")
        else:
            self.perform_action()

    def update_gui_loop(self):
        if self.toggle_requested:
            self.toggle_requested = False
            if self.is_running:
                self.stop()
            else:
                self.start()
                
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, msg + "\n")
                self.log_text.see(tk.END)
            except queue.Empty:
                break
                
        if self.is_running:
            self.timer_display.config(text=f"До действия: {self.seconds_left} sec.")
            
            elapsed = int(time.time() - self.start_time)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            self.stats_display.config(text=f"Действий: {self.actions_count} | Время сессии: {time_str}")
        else:
            self.timer_display.config(text="До действия: --")
            
        self.root.after(100, self.update_gui_loop)

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    root = tk.Tk()
    app = AntiAFKApp(root)
    root.mainloop()
