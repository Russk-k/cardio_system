import wfdb
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import Rectangle
import pygame
import time
import os
from glob import glob
import tkinter as tk
from tkinter import simpledialog

# ------------------ CONFIGURAÇÃO INICIAL ------------------
# Diretorio com os registros
data_dir = r"/home/russk/cardio_system/mit-bih-arrhythmia-database-1.0.0/"
record_files = [os.path.splitext(os.path.basename(f))[0] for f in glob(os.path.join(data_dir, "*.dat"))]

# Cria interface simples para escolher o registro
root = tk.Tk()
root.withdraw()  # esconde a janela principal

record_name = simpledialog.askstring("Escolha o registro",
                                     f"Registros disponíveis:\n{', '.join(record_files)}\n\nDigite o nome do registro:")
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
pygame.mixer.init()

def play_alarm():
    pygame.mixer.music.load("alarm.wav")  
    for _ in range(3):
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

# ------------------ GRÁFICO PRINCIPAL ------------------
fig, ax = plt.subplots(figsize=(12, 5))
ax.set_xlim(0, 10)
ax.set_ylim(-2, 2)
line, = ax.plot([], [], color='black', lw=1.2, label='ECG')
beat_points, = ax.plot([], [], 'ro', markersize=4, label='Batimentos')
text_annotations = []
qrs_rects = []

ax.set_xlabel('Tempo (s)')
ax.set_ylabel('Amplitude (mV)')
ax.set_title(f'ECG: {record_name}', fontsize=12)
ax.legend()

# Grade
x_minor = np.arange(0, 10, 0.04)
x_major = np.arange(0, 10, 0.2)
y_minor = np.arange(-2, 2, 0.1)
y_major = np.arange(-2, 2, 0.5)
ax.set_xticks(x_major)
ax.set_xticks(x_minor, minor=True)
ax.set_yticks(y_major)
ax.set_yticks(y_minor, minor=True)
ax.grid(which='major', color='red', linestyle='-', linewidth=0.8, alpha=0.6)
ax.grid(which='minor', color='red', linestyle='-', linewidth=0.3, alpha=0.3)

# ------------------ JANELA DE ARRITMIA ------------------
fig_arr, ax_arr = plt.subplots(figsize=(8, 4))
ax_arr.set_title('Última Arritmia Detectada')
ax_arr.set_xlabel('Tempo (s)')
ax_arr.set_ylabel('Amplitude (mV)')
line_arr, = ax_arr.plot([], [], color='black', lw=1.5)
highlight_rect = None
ax_arr.grid(True)
plt.show(block=False)

# ------------------ ANIMAÇÃO ------------------
xdata, ydata = [], []
beat_x, beat_y = [], []

def init():
    line.set_data([], [])
    beat_points.set_data([], [])
    for t in text_annotations:
        t.remove()
    text_annotations.clear()
    return [line, beat_points]

def update(frame):
    global xdata, ydata, beat_x, beat_y, text_annotations, qrs_rects, line_arr, highlight_rect

    start = frame * fs
    end = start + fs
    if end > len(signal):
        end = len(signal)

    new_x = np.arange(start, end) / fs
    new_y = signal[start:end]
    xdata.extend(new_x)
    ydata.extend(new_y)

    # Remove textos antigos
    for t in text_annotations:
        t.remove()
    text_annotations.clear()

    # Batimentos no frame
    mask = (samples >= start) & (samples < end)
    for i, (s, sym) in enumerate(zip(samples[mask], np.array(symbols)[mask])):
        beat_x.append(s / fs)
        beat_y.append(signal[s])

        if sym != 'N':
            # QRS principal
            qrs_start = int(max(s - 0.08*fs, 0))
            qrs_end = int(min(s + 0.08*fs, len(signal)))
            qrs_min = np.min(signal[qrs_start:qrs_end])
            qrs_max = np.max(signal[qrs_start:qrs_end])
            rect = Rectangle((qrs_start/fs, qrs_min),
                             (qrs_end - qrs_start)/fs,
                             qrs_max - qrs_min,
                             color='yellow', alpha=0.3)
            ax.add_patch(rect)
            qrs_rects.append(rect)

            text = ax.text(s / fs, qrs_max + 0.05, sym, color='blue',
                           fontsize=9, ha='center', fontweight='bold')
            text_annotations.append(text)
            play_alarm()

            # ------------------ TRÊS QRS NA JANELA DE ARRITMIA ------------------
            all_beats = np.array(samples)
            idx_current = np.where(all_beats == s)[0][0]
            idx_prev = max(idx_current - 1, 0)
            idx_next = min(idx_current + 1, len(all_beats)-1)

            start_idx = int(max(all_beats[idx_prev] - 0.08*fs, 0))
            end_idx = int(min(all_beats[idx_next] + 0.08*fs, len(signal)))
            arr_x = np.arange(start_idx, end_idx) / fs
            arr_y = signal[start_idx:end_idx]

            line_arr.set_data(arr_x, arr_y)
            ax_arr.set_xlim(arr_x[0], arr_x[-1])
            ax_arr.set_ylim(np.min(arr_y)-0.2, np.max(arr_y)+0.2)
            ax_arr.set_title(f'Arritmia detectada: {arrhythmia_dict.get(sym, sym)}\nTempo aprox.: {s/fs:.2f}s')

            # Destaca o QRS do meio
            if highlight_rect:
                highlight_rect.remove()
            mid_start = int(max(s - 0.08*fs, 0))
            mid_end = int(min(s + 0.08*fs, len(signal)))
            mid_min = np.min(signal[mid_start:mid_end])
            mid_max = np.max(signal[mid_start:mid_end])
            highlight_rect = Rectangle((mid_start/fs, mid_min),
                                       (mid_end - mid_start)/fs,
                                       mid_max - mid_min,
                                       color='yellow', alpha=0.3)
            ax_arr.add_patch(highlight_rect)

            fig_arr.canvas.draw()
            fig_arr.canvas.flush_events()

            # Salva print
            filename = f"arrhythmia_screenshots/{record_name}_arritmia_{sym}_{int(s/fs*100)}ms.png"
            fig_arr.savefig(filename, dpi=150)
            print(f"Print salvo: {filename}")

    line.set_data(xdata, ydata)
    beat_points.set_data(beat_x, beat_y)

    if xdata[-1] > 10:
        ax.set_xlim(xdata[-1] - 10, xdata[-1])

    return [line, beat_points, *qrs_rects, *text_annotations]

ani = animation.FuncAnimation(fig, update,
                              frames=range(len(signal)//fs),
                              init_func=init,
                              blit=True,
                              interval=1000,
                              repeat=False)

plt.tight_layout()
plt.show()