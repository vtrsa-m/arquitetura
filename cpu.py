# Estado inicial do processador
# tudo começa zerado para simular uma máquina
# que acabou de ser ligada
# e ainda não executou nenhuma instrução
ram = [0] * 32
regs = [0] * 4

ponteiro_pc = 0
reg_instrucao_ir = "0000000000000000"

flag_zero = False
flag_negativo = False
rodando = True


def atualizar_flags(resultado):
    global flag_zero, flag_negativo

    # A ULA trabalha com números de 16 bits
    # então o resultado precisa ser ajustado para esse limite
    # antes de atualizar as flags e continuar a execução
    resultado = (resultado + 2**15) % 2**16 - 2**15

    flag_zero = (resultado == 0)
    flag_negativo = (resultado < 0)

    return resultado & 0xFFFF


def executar_processador():
    global ponteiro_pc, reg_instrucao_ir, rodando, ram, regs

    while rodando and ponteiro_pc < 32:

        instrucao_atual = ram[ponteiro_pc]

        # A RAM começa preenchida com inteiros
        # mas as instruções ficam salvas como texto em binário
        # então essa conversão evita ter que ficar verificando isso
        # o tempo todo
        if isinstance(instrucao_atual, int) and instrucao_atual == 0:
            instrucao_atual = "0000000000000000"

        reg_instrucao_ir = instrucao_atual

        # O PC já é atualizado depois que a instrução entra no IR
        # então se acontecer um desvio
        # é só trocar esse valor pelo novo endereço
        ponteiro_pc += 1

        # Cada grupo de instruções segue um formato diferente
        # então separar esse tratamento deixa a leitura
        # mais organizada e facilita fazer alterações depois

        if reg_instrucao_ir == "1111111111111111":
            rodando = False
            break

        elif reg_instrucao_ir == "0000000000000000":
            continue
        # Grupo de instruções de desvio
        elif reg_instrucao_ir.startswith("0000"):

            tipo_desvio = reg_instrucao_ir[4:8]
            destino_ram = int(reg_instrucao_ir[11:16], 2)

            # O endereço de destino já vem na própria instrução
            # então se a condição for atendida
            # é só substituir o valor atual do PC
            if tipo_desvio == "0001":
                ponteiro_pc = destino_ram

            elif tipo_desvio == "0010" and flag_zero:
                ponteiro_pc = destino_ram

            elif tipo_desvio == "0011" and flag_negativo:
                ponteiro_pc = destino_ram
        # Grupo de instruções de memória
        elif reg_instrucao_ir.startswith("1000"):

            operacao = reg_instrucao_ir[4:8]
            num_reg = int(reg_instrucao_ir[9:11], 2)
            num_mem = int(reg_instrucao_ir[11:16], 2)

            if operacao == "0001":

                valor_ram = ram[num_mem]

                # Quando o valor veio do arquivo
                # ele ainda está como texto em binário
                # então ele é convertido antes
                # de ir para o registrador
                if isinstance(valor_ram, str):
                    regs[num_reg] = int(valor_ram, 2)
                else:
                    regs[num_reg] = valor_ram

            elif operacao == "0010":
                ram[num_mem] = regs[num_reg]
        # Grupo de instruções de registradores
        elif reg_instrucao_ir.startswith("100100010000"):

            reg_destino = int(reg_instrucao_ir[12:14], 2)
            reg_origem = int(reg_instrucao_ir[14:16], 2)

            # O MOVE só copia um valor de um registrador para outro
            # então não faz sentido alterar as flags
            # já que nenhum cálculo foi realizado
            regs[reg_destino] = regs[reg_origem]
        # Grupo de instruções da ULA
        elif reg_instrucao_ir.startswith("1010"):

            op_uula = reg_instrucao_ir[4:8]

            r1 = int(reg_instrucao_ir[10:12], 2)
            r2 = int(reg_instrucao_ir[12:14], 2)
            r3 = int(reg_instrucao_ir[14:16], 2)

            val2 = regs[r2]
            val3 = regs[r3]

            # Todas as operações passam pela mesma função
            # de atualização das flags para evitar repetir
            # a mesma lógica em cada operação da ULA
            if op_uula == "0001":
                regs[r1] = atualizar_flags(val2 + val3)

            elif op_uula == "0010":
                regs[r1] = atualizar_flags(val2 - val3)

            elif op_uula == "0011":
                regs[r1] = atualizar_flags(val2 & val3)

            elif op_uula == "0100":
                regs[r1] = atualizar_flags(val2 | val3)
