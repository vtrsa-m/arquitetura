import os
import cpu

# Variavel para direcionar os arquivos 

pasta_dos_arquivos = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arquivos")
if not os.path.exists(pasta_dos_arquivos):
    os.makedirs(pasta_dos_arquivos)

# Arquivos usados pelo simulador
# cada um guarda uma parte diferente
# do estado da máquina durante a execução

EN = "entrada.txt"
B_R = os.path.join(pasta_dos_arquivos, "banco_registradores.txt")
U_C = os.path.join(pasta_dos_arquivos, "unidade_controle.txt")
M_R = os.path.join(pasta_dos_arquivos, "memoria_ram.txt")

def ler_arquivo_entrada():

    pasta_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_txt = os.path.join(pasta_atual, EN)

    # Sem um arquivo de entrada
    # não existe programa para carregar
    # então a execução é interrompida logo no começo
    if not os.path.exists(caminho_txt):
        print("Erro na leitura do arquivo!")
        return False

    try:
        with open(caminho_txt, "r") as f:

            # Os espaços são removidos
            # porque eles não mudam o significado da instrução
            # e só dificultariam a leitura dos dados
            linhas = [
                linha.strip().replace(" ", "")
                for linha in f
                if linha.strip()
            ]

        # A RAM só tem espaço para 32 posições
        # então qualquer instrução que passar desse limite
        # acaba sendo ignorada
        for i, linha in enumerate(linhas[:32]):
            if len(linha) == 16:
                cpu.ram[i] = linha

        return True

    except IOError:
        print("Erro ao tentar acessar o arquivo de entrada!")
        return False


def salvar_arquivos_saida():

    try:

        # Cada estrutura da máquina é salva
        # em um arquivo diferente para facilitar
        # a conferência dos resultados depois
        # que a simulação termina

        with open(U_C, "w") as f:
            f.write(f"PC: {cpu.ponteiro_pc}\n")

            # O IR normalmente guarda uma instrução em binário
            # mas essa verificação garante que ele seja salvo certo
            # mesmo se tiver outro tipo de valor
            if isinstance(cpu.reg_instrucao_ir, int):
                f.write(f"IR: {cpu.reg_instrucao_ir:016b}\n")
            else:
                f.write(f"IR: {cpu.reg_instrucao_ir}\n")

        with open(B_R, "w") as f:
            for i, valor in enumerate(cpu.regs):
                f.write(f"R{i}: {valor}\n")

        with open(M_R, "w") as f:
            for i, conteudo in enumerate(cpu.ram):

                # A memória pode conter tanto instruções
                # quanto valores gravados durante a execução
                # então cada tipo de dado é salvo
                # no formato que faz mais sentido
                if isinstance(conteudo, int):
                    f.write(
                        f"Posicao {i:02d}: {(conteudo & 0xFFFF):016b}\n"
                    )
                else:
                    f.write(f"Posicao {i:02d}: {conteudo}\n")

    except IOError:
        print("Erro na escrita dos arquivos de saída!")
