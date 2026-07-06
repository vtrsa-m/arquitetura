import os # Importa a biblioteca para manipulação de arquivos
# Constantes para os nomes dos arquivos
B_R = "banco_registradores.txt"
EN = "entrada.txt"
U_C = "unidade_controle.txt"
M_R = "memoria_ram.txt"

# Declaração das estruturas de hardware da máquina
ram = [0] * 32                           # Memória principal contendo 32 posições de 16 bits
regs = [0] * 4                           # Banco de registradores de uso geral (R0 a R3)
ponteiro_pc = 0                          # Program Counter (aponta para o endereço da instrução)
reg_instrucao_ir = "0000000000000000"    # Instruction Register (guarda a instrução em execução)

# Flags de controle de estado da UULA
flag_zero = False
flag_negativo = False
rodando = True                           # Flag que controla o loop de execução da CPU

def atualizar_flags(resultado):          # Atualiza as flags da UULA após operações aritméticas
    global flag_zero, flag_negativo
    resultado = (resultado + 2**15) % 2**16 - 2**15 # Mantém o valor no limite de 16 bits assinados
    flag_zero = (resultado == 0)
    flag_negativo = (resultado < 0)
    return resultado & 0xFFFF

def ler_arquivo_entrada():               # Função que faz a leitura das instruções do arquivo de entrada
    global ram
    pasta_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_txt = os.path.join(pasta_atual, EN)
    
    if not os.path.exists(caminho_txt):  # Caso o arquivo não exista, interrompe a execução
        print("Erro na leitura do arquivo!")
        return False
        
    try:
        with open(caminho_txt, "r") as f:
            # Divide e formata as linhas ignorando espaços vazios
            linhas = [linha.strip().replace(" ", "") for linha in f if linha.strip()]
            
        for i, linha in enumerate(linhas[:32]): # Carrega no máximo 32 posições na RAM
            if len(linha) == 16:
                ram[i] = linha
        return True
    except IOError:
        print("Erro ao tentar acessar o arquivo de entrada!")
        return False

