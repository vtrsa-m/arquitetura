from arquivos import ler_arquivo_entrada, salvar_arquivos_saida
from cpu import executar_processador

if __name__ == "__main__":

    # A execução só começa depois
    # que o programa é carregado corretamente
    # evitando que a CPU tente executar
    # uma memória inválida

    print("Iniciando a execução do processador...")

    if ler_arquivo_entrada():

        print("Arquivo de entrada lido com sucesso.")

        executar_processador()

        print("Execução do processador finalizada.")

        salvar_arquivos_saida()

        print("Arquivos de saída gerados com sucesso.")