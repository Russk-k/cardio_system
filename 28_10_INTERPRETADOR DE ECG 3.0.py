import wfdb
import matplotlib
matplotlib.use("TkAgg")  # garante compatibilidade com Tkinter
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import Rectangle
import os
from glob import glob
import tkinter as tk
from tkinter import simpledialog
from playsound import playsound

# ------------------ CONFIGURAÇÃO INICIAL ------------------
# Diretório com os registros (caminho Linux)
data_dir = "/home/pi/cardio_system/mit-bih-arrhythmia-database-1.0.0"
record_files = [os.path.splitext(os.path.basename(f))[0] for f in glob(os.path.join(data_dir, "*.dat"))]

# Cria interface simples para escolher o registro
root = tk.Tk()
root.withdraw()  # esconde a janela principal

record_name = simpledialog.askstring(
    "Escolha o registro",
    f"Registros disponíveis:\n{', '.join(record_files)}\n\nDigite o nome do registro:"
)
if record_name is None or record_name.strip() == "":
    raise SystemExit("Nenhum registro selecionado. Programa encerrado.")

record_path = os.path.join(data_dir, record_name)

# Lê o sinal ECG
record = wfdb.rdrecord(record_path)
signal = record.p_signal[:, 0]
fs = int(record.fs)

# Lê anotações de arritmia
ann = wfdb.rdann(record_path, 'atr')
samples = ann.sample
symbols = ann.symbol

# Dicionário com nomes das arritmias
arrhythmia_dict = {
    'N': 'Normal',
    'L': 'Bloqueio de Ramo Esquerdo',
    'R': 'Bloqueio de Ramo Direito',
    'A': 'Batimento Atrial Prematuro',
    'V': 'Batimento Ventricular Prematuro',
    'F': 'Fusão de Batimentos',
    'f': 'Fusão Atrial-Ventricular',
    'Q': 'Batimento Aberrante',
    '/': 'Ruído ou Indefinido'
}

# Pasta para salvar prints
if not os.path.exists('arrhythmia_screenshots'):
    os.makedirs('arrhythmia_screenshots')

# ------------------ FUNÇÃO DE ALARME ------------------
def play_alarm():
    for _ in range(3):
        playsound("alarm.wav")  # Coloque um arquivo alarm.wav no diretório

# ---------------