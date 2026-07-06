#!/bin/python3

import os
import tkinter as tk
from tkinter import ttk, messagebox

# =====================================================================
# --- PARTE 1: O NOSSO PROCESSADOR (EXATAMENTE IGUAL AO ANTERIOR) ---
# =====================================================================

B_R = "banco_registradores.txt"
EN = "entrada.txt"
U_C = "unidade_controle.txt"
M_R = "memoria_ram.txt"

ram = [0] * 32
regs = [0] * 4
ponteiro_pc = 0
reg_instrucao_ir = "0000000000000000"

flag_zero = False
flag_negativo = False
rodando = True

def atualizar_flags(resultado):
    global flag_zero, flag_negativo
    resultado = (resultado + 2**15) % 2**16 - 2**15
    flag_zero = (resultado == 0)
    flag_negativo = (resultado < 0)
    return resultado & 0xFFFF

def rodar_simulacao_completa():
    """Roda todo o ciclo da CPU pegando o entrada.txt e gerando os arquivos."""
    global ram, regs, ponteiro_pc, reg_instrucao_ir, flag_zero, flag_negativo, rodando
    
    # Reseta o hardware antes de rodar
    ram = [0] * 32
    regs = [0] * 4
    ponteiro_pc = 0
    reg_instrucao_ir = "0000000000000000"
    flag_zero = flag_negativo = False
    rodando = True
    
    pasta_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_txt = os.path.join(pasta_atual, EN)
    
    if not os.path.exists(caminho_txt):
        return False
        
    with open(caminho_txt, "r") as f:
        linhas = [linha.strip().replace(" ", "") for linha in f if linha.strip()]
        
    for i, linha in enumerate(linhas[:32]):
        if len(linha) == 16:
            ram[i] = linha
            
    while rodando and ponteiro_pc < 32:
        instrucao_atual = ram[ponteiro_pc]
        if isinstance(instrucao_atual, int) and instrucao_atual == 0:
            instrucao_atual = "0000000000000000"
            
        reg_instrucao_ir = instrucao_atual
        ponteiro_pc += 1
        
        if reg_instrucao_ir == "1111111111111111":
            rodando = False
            break
        elif reg_instrucao_ir == "0000000000000000":
            continue
            
        elif reg_instrucao_ir.startswith("0000"):
            tipo_desvio = reg_instrucao_ir[4:8]
            destino_ram = int(reg_instrucao_ir[11:16], 2)
            if tipo_desvio == "0001":
                ponteiro_pc = destino_ram
            elif tipo_desvio == "0010" and flag_zero:
                ponteiro_pc = destino_ram
            elif tipo_desvio == "0011" and flag_negativo:
                ponteiro_pc = destino_ram

        elif reg_instrucao_ir.startswith("1000"):
            operacao = reg_instrucao_ir[4:8]
            num_reg = int(reg_instrucao_ir[9:11], 2)
            num_mem = int(reg_instrucao_ir[11:16], 2)
            if operacao == "0001":
                valor_ram = ram[num_mem]
                regs[num_reg] = int(valor_ram, 2) if isinstance(valor_ram, str) else valor_ram
            elif operacao == "0010":
                ram[num_mem] = regs[num_reg]

        elif reg_instrucao_ir.startswith("100100010000"):
            reg_destino = int(reg_instrucao_ir[12:14], 2)
            reg_origem = int(reg_instrucao_ir[14:16], 2)
            regs[reg_destino] = regs[reg_origem]

        elif reg_instrucao_ir.startswith("1010"):
            op_uula = reg_instrucao_ir[4:8]
            r1 = int(reg_instrucao_ir[10:12], 2)
            r2 = int(reg_instrucao_ir[12:14], 2)
            r3 = int(reg_instrucao_ir[14:16], 2)
            val2, val3 = regs[r2], regs[r3]
            if op_uula == "0001":
                regs[r1] = atualizar_flags(val2 + val3)
            elif op_uula == "0010":
                regs[r1] = atualizar_flags(val2 - val3)
            elif op_uula == "0011":
                regs[r1] = atualizar_flags(val2 & val3)
            elif op_uula == "0100":
                regs[r1] = atualizar_flags(val2 | val3)

    # Salva arquivos
    with open(U_C, "w") as f:
        f.write(f"PC: {ponteiro_pc}\nIR: {reg_instrucao_ir if isinstance(reg_instrucao_ir, str) else f'{reg_instrucao_ir:016b}'}\n")
    with open(B_R, "w") as f:
        for i, valor in enumerate(regs):
            f.write(f"R{i}: {valor}\n")
    with open(M_R, "w") as f:
        for i, conteudo in enumerate(ram):
            f.write(f"Posicao {i:02d}: {conteudo if isinstance(conteudo, str) else f'{(conteudo & 0xFFFF):016b}'}\n")
    return True


