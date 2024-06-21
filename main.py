import customtkinter
import tkinter as tk
import os
from PIL import Image
from PIL import ImageTk

import keyboard
import threading
from win10toast import ToastNotifier
import time
import datetime
import logging

import minecraft_launcher_lib
from minecraft_launcher_lib.utils import get_minecraft_directory, get_version_list
from minecraft_launcher_lib.forge import find_forge_version
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command
from random_username.generate import generate_username

from uuid import uuid1
from subprocess import call
import subprocess
import sys
import io
from io import StringIO
import pystray
import json
import random
import string


#minecraft_directory = get_minecraft_directory().replace('minecraft', 'cultismMC')
minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()

customtkinter.set_default_color_theme("assets/green.json")

version = 'ex0.1'

class recraftMC(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        #customtkinter.set_default_color_theme("green")
        self.title("re:Craft Launcher: Experimental edition🧪")
        self.geometry("920x585")
        #self.minsize(920, 585)
        #self.maxsize(920, 585)
        self.resizable(False, False)

        self.install_thread = None
        self.progress_max = 0
        self.installing = False  # флаг, указывающий, идет ли установка
        self.install_thread_id = None

        self.progress_bar_visible = False

        self.toaster = ToastNotifier()

        # Путь к папке для хранения пользовательских данных
        self.userdata_folder = os.path.join(os.getenv('APPDATA'), 'reCraftUserdata')
        
        # Создание папки для хранения пользовательских данных, если она не существует
        if not os.path.exists(self.userdata_folder):
            os.makedirs(self.userdata_folder)

        # Путь к файлу с настройками
        self.settings_file_path = os.path.join(self.userdata_folder, 'settings.json')
        
        # Создание файла с настройками, если он не существует
        if not os.path.exists(self.settings_file_path):
            self.create_settings_file()

        # Загрузка настроек из файла
        self.load_settings()

        console = customtkinter.CTkFont(family="Consolas", size=18, weight="normal")    

        self.greetings = ["Добро пожаловать в re:Craft!",
                          "Приветствую вас в re:Craft!",
                          "Рады видеть вас в re:Craft!"
                          ]

        #даем иконку
        self.iconpath = ImageTk.PhotoImage(file=os.path.join("assets","logo.png"))
        self.wm_iconbitmap()
        self.iconphoto(False, self.iconpath)

        # set grid layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        keyboard.add_hotkey('alt+6', self.open_new_window_in_about_frame)
        self.current_frame = None

        # load images with light and dark mode image
        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets")
        self.logo_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "title.png")), size=(150, 35))
        self.icon = customtkinter.CTkImage(Image.open(os.path.join(image_path, "logo.png")), size=(60, 60))
        self.large_title_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "title.png")), size=(400, 90))
        self.image_icon_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "image_icon_light.png")), size=(20, 20))
        self.home_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "home_dark.png")),
                                                 dark_image=Image.open(os.path.join(image_path, "home_light.png")), size=(20, 20))
        self.settings_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "settings_dark.png")),
                                                    dark_image=Image.open(os.path.join(image_path, "settings_light.png")), size=(20, 20))
        self.about_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "about_dark.png")),
                                                  dark_image=Image.open(os.path.join(image_path, "about_light.png")), size=(20, 20))
        self.cmd_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "Terminal_dark.png")),
                                                  dark_image=Image.open(os.path.join(image_path, "terminal_light.png")), size=(20, 20))

        # панель сбоку
        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)

        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text="", image=self.icon,
                                                             compound="left", font=customtkinter.CTkFont(size=15, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Главная",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image=self.home_image, anchor="w", command=self.home_button_event)
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.settings_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Настройки",
                                                       fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                       image=self.settings_image, anchor="w", command=self.settings_button_event)
        self.settings_button.grid(row=2, column=0, sticky="ew")

        self.cmd_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Терминал",
                                                       fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                       image=self.cmd_image, anchor="w", command=self.cmd_button_event)
        self.cmd_button.grid(row=3, column=0, sticky="ew")

        self.about_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="О лаунчере",
                                                    fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                    image=self.about_image, anchor="w", command=self.about_button_event)
        self.about_button.grid(row=4, column=0, sticky="ew")

        #ник поле ввода
        self.nick_entry = customtkinter.CTkEntry(self.navigation_frame, placeholder_text="Никнейм")
        self.nick_entry.grid(row=6, column=0, padx=20, pady=5, sticky="nsew")

        #лист версий
        all_versions = self.get_all_versions()
        self.version_optionmenu = customtkinter.CTkComboBox(self.navigation_frame, values=all_versions)
        self.version_optionmenu.grid(row=7, column=0, padx=20, pady=1, sticky="nsew")

        #текст скачивания версии
        self.version_label = customtkinter.CTkLabel(self.navigation_frame, text="", anchor="w")
        self.version_label.grid(row=8, column=0, padx=20, pady=(5, 0), sticky="w")

        #прогресс бар
        self.progress_bar = customtkinter.CTkProgressBar(self.navigation_frame)
        self.progress_bar.configure(mode="indeterminnate")
        self.progress_bar.grid(row=9, column=0, padx=20, pady=5, sticky="nsew")
        
        #кнопка запуска и кнопка папки игры
        self.start_button = customtkinter.CTkButton(self.navigation_frame, text="Запуск игры", command=self.launch_game)
        self.start_button.grid(row=10, column=0, padx=20, pady=5, sticky="nsew")

        self.open_folder_button = customtkinter.CTkButton(self.navigation_frame, text="Открыть папку игры", command=self.open_minecraft_folder)
        self.open_folder_button.grid(row=11, column=0, padx=20, pady=5, sticky="nsew")

        #домашняя страница
        self.home_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.home_frame_large_image_label = customtkinter.CTkLabel(self.home_frame, text="Добро пожаловать в re:Craft!", 
                                                                   compound="left", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.home_frame_large_image_label.grid(row=0, column=0, padx=20, pady=10)
        
        #Приветствие которое со временем меняется
        #self.home_frame_label = customtkinter.CTkLabel(self.home_frame, text="", font=customtkinter.CTkFont(size=20, weight="bold"))
        #self.home_frame_label.grid(row=1, column=0, padx=20, pady=(10, 20))

        # Добавляем метод в инициализацию класса для обновления приветствия
        #self.update_greeting()

        #новости, чанджлог
        self.changelog = customtkinter.CTkLabel(self.home_frame, text="Изменения в версии ex0.1:",
                                                 compound="left", font=customtkinter.CTkFont(size=20, weight="normal"))
        self.changelog.grid(row=2, column=0, sticky="s", padx=20, pady=(0, 20))

        # Создание рамки с возможностью прокрутки
        self.frame = customtkinter.CTkScrollableFrame(self.home_frame, width=550, height=200)  # Устанавливаем размер рамки
        self.frame.grid(row=3, column=0, sticky="s")  # Используем grid вместо pack

        self.changelog = customtkinter.CTkLabel(self.frame, text="привет, ты находишся в эксперементальной ветке, малыш🧪 \n прочитай про ветку на гитхабе")
        self.changelog.grid(row=4, column=0, sticky="s", padx=20)


        #вторая страница: шедевронастройки
        self.settings_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")

        # Создаем фрейм для настроек запуска игры
        self.launch_settings_frame = customtkinter.CTkFrame(self.settings_frame, corner_radius=10, fg_color="gray20")
        self.launch_settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.title = customtkinter.CTkLabel(self.launch_settings_frame, text='Настройки игры', fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="ew")

        self.jvm_arguments_entry = customtkinter.CTkEntry(self.launch_settings_frame, placeholder_text="JVM Аргументы")
        self.jvm_arguments_entry.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")

        self.executable_path_entry = customtkinter.CTkEntry(self.launch_settings_frame, placeholder_text="Путь к Java Executable")
        self.executable_path_entry.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")

        self.default_executable_path_entry = customtkinter.CTkEntry(self.launch_settings_frame, placeholder_text="Путь к Java Executable по умолчанию")
        self.default_executable_path_entry.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")

        self.custom_resolution_checkbox = customtkinter.CTkCheckBox(self.launch_settings_frame, text="Пользовательское разрешение")
        self.custom_resolution_checkbox.grid(row=4, column=0, padx=20, pady=5, sticky="w")

        self.resolution_width_entry = customtkinter.CTkEntry(self.launch_settings_frame, placeholder_text="Ширина разрешения")
        self.resolution_width_entry.grid(row=5, column=0, padx=20, pady=5, sticky="nsew")

        self.resolution_height_entry = customtkinter.CTkEntry(self.launch_settings_frame, placeholder_text="Высота разрешения")
        self.resolution_height_entry.grid(row=6, column=0, padx=20, pady=5, sticky="nsew")

        self.game_directory_entry = customtkinter.CTkEntry(self.launch_settings_frame, placeholder_text="Каталог игры")
        self.game_directory_entry.grid(row=7, column=0, padx=20, pady=5, sticky="nsew")

        self.demo_mode_checkbox = customtkinter.CTkCheckBox(self.launch_settings_frame, text="Демо-режим")
        self.demo_mode_checkbox.grid(row=8, column=0, padx=20, pady=5, sticky="w")



        # Создаем фрейм для настроек интерфейса
        self.interface_settings_frame = customtkinter.CTkFrame(self.settings_frame, corner_radius=10, fg_color="gray20")
        self.interface_settings_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.title = customtkinter.CTkLabel(self.interface_settings_frame, text='Настройки интерфейса', fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")


        # Создаем виджеты для выбора приближения
        self.scaling_label = customtkinter.CTkLabel(self.interface_settings_frame, text="Масштабирование:", anchor="w")
        self.scaling_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.scaling_optionmenu = customtkinter.CTkOptionMenu(self.interface_settings_frame, values=["100%", "90%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionmenu.grid(row=2, column=0, padx=20, pady=20, sticky="s")

        # Создаем виджеты для выбора темы
        self.theme_label = customtkinter.CTkLabel(self.interface_settings_frame, text="Тема:", anchor="w")
        self.theme_label.grid(row=3, column=0, padx=20, pady=(10, 0))
        self.theme_optionmenu = customtkinter.CTkOptionMenu(self.interface_settings_frame, values=["Light", "Dark", "System"],
                                                               command=self.change_appearance_mode_event)
        self.theme_optionmenu.grid(row=4, column=0, padx=20, pady=20, sticky="s")

        # Создаем переменную для переключателя
        self.greeting_switch_var = customtkinter.StringVar(value="off")

        # Создаем переключатель и привязываем его к методу toggle_greeting
        self.greeting_switch = customtkinter.CTkSwitch(self.interface_settings_frame, text="Приветствие в зависимости от времени",
                                                       variable=self.greeting_switch_var, onvalue="on", offvalue="off",
                                                       command=self.toggle_greeting)
        self.greeting_switch.grid(row=5, column=0, padx=20, pady=5, sticky="w")
        self.greeting_switch.configure(state="disabled")

        #переменная для переключателя
        self.random_greeting_switch_var = customtkinter.StringVar(value="on")

        # Создаем переключатель и привязываем его к методу randomgreeting
        self.random_greeting_switch = customtkinter.CTkSwitch(self.interface_settings_frame, text="Случайное приветствие",
                                                       variable=self.random_greeting_switch_var, onvalue="on", offvalue="off",
                                                       command=self.update_randomgreeting)
        self.random_greeting_switch.grid(row=6, column=0, padx=20, pady=5, sticky="w")

        # Обновляем приветствие при запуске
        self.update_randomgreeting()
        '''
        #настройка темы

        self.jvm_arguments_entry = customtkinter.CTkEntry(self.settings_frame, placeholder_text="JVM Аргументы")
        self.jvm_arguments_entry.grid(row=9, column=0, padx=20, pady=5, sticky="nsew")

        self.executable_path_entry = customtkinter.CTkEntry(self.settings_frame, placeholder_text="Путь к Java Executable")
        self.executable_path_entry.grid(row=11, column=0, padx=20, pady=5, sticky="nsew")

        self.default_executable_path_entry = customtkinter.CTkEntry(self.settings_frame, placeholder_text="Путь к Java Executable по умолчанию")
        self.default_executable_path_entry.grid(row=12, column=0, padx=20, pady=5, sticky="nsew")

        self.custom_resolution_checkbox = customtkinter.CTkCheckBox(self.settings_frame, text="Пользовательское разрешение")
        self.custom_resolution_checkbox.grid(row=8, column=2, padx=20, pady=5, sticky="w")

        self.resolution_width_entry = customtkinter.CTkEntry(self.settings_frame, placeholder_text="Ширина разрешения")
        self.resolution_width_entry.grid(row=9, column=2, padx=20, pady=5, sticky="nsew")

        self.resolution_height_entry = customtkinter.CTkEntry(self.settings_frame, placeholder_text="Высота разрешения")
        self.resolution_height_entry.grid(row=10, column=2, padx=20, pady=5, sticky="nsew")

        self.game_directory_entry = customtkinter.CTkEntry(self.settings_frame, placeholder_text="Каталог игры")
        self.game_directory_entry.grid(row=12, column=2, padx=20, pady=5, sticky="nsew")

        self.demo_mode_checkbox = customtkinter.CTkCheckBox(self.settings_frame, text="Демо-режим")
        self.demo_mode_checkbox.grid(row=13, column=2, padx=20, pady=5, sticky="w")'''

        # Добавление кнопки "Сохранить настройки"
        self.save_settings_button = customtkinter.CTkButton(self.settings_frame, text="Сохранить настройки")
        self.save_settings_button.grid(row=15, column=0, padx=20, pady=10, sticky="nsew")

        #третья страница: терминал
        self.cmd_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.cmd_frame.grid_rowconfigure(0, weight=1)
        self.cmd_frame.grid_columnconfigure(0, weight=1)

        # Создание текстового поля для вывода
        self.output_text = customtkinter.CTkTextbox(self.cmd_frame, wrap="word", text_color="#05ff00", font=console)
        self.output_text.pack(fill="both", expand=True)

        # Перенаправление стандартного вывода в текстовое поле
        sys.stdout = self.TextRedirector(self.output_text, "stdout")
        sys.stderr = self.TextRedirector(self.output_text, "stderr")

        # Настройка логгера
        self.logger = logging.getLogger("minecraft_logger")
        self.logger.setLevel(logging.INFO)

        # Создание обработчика для записи логов в текстовое поле
        log_stream = StringIO()
        log_handler = logging.StreamHandler(log_stream)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(formatter)
        self.logger.addHandler(log_handler)

        # Вывод логов из буфера в терминал
        self.after(100, self.update_terminal, log_stream)

        #четвертая страница: о лаунчере
        self.about_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.about_frame.grid_rowconfigure(0, weight=1)
        self.about_frame.grid_columnconfigure(0, weight=1)

        #логотип лаунчера
        self.about_frame_image_label = customtkinter.CTkLabel(self.about_frame, text="", image=self.large_title_image)
        self.about_frame_image_label.grid(row=0, column=0, padx=20, pady=10)

        #гигатекст
        self.editable_text_label = customtkinter.CTkLabel(self.about_frame, text="re:Craft Launcher - лаунчер майнкрафт написаный на Python 3 \n с использованием CustomTkinter и Minecraft Launcher Lib. \n Хз а зачем я это пишу ваще, короче лаунчер создан enexis'ом")
        self.editable_text_label.grid(row=1, column=0, sticky="s", padx=20, pady=(0, 200))

        #уникальный код привязанный к каждому лаунчеру
        self.code = customtkinter.CTkLabel(self.about_frame, text="ID: странно, у вас нет id...")
        self.code.grid(row=2, column=0, sticky="s", padx=20, pady=(0, 0))

        #версия, права текст
        #self.editable_text_label = customtkinter.CTkLabel(self.about_frame, text="cultism GUI - 5.0, cultism launch - 2.6")
        #self.editable_text_label.grid(row=2, column=0, sticky="s", padx=20, pady=(0, 100))

        #выбор стандартной страницы, в моем случае домашняя
        self.select_frame_by_name("home")

        self.install_thread = None

        self.progress_max = 0  # добавляем переменную для хранения максимального значения прогресс-бара


    #шэдэвро пасхалка
    def about_button_event(self):
        self.select_frame_by_name("about")

    #создание окна нового
    def open_new_window(self):
        new_window = customtkinter.CTk()
        new_window.title("C. U. L. T. I. S. M.")
        new_window.geometry("780x350")

        label = customtkinter.CTkLabel(new_window, text="░█████╗░██╗░░░██╗██╗░░░████████╗██╗░██████╗███╗░░░███╗\n██╔══██╗██║░░░██║██║░░░╚══██╔══╝██║██╔════╝████╗░████║\n██║░░╚═╝██║░░░██║██║░░░░░░██║░░░██║╚█████╗░██╔████╔██║\n██║░░██╗██║░░░██║██║░░░░░░██║░░░██║░╚═══██╗██║╚██╔╝██║\n╚█████╔╝╚██████╔╝███████╗░██║░░░██║██████╔╝██║░╚═╝░██║\n░╚════╝░░╚═════╝░╚══════╝░╚═╝░░░╚═╝╚═════╝░╚═╝░░░░░╚═╝",text_color = "#b80000", font=customtkinter.CTkFont(size=12))
        label.pack(pady=20)

        # функция для закрытия нового окна
        def close_new_window():
            new_window.destroy()

        # кнопка для закрытия нового окна
        #close_button = customtkinter.CTkButton(new_window, text="ПРИСОЕДЕНИТСЯ К КУЛЬТУ", command=close_new_window)
        #close_button.pack(pady=10)

        # обработчик для закрытия окна при нажатии на крестик
        def on_close_window():
            close_new_window()

        # привязываем обработчик к событию закрытия окна
        new_window.protocol("WM_DELETE_WINDOW", on_close_window)

        # Запускаем главный цикл окна
        new_window.mainloop()

    def open_new_window_in_about_frame(self):
        # открыть пасхалку на Alt + 6 
        if self.current_frame == self.about_frame:
            self.open_new_window()
    
    #переключение между страницами
    def select_frame_by_name(self, name):
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.settings_button.configure(fg_color=("gray75", "gray25") if name == "settings" else "transparent")
        self.cmd_button.configure(fg_color=("gray75", "gray25") if name == "cmd" else "transparent")
        self.about_button.configure(fg_color=("gray75", "gray25") if name == "about" else "transparent")

        self.current_frame = None
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
            self.current_frame = self.home_frame
        else:
            self.home_frame.grid_forget()
        if name == "settings":
            self.settings_frame.grid(row=0, column=1, sticky="nsew")
            self.current_frame = self.settings_frame
        else:
            self.settings_frame.grid_forget()
        if name == "cmd":
            self.cmd_frame.grid(row=0, column=1, sticky="nsew")
            self.current_frame = self.cmd_frame
        else:
            self.cmd_frame.grid_forget()
        if name == "about":
            self.about_frame.grid(row=0, column=1, sticky="nsew")
            self.current_frame = self.about_frame
        else:
            self.about_frame.grid_forget()

    def home_button_event(self):
        self.select_frame_by_name("home")

    def settings_button_event(self):
        self.select_frame_by_name("settings")

    def cmd_button_event(self):
        self.select_frame_by_name("cmd")

    def about_button_event(self):
        self.select_frame_by_name("about")

    def change_appearance_mode_event(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    #методы для запуска игры
        
    def update_progress_max(self, max_value):
        self.progress_max = max_value
        self.progress_bar['maximum'] = max_value

    def update_progress_label(self, status):
        try:
            status_value = int(status)
            self.progress_bar.set(status_value)
        except ValueError:
            # Если не удается преобразовать в число, установите значение по умолчанию или обработайте ошибку по своему усмотрению
            self.progress_bar.set(0)

    def update_progress(self, count, _=0):
        self.progress_bar['value'] = count
        self.progress_bar['maximum'] = self.progress_max

    def install_minecraft(self):
        threading.Thread(target=self._install_minecraft).start()
        self.update_progress_max(100)  # Пример: установка максимального значения прогресс-бара
        self.version_label.configure(text=f"Идет запуск версии {self.version_optionmenu.get()}")  # Обновляем текст
        self.start_install_thread()

    def reset_progress_bar(self):  
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = 0
        self.progress_bar.stop()
        self.installing = False  # сбрасываем флаг при завершении установки

    def _install_minecraft(self):
        self.installing = True  # устанавливаем флаг при начале установки
        install_minecraft_version(versionid=self.version_id, minecraft_directory=minecraft_directory,
                                  callback={'setStatus': self.update_progress_label,
                                            'setProgress': self.update_progress,
                                            'setMax': self.update_progress_max})

        if self.username == '':
            self.username = generate_username()[0]

        options = {
            "username": self.username,
            "uuid": str(uuid1()),
            "token": ""
        }

        call(get_minecraft_command(version=self.version_id, minecraft_directory=minecraft_directory, options=options))
        self.reset_progress_bar()  # добавлен вызов метода для сброса прогресс-бара и сброса флага


    def start_install_thread(self):
        if not self.installing:  # проверяем, что установка не идет
            self.reset_progress_bar()  # установить прогресс-бар в ноль
            self.progress_bar.start()
            self.install_thread_id = self.after(0, self.install_minecraft)
            self.installing = True  # устанавливаем флаг при начале установки

    def stop_install_thread(self):
        if self.install_thread_id is not None:
            self.after_cancel(self.install_thread_id)
            self.install_thread_id = None
            self.installing = False  # сбрасываем флаг при отмене таймера
            self.reset_progress_bar()  # установить прогресс-бар в ноль

    def launch_game(self):
        self.version_id = self.version_optionmenu.get()
        self.username = self.nick_entry.get()
        self.version_label.configure(text=f"Запускается версия: {self.version_id}")  # Обновляем текст
        self.start_install_thread()
        
    def open_minecraft_folder(self):
        minecraft_directory = os.path.join(os.path.expanduser("~"), 'AppData', 'Roaming', '.minecraft')
        os.startfile(minecraft_directory)

    def get_all_versions(self):
        minecraft_versions = [version['id'] for version in get_version_list()]
        forge_versions = self.get_all_forge_versions()
        return minecraft_versions + forge_versions

    def get_all_forge_versions(self):
        all_forge_versions = []
        for minecraft_version in get_version_list():
            forge_versions = find_forge_version(minecraft_version['id'])
            if forge_versions:
                all_forge_versions.extend(forge_versions)
        return all_forge_versions if all_forge_versions else ["No Forge versions available"]
    
    def show_notification(self, message):
        title = "re:Craft"
        notification_thread = threading.Thread(target=self.toaster.show_toast, args=(title, message), kwargs={'duration': 10})
        notification_thread.start()

    def __del__(self):
        # Восстановление стандартного вывода перед завершением программы
        sys.stdout = self.original_stdout

    class TextRedirector(io.TextIOBase):
        def __init__(self, widget, tag="stdout"):
            self.widget = widget
            self.tag = tag

        def write(self, str):
            self.widget.configure(state="normal")
            self.widget.insert("end", str, (self.tag,))
            self.widget.see("end")  # Прокрутка до конца
            self.widget.configure(state="disabled")

    '''
    def update_greeting(self):
        current_time = datetime.datetime.now().time()

        if datetime.time(0, 0) <= current_time < datetime.time(3, 0):
            greeting = "Доброй ночи"
        elif datetime.time(4, 0) <= current_time < datetime.time(11, 0):
            greeting = "Доброе утро"
        elif datetime.time(12, 0) <= current_time < datetime.time(16, 0):
            greeting = "Добрый день"
        elif datetime.time(17, 0) <= current_time < datetime.time(23, 0):
            greeting = "Добрый вечер"
        else:
            greeting = "Доброго времени суток"

        self.home_frame_label.configure(text=greeting)'''
        
    def toggle_greeting(self):
        # Если переключатель в положении "выключено", скрываем приветствие
        if self.greeting_switch_var.get() == "off":
            self.home_frame_label.grid_remove()
        # Если переключатель в положении "включено", отображаем приветствие
        else:
            self.home_frame_label.grid()

    def update_terminal(self, log_stream):
        # Получаем все, что было записано в буфер
        logs = log_stream.getvalue()
        if logs:
            # Вставляем логи в терминал
            self.output_text.insert("end", logs)
            self.output_text.see("end")
        # Очищаем буфер
        log_stream.truncate(0)
        log_stream.seek(0)
        # Повторяем обновление терминала через некоторое время
        self.after(100, self.update_terminal, log_stream)

    # Метод для обновления приветствия
    def update_randomgreeting(self):
        if self.random_greeting_switch.get() == 'on':
            greeting = random.choice(self.greetings)
        else:
            greeting = "Добро пожаловать в re:Craft!"
        self.home_frame_large_image_label.configure(text=greeting)

        # Метод для генерации случайного кода
    def generate_random_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

    # Метод для создания файла с настройками
    def create_settings_file(self):
        random_code = self.generate_random_code()
        settings = {'random_code': random_code}
        with open(self.settings_file_path, 'w') as file:
            json.dump(settings, file, indent=4)

    # Метод для загрузки настроек из файла
    def load_settings(self):
        with open(self.settings_file_path, 'r') as file:
            self.settings = json.load(file)

    def update_random_code_label(self):
        # Загружаем случайный код из настроек
        random_code = self.settings.get('random_code', 'Unknown')
        # Обновляем текстовую метку с случайным кодом
        self.code.configure(text=f"ID: {random_code}")

if __name__ == "__main__":
    app = recraftMC()
    app.update_random_code_label()
    app.mainloop()