def executar_processador():              # Executa o ciclo de busca, decodificação e execução da CPU
    global ponteiro_pc, reg_instrucao_ir, rodando, ram, regs
    
    while rodando and ponteiro_pc < 32:
        instrucao_atual = ram[ponteiro_pc] # Busca a instrução na memória RAM (Fetch)
        
        if isinstance(instrucao_atual, int) and instrucao_atual == 0:
            instrucao_atual = "0000000000000000" # Evita erros caso leia uma posição vazia da RAM, tranformando o 0 em "0000000000000000" para manter o mesmo padrão
            
        reg_instrucao_ir = instrucao_atual # Atualiza o valor atual do IR
        ponteiro_pc += 1                   # Incrementa o PC para apontar para a próxima instrução
        
        # A partir daqui teremos diferentes grupos de instruções sendo decodificadas por fatiamento
        
        if reg_instrucao_ir == "1111111111111111": # Instrução HALT: interrompe a máquina
            rodando = False
            break
            
        elif reg_instrucao_ir == "0000000000000000": # Instrução NOP: não realiza nenhuma operação
            continue
            
        # Grupo de Desvios (BRANCH, BZERO, BNEG)
        elif reg_instrucao_ir.startswith("0000"): # Checa se a instrução é do grupo de desvio pelo começo em "0000"
            tipo_desvio = reg_instrucao_ir[4:8]
            destino_ram = int(reg_instrucao_ir[11:16], 2) # Converte os 5 bits de endereço para inteiro
            
            if tipo_desvio == "0001":      # BRANCH incondicional
                ponteiro_pc = destino_ram
            elif tipo_desvio == "0010" and flag_zero:     # BZERO: desvia se a flag zero for verdadeira
                ponteiro_pc = destino_ram
            elif tipo_desvio == "0011" and flag_negativo: # BNEG: desvia se a flag negativo for verdadeira
                ponteiro_pc = destino_ram

        # Grupo de Carregamento e Armazenamento (LOAD, STORE)
        elif reg_instrucao_ir.startswith("1000"): # Checa se a instrução é do grupo de carregamento e armazenamento pelo começo em "1000"
            operacao = reg_instrucao_ir[4:8]              # Identifica a operação (LOAD ou STORE)
            num_reg = int(reg_instrucao_ir[9:11], 2)      # Identifica o registrador (2 bits)
            num_mem = int(reg_instrucao_ir[11:16], 2)     # Identifica a posição da memória RAM (5 bits)
            
            if operacao == "0001":         # LOAD: carrega valor da RAM para o registrador
                valor_ram = ram[num_mem]
                if isinstance(valor_ram, str):
                    regs[num_reg] = int(valor_ram, 2)     # Converte texto binário para inteiro
                else:
                    regs[num_reg] = valor_ram
            elif operacao == "0010":       # STORE: salva valor do registrador na RAM
                ram[num_mem] = regs[num_reg]

        # Grupo de Movimentação entre Registradores (MOVE)
        elif reg_instrucao_ir.startswith("100100010000"):
            reg_destino = int(reg_instrucao_ir[12:14], 2)
            reg_origem = int(reg_instrucao_ir[14:16], 2)
            regs[reg_destino] = regs[reg_origem] # Copia o valor entre os registradores

        # Grupo Lógico e Aritmético da UULA (ADD, SUB, AND, OR)
        elif reg_instrucao_ir.startswith("1010"):
            op_uula = reg_instrucao_ir[4:8]
            r1 = int(reg_instrucao_ir[10:12], 2) # Registrador destino
            r2 = int(reg_instrucao_ir[12:14], 2) # Primeiro operando
            r3 = int(reg_instrucao_ir[14:16], 2) # Segundo operando
            
            val2 = regs[r2]
            val3 = regs[r3]
            
            if op_uula == "0001":          # ADD: soma e atualiza flags
                regs[r1] = atualizar_flags(val2 + val3)
            elif op_uula == "0010":        # SUB: subtração e atualiza flags
                regs[r1] = atualizar_flags(val2 - val3)
            elif op_uula == "0011":        # AND: operação lógica E
                regs[r1] = atualizar_flags(val2 & val3)
            elif op_uula == "0100":        # OR: operação lógica OU
                regs[r1] = atualizar_flags(val2 | val3)

def salvar_arquivos_saida():             # Escreve o estado final do sistema nos arquivos de saída
    try:
        # Escreve os dados da Unidade de Controle
        with open(U_C, "w") as f:                       # Abre o arquivo da Unidade de Controle em modo de escrita 
            f.write(f"PC: {ponteiro_pc}\n") 
            if isinstance(reg_instrucao_ir, int):       # Caso o IR seja um inteiro, escreve em formato binário de 16 bits 
                f.write(f"IR: {reg_instrucao_ir:016b}\n")
            else:
                f.write(f"IR: {reg_instrucao_ir}\n")    # Caso o IR seja uma string, escreve diretamente no arquivo
                
        # Escreve os dados do Banco de Registradores
        with open(B_R, "w") as f:                       # Abre o arquivo do Banco de Registradores em modo de escrita
            for i, valor in enumerate(regs):            
                f.write(f"R{i}: {valor}\n")             # Escreve o valor do registrador no arquivo, cada um em uma linha
                
        # Escreve os dados da Memória RAM
        with open(M_R, "w") as f:                       # Abre o arquivo da Memória RAM em modo de escrita
            for i, conteudo in enumerate(ram):
                if isinstance(conteudo, int):           # Caso o conteúdo seja um inteiro, escreve a posição formatada em dois digitos e o valor em binário de 16 bits
                    f.write(f"Posicao {i:02d}: {(conteudo & 0xFFFF):016b}\n")
                else:
                    f.write(f"Posicao {i:02d}: {conteudo}\n")
    except IOError:
        print("Erro na escrita dos arquivos de saída!")

if __name__ == "__main__":
    print("Iniciando a execução do processador...")
    if ler_arquivo_entrada():
        print("Arquivo de entrada lido com sucesso.")
        executar_processador()
        print("Execução do processador finalizada.")
        salvar_arquivos_saida()
        print("Arquivos de saída gerados com sucesso.")