# =====================================================================
# --- PARTE 2: A INTERFACE GRÁFICA E MONTADOR (ASSEMBLER) ---
# =====================================================================

programa_binario = []  # Guarda as linhas binárias que serão salvas no entrada.txt

def traduzir_para_binario():
    """Pega as opções selecionadas na tela e converte para código de máquina de 16 bits."""
    op = combo_op.get()
    
    try:
        if op == "HALT":
            return "1111111111111111", "HALT"
        elif op == "NOP":
            return "0000000000000000", "NOP"
            
        elif op == "DADO_NUMERICO": # Para colocar números puros na RAM (ex: 5, 3)
            num = int(entry_p1.get())
            binario = f"{(num & 0xFFFF):016b}"
            return binario, f"DADO: {num}"
            
        elif op in ["LOAD", "STORE"]:
            reg = int(entry_p1.get())
            mem = int(entry_p2.get())
            cod = "0001" if op == "LOAD" else "0010"
            binario = f"1000{cod}0{reg:02b}{mem:05b}"
            return binario, f"{op} R{reg} {mem}"
            
        elif op == "MOVE":
            rd = int(entry_p1.get())
            ro = int(entry_p2.get())
            binario = f"100100010000{rd:02b}{ro:02b}"
            return binario, f"MOVE R{rd} R{ro}"
            
        elif op in ["ADD", "SUB", "AND", "OR"]:
            r1 = int(entry_p1.get())
            r2 = int(entry_p2.get())
            r3 = int(entry_p3.get())
            cod_map = {"ADD": "0001", "SUB": "0010", "AND": "0011", "OR": "0100"}
            binario = f"1010{cod_map[op]}00{r1:02b}{r2:02b}{r3:02b}"
            return binario, f"{op} R{r1} R{r2} R{r3}"
            
        elif op in ["BRANCH", "BZERO", "BNEG"]:
            mem = int(entry_p1.get())
            cod_map = {"BRANCH": "0001", "BZERO": "0010", "BNEG": "0011"}
            binario = f"0000{cod_map[op]}000{mem:05b}"
            return binario, f"{op} {mem}"
            
    except ValueError:
        messagebox.showerror("Erro", "Preencha os parâmetros corretamente com números inteiros!")
        return None, None

def adicionar_instrucao():
    if len(programa_binario) >= 32:
        messagebox.showwarning("Aviso", "Memória cheia! Máximo de 32 instruções.")
        return
        
    binario, texto = traduzir_para_binario()
    if binario:
        programa_binario.append(binario)
        pos = len(programa_binario) - 1
        lista_vis.insert(tk.END, f"[{pos:02d}] {binario}  ({texto})")

def limpar_tudo():
    programa_binario.clear()
    lista_vis.delete(0, tk.END)
    txt_uc.delete(1.0, tk.END)
    txt_br.delete(1.0, tk.END)
    txt_ram.delete(1.0, tk.END)

def executar_e_mostrar():
    if not programa_binario:
        messagebox.showwarning("Aviso", "Adicione pelo menos uma instrução!")
        return
        
    # 1. Escreve no entrada.txt automaticamente
    pasta_atual = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(pasta_atual, EN), "w") as f:
        for linha in programa_binario:
            f.write(linha + "\n")
            
    # 2. Roda o simulador
    sucesso = rodar_simulacao_completa()
    
    if sucesso:
        # 3. Lê os arquivos gerados e exibe na tela
        with open(os.path.join(pasta_atual, U_C)) as f:
            txt_uc.delete(1.0, tk.END)
            txt_uc.insert(tk.END, f.read())
            
        with open(os.path.join(pasta_atual, B_R)) as f:
            txt_br.delete(1.0, tk.END)
            txt_br.insert(tk.END, f.read())
            
        with open(os.path.join(pasta_atual, M_R)) as f:
            txt_ram.delete(1.0, tk.END)
            txt_ram.insert(tk.END, f.read())
            
        messagebox.showinfo("Sucesso", "Simulação concluída! Arquivos de saída gerados.")

