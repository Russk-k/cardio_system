import os
import sys
import subprocess

# Lista das bibliotecas externas (que precisam de instalação via pip)
dependencias = [
    "wfdb",
    "matplotlib",
    "numpy"
]

# Dependências internas (já vêm com o Python):
# winsound (só Windows)
# os, glob, tkinter — já incluídas no Python

def instalar(pacote):
    """Instala um pacote via pip"""
    try:
        print(f"\nInstalando {pacote}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", pacote])
        print(f"{pacote} instalado com sucesso!\n")
    except subprocess.CalledProcessError:
        print(f"Erro ao instalar {pacote}.\n")

def main():
    print("Iniciando instalação das dependências...\n")
    
    for dep in dependencias:
        instalar(dep)
    
    print("Todas as dependências foram instaladas!\n")

    # Aviso para winsound (não existe no Linux)
    if sys.platform != "win32":
        print("Aviso: o módulo 'winsound' é exclusivo do Windows.")
        print("   No Raspberry Pi, você pode substituir por 'os.system(\"aplay som.wav\")' ou usar a biblioteca 'playsound'.")
        print("   Para instalar 'playsound': pip install playsound\n")

if __name__ == "__main__":
    main()