def atualizar_campos(event=None):
    """Muda os nomes dos campos de texto dependendo da instrução selecionada."""
    op = combo_op.get()
    # Esconde todos primeiro
    lbl_p1.grid_remove(); entry_p1.grid_remove()
    lbl_p2.grid_remove(); entry_p2.grid_remove()
    lbl_p3.grid_remove(); entry_p3.grid_remove()
    
    if op in ["LOAD", "STORE"]:
        lbl_p1.config(text="Num Registrador (0-3):"); lbl_p1.grid(row=1, column=0, sticky="e")
        entry_p1.grid(row=1, column=1)
        lbl_p2.config(text="Posição RAM (0-31):"); lbl_p2.grid(row=2, column=0, sticky="e")
        entry_p2.grid(row=2, column=1)
    elif op == "MOVE":
        lbl_p1.config(text="Reg Destino (0-3):"); lbl_p1.grid(row=1, column=0, sticky="e")
        entry_p1.grid(row=1, column=1)
        lbl_p2.config(text="Reg Origem (0-3):"); lbl_p2.grid(row=2, column=0, sticky="e")
        entry_p2.grid(row=2, column=1)
    elif op in ["ADD", "SUB", "AND", "OR"]:
        lbl_p1.config(text="Reg Destino (R1):"); lbl_p1.grid(row=1, column=0, sticky="e")
        entry_p1.grid(row=1, column=1)
        lbl_p2.config(text="Reg Operando 1 (R2):"); lbl_p2.grid(row=2, column=0, sticky="e")
        entry_p2.grid(row=2, column=1)
        lbl_p3.config(text="Reg Operando 2 (R3):"); lbl_p3.grid(row=3, column=0, sticky="e")
        entry_p3.grid(row=3, column=1)
    elif op in ["BRANCH", "BZERO", "BNEG"]:
        lbl_p1.config(text="Destino RAM (0-31):"); lbl_p1.grid(row=1, column=0, sticky="e")
        entry_p1.grid(row=1, column=1)
    elif op == "DADO_NUMERICO":
        lbl_p1.config(text="Valor Número Inteiro:"); lbl_p1.grid(row=1, column=0, sticky="e")
        entry_p1.grid(row=1, column=1)

# --- CONSTRUÇÃO DA JANELA ---
janela = tk.Tk()
janela.title("Simulador de Processador - Arquitetura 16 Bits")
janela.geometry("800x550")

frame_esq = tk.LabelFrame(janela, text=" Montador de Programa (Assembler) ", padx=10, pady=10)
frame_esq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

frame_dir = tk.LabelFrame(janela, text=" Resultados e Hardware ", padx=10, pady=10)
frame_dir.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

# Controles de Montagem
tk.Label(frame_esq, text="Operação:").grid(row=0, column=0, sticky="e")
combo_op = ttk.Combobox(frame_esq, values=[
    "LOAD", "STORE", "MOVE", "ADD", "SUB", "AND", "OR", 
    "BRANCH", "BZERO", "BNEG", "NOP", "HALT", "DADO_NUMERICO"
], state="readonly", width=15)
combo_op.current(0)
combo_op.grid(row=0, column=1, pady=5)
combo_op.bind("<<ComboboxSelected>>", atualizar_campos)

lbl_p1 = tk.Label(frame_esq); entry_p1 = tk.Entry(frame_esq, width=10)
lbl_p2 = tk.Label(frame_esq); entry_p2 = tk.Entry(frame_esq, width=10)
lbl_p3 = tk.Label(frame_esq); entry_p3 = tk.Entry(frame_esq, width=10)

btn_add = tk.Button(frame_esq, text="➕ Adicionar Instrução", command=adicionar_instrucao, bg="#d1e7dd")
btn_add.grid(row=4, column=0, columnspan=2, pady=10, sticky="we")

lista_vis = tk.Listbox(frame_esq, font=("Courier", 9))
lista_vis.grid(row=5, column=0, columnspan=2, sticky="nsew")
frame_esq.rowconfigure(5, weight=1)

tk.Button(frame_esq, text="🗑️ Limpar Tudo", command=limpar_tudo).grid(row=6, column=0, columnspan=2, pady=5, sticky="we")

# Painel de Saídas
btn_exec = tk.Button(frame_dir, text="▶️ EXECUTAR SIMULAÇÃO", font=("Arial", 11, "bold"), bg="#cfe2ff", command=executar_e_mostrar)
btn_exec.pack(fill=tk.X, pady=5)

tk.Label(frame_dir, text="Unidade de Controle:", font=("Arial", 9, "bold")).pack(anchor="w")
txt_uc = tk.Text(frame_dir, height=2, font=("Courier", 9), bg="#f8f9fa")
txt_uc.pack(fill=tk.X, pady=2)

tk.Label(frame_dir, text="Banco de Registradores:", font=("Arial", 9, "bold")).pack(anchor="w")
txt_br = tk.Text(frame_dir, height=4, font=("Courier", 9), bg="#f8f9fa")
txt_br.pack(fill=tk.X, pady=2)

tk.Label(frame_dir, text="Memória RAM:", font=("Arial", 9, "bold")).pack(anchor="w")
txt_ram = tk.Text(frame_dir, height=12, font=("Courier", 8), bg="#f8f9fa")
txt_ram.pack(fill=tk.BOTH, expand=True, pady=2)

atualizar_campos() # Inicializa os campos na tela
janela.mainloop()