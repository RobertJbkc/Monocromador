
#region Objetivo
# - Um programa que, ao receber o comprimento de onda inicial e final, além do tamanho da fenda e pontos por resolução, move o monocromador para os pontos e realiza 3 ou 5 medidas em cada ponto, calcula média e desvio padrão e armazena os dados (tensão e comprimento de onda) em um arquivo .csv.
# - Criar uma classe para o experimento --> OOP
#   - Integrar a função de movimentar o monocromador
# - Fluxograma
#   - Conectar
#   - Calcular passos
#   - Loop coleta 
#       - Pegar dados
#       - Armazena dados
#       - Mover
#   - Criar um DataFrame
#   - Criar o .csv, incluir dados e metadados
#   - Fim
#endregion ========== Fim do objetivo ==========

#region Observações
# - A função de coleta de dados tem que ser chamda junto com a de criar um .csv.
#endregion


# ========== Imports ==========\
# Deveria estar dentro da classe?
import serial
import matplotlib.pyplot as plt
from time import sleep, perf_counter
# Alt + 0197 --> Å

#region class ComunicaArduino
class ComunicaArduino:
    """
    Classe destinada a facilitar a leitura e escrita ao comunicar-se com a placa Arduino.

    São métodos de leitura e escrita, além de conexão e desconexão da comunicação Serial.
    """

    def __init__(self, porta: str, boundrate: int, timeout: None=None):
        """
        Função constutora para a classe de comunicação Python-Arduino

        Args:
            porta (str): A porta 'COM' em que a placa Arduino está conectada
            boundrate (int): A taxa de comunicação Serial
            timeout (None): O tempo máximo que o python espera por uma resposta. None --> Infinito. Defaults to None.
        """
        self.porta = porta
        self.boundrate = boundrate
        self.timeout = timeout

    # ========== Conexão ==========
    def conectar(self):
        """Cria e abre a conexão entre o Arduino e o computador (Python)"""
        self.conexao = serial.Serial(
            port=self.porta,
            baudrate=self.boundrate,
            timeout=self.timeout
         )
        sleep(0.5)
        print(f'Conectando na porta {self.porta}...')
        sleep(2.5) # Tempo para garanti que a conxão foi aberta
        print(f'Arduino conectado na porta {self.porta}. Canal Serial aberto')

    def desconectar(self):
        """
        Fecha a comunicação entre o Arduino e o computador (Python)
        """
        self.conexao.close()  
    

    # ========== Leitura ==========
    def ler_Serial(self):
        """
        Faz a leitura da saída Serial do Arduino. Lê uma linha e decodifica em "utf-8"

        Returns:
            str: A linha que foi lida, sem espaços e novas linhas
        """

        # "readline()" lê até um "\n"
        saida = self.conexao.readline().decode("utf-8").rstrip()

        return saida
    

    # ========== Escrita ==========
    def escrever(self, mensagem):
        """
        Encia uma mensagem via comunicação Serial para o Arduino. Escreve na porta Serial

        Args:
            mensagem (None): A mensagem que será enviada para o Arduino
        """

        print(f'PC: Enviando [{mensagem}]...')
        mensagem = str(mensagem)
        mensagem_b = mensagem.encode('ascii')
        self.conexao.write(mensagem_b)


    # ========== Métodos (explícitos) ==========
    def mover_motor(self, passos):
        self.escrever(passos)
        saida = self.ler_Serial()
        print(f'Arduino: [{saida}]')


    
#endregion

#region class SR510
class SR510:
    """
    Classe para traduzir o idioma Serial falado pelo Lovk-in SR510 em um idioma de funções Python.
    
    Os métodos são leituras ou escritas de comandos do Lock-in obtidos a partir do manual do equipamento.

    A base de funcionamento é o módulo pySerial.
    """

    def __init__(self, porta, boundrate):
         
         self.porta = porta
         self.boundrate = boundrate
         self.conexao = None


    # ========== Conexão ==========
    def conectar(self):
        """Cria (e abre) a conexão Serial entre computador e Lock-in"""
         
        self.conexao = serial.Serial(
            port=self.porta,
            baudrate=self.boundrate, # Configurado nas chaves 1, 2 e 3
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE, # Configurado nas chaves 4 e 5
            stopbits=serial.STOPBITS_TWO, # O SR510 exige 2 em 9600 baud
            timeout=0.05
         )
        sleep(0.5)
        print(f'Conectando na porta {self.porta}...')
        sleep(2.5) # Tempo para garanti que a conxão foi aberta
        print(f'SR510 conectado na porta {self.porta}. Canal Serial aberto')

    def fechar(self):
        """Fecha a conexão antre computador e Lock-in"""

        if self.conexao:
            self.conexao.close()

    
    # ========== Leitura ==========
    def ler_valor_saida(self):
        """Lê o valor mostrado no LCD de saida"""

        self.conexao.write(b'Q\r') # Envia o comando
        raw = self.conexao.readline().decode('utf-8').strip()
        # try caso venha um valor estranho
        try:
            return float(raw) # Transforma o texto em número
        except ValueError as e:
            print(f'Erro ao converter a resposta "raw" --> float: {e}')
            return None

    def ler_tempo_espera(self):

        self.conexao.write(b'W\r') # Envia o comando
        raw = self.conexao.readline().decode('utf-8')#.strip()
        
        return raw
    
    def ler_sensitividade(self):
        """
        Lê o valor de sensitividade escolhido no Lock-in

        Returns:
            str: A escala em que o Lock-in está informando a tensão
        """

        dicionario_traducao = {
            1: '10 nV',
            2: '20 nV',
            3: '50 nV',
            4: '100 nV',
            5: '200 nV',
            6: '500 nV',
            7: '1 µV',
            8: '2 µV',
            9: '5 µV',
            10: '10 µV',
            11: '20 µV',
            12: '50 µV',
            13: '100 µV',
            14: '200 µV',
            15: '500 µV',
            16: '1 mV',
            17: '2 mV',
            18: '5 mV',
            19: '10 mV',
            20: '20 mV',
            21: '50 mV',
            22: '100 mV',
            23: '200 mV',
            24: '500 mV',
        }
        self.conexao.write(b'G\r')
        raw = self.conexao.readline().decode('utf-8').strip()
        try:
            sensitividade_c = int(raw) # Transforma o texto em número
        except ValueError as e:
            print(f'Erro ao converter a resposta "raw" --> float: {e}')
            sensitividade_c = None

        return dicionario_traducao[sensitividade_c]

    
    # ========== Escrita ==========
    def set_tempo_espera(self, t):

        comando = f'W{t}\r'
        self.conexao.write(comando.encode('ascii')) # Envia o comando
#endregion

#region class Experiento
class Experimento:
    """
    A classe armazena todos os métodos necessários para realizar um experimento com o monocromador conectado ao Lock-in amplifier SR510.
    
    Ela conta com os métodos intermediários e com um método final ".run()" para rodar um experimento inteiro.

    A base de funcionamento é o módulo pySerial.
    """

    # Todo experimento tem isso igual. Verifiar se esse é o estilo correto
    grade = 16 # parametro_de_grade angstrons / mm

    def __init__(self, nome_arquivo: str, operador: str, comp_i: float, comp_f: float, tamanho_fenda: float, ppr: int=5, descricao: str=None):
        """
        Método construtor para a classe Experimento. Seus parâmetros são todos os necessários para rodar um experimeto. Características de um experiemnto.

        Args:
            nome (str): O nome do arquivo .csv em que os dados serão salvos
            comp_i (float): Comprimento de onda inicial (em )
            comp_f (float): Comprimento de onda final (em )
            tamanho_fenda (float): Abertura de fenda definida no monocromador (em )
            ppr (int, optional): "Ponto Por Resolução". Define o número de pontos que será feito dentro da resolução (R) do monocromador. R = tamanho_fenda * (característica da rede de difração). Defaults to 5.
            descricao (str, optional): Uma breve descrição do esperimento que será realizado. Defaults to None.
        """

        # ========== Características iniciais do objeto ==========
        self.nome_arquivo = nome_arquivo
        self.operador = operador
        self.comp_i = comp_i
        self.comp_f = comp_f
        self.tamanho_fenda = tamanho_fenda
        self.ppr = ppr
        self.descricao = descricao

        # ========== Novas características que não são definidas pelo usuário
        self.lista_tensao = []
        self.lista_comprimento_onda = []
        self.comp_atual = self.comp_i
        self.abortar_experimento = False
        self.experimento_concluido = False

        # Para o gráfico
        # self.tamanho_buffer = 100
        self.buffer_x = []
        self.buffer_y = []
        self.fig, self.ax = None, None
        self.ln = None

        #region Metadados
        from datetime import date, datetime
        tempo = datetime.now().time()
        hoje = date.today() # Obtém a data atual (YYYY-MM-DD)
        self.metadados = [
            f'# Experimento: {self.descricao}',
            f'# Data: [{hoje}] [{tempo}]',
            f'# Operador: {self.operador}',
            f'# Comprimento de onda inicial: {self.comp_i}',
            f'# Comprimento de onda final: {self.comp_f}',
            f'# Tamanho da fenda {self.tamanho_fenda}',
            f'# Ponto Por Resolução (PPR): {self.ppr}'
        ]
        #endregion

    # ========== Conexão ==========
    def conectar(self, conexao_lock_in: dict, conexao_arduino: dict):
        """Cria a conexao (abre o canal), por meio de "SR510", com o Lock-in e por meio de "ComunicaArduino" com o Arduino"""

        self.sr510 = SR510(**conexao_lock_in) # Cria o objeto da classe "SR510"
        self.arduino = ComunicaArduino(**conexao_arduino)
        self.sr510.conectar() # Usa o método "conectar()" da classe "SR510" para criar a conexão computador-Lock-in
        self.arduino.conectar()

    def desconectar(self):
            """Desconecta o computador do Lock-in"""

            self.sr510.fechar()
            self.arduino.desconectar()


    # ========== Responsividade ==========
    def fechamento(self, evento):
        """Função executada caso a janela de plotagem seja fechada. Encerra o programa."""

        # Não uso o "evnto", mas preciso desse argumeto para o Matplot não reclamar
        if self.experimento_concluido:
            return
        
        print('\n[AVISO] Janela fechada. Abortando experimento com segurança...')
        self.abortar_experimento = True

    def tecla_pressionada(self, evento):
        """
        Função chamada quando o programa detecta a pressão em alguma tecla NA JANELA DE PLOTAGEM.

        Args:
            evento (_type_): O sinal do Matplotlib para a ativação da função. Carrega informações sobre o evento (qual a tecla...)
        """

        if evento.key == 'escape' or evento.key == 'q':
            print('\n[AVISO] Tecla de parada pressionada. Encerrando...')
            self.abortar_experimento = True

    # ========== Gráfico ==========
    def inicializar_grafico(self):
        """Prepara a janela do gráfico antes de começar o loop, além de ativar a interatividade"""

        plt.ion() # Ativa o modo interativo
        self.fig, self.ax = plt.subplots(figsize=(8, 5))

        # ========== Conectar eventos a funções via Matplotlib ==========
        self.fig.canvas.mpl_connect('close_event', self.fechamento) # Detecta se a janela foi fechada
        self.fig.canvas.mpl_connect('key_press_event', self.tecla_pressionada) # Detecta teclas pressionada

        self.ln, = self.ax.plot([], [], 'ro-', ms=2.5, animated=False, label='Sinal') # 'ro-' --> bola vermelha com linha
        
        self.ax.set_title(f'Espectro em Tempo Real')
        self.ax.set_xlabel('Comprimento de Onda (Å)')
        escala = self.sr510.ler_sensitividade()
        print(f'Gráfico: Sensibilidade [{escala}]')
        self.ax.set_ylabel(f'Sinal ({escala})')
        self.ax.grid(True)
        self.ax.legend(loc='upper left')

        # Ajusta os limites do eixo X baseado no definido pelo usuário
        self.ax.set_xlim(min(self.comp_i, self.comp_f), max(self.comp_i, self.comp_f))
        plt.tight_layout()
        plt.show()

    def atualizar_grafico(self):
        if self.ln:
            # O set_data aceita o deque diretamente
            self.ln.set_data(self.buffer_x, self.buffer_y)
            
            # Ajuste de margem no eixo Y para o sinal não bater no teto
            margem = (max(self.buffer_y) - min(self.buffer_y)) * 0.1
            self.ax.set_ylim(min(self.buffer_y) - margem, max(self.buffer_y) + margem)
            
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()


    def calcula_passo(self):
        """
        Calcula o total de pontos de medida e o passo step (unidade de passo de motor) que o motor deverá dar a cada loop

        Returns:
            tuple: (O número de pontos de medida, 
            O passo do motor "step", O passo em Angstron)
        """

        from math import modf, ceil
        def conversor_angstron_step_step_angstron(valor, ang_step: str):
            """
            Uma função que realiza a conversão bidirecional entre passos em Å e passos step

            Args:
                valor (Any): O valor a ser convertido
                ang_step (str): A unidade em que se está

            Returns:
                float: O valor convertido
            """

            fator_calibracao = 10.6170 # Passos por Å
            if ang_step == 'ang':
                # ===== Å --para-> step
                return fator_calibracao * valor
            else:
                # ===== Step --para-> Å
                return (1/fator_calibracao) * valor

        def acerta_passo(total_pontos_original: int, passo_a: float):
            """
            Garante que o step não é um número fracionário e que todo o range de medida escolhido será contemplado com resolução melhor ou igual à original

            Args:
                total_pontos_original (int): O número de pntos de medida
                passo_a (float): O passo em Å que seria dado

            Returns:
                tuple: Uma tupla --> (total de pontos de medida, passo do motor "step" emunidades de passo de motor)
            """

            
            step_basico = conversor_angstron_step_step_angstron(passo_a, 'ang')
            fracionaria, step = modf(step_basico) # Tupla --> (parte fracionária, parte inteira(float))
            falta = fracionaria * total_pontos_original # Em unidades de passo de motor
            ciclos_extras = ceil(falta / step) # Número de ciclos extras que serão necessários para varrer o espectro
            total_pontos = total_pontos_original + ciclos_extras

            return total_pontos, step
        
        diferenca = abs(self.comp_f - self.comp_i)
        resolucao = self.tamanho_fenda * Experimento.grade
        total_pontos = self.ppr * diferenca / resolucao # Total de ciclos
        passo_a = diferenca / total_pontos # Unidades de comprimento Å
        novo_total_pontos, step = acerta_passo(total_pontos, passo_a)
        novo_passo_a = conversor_angstron_step_step_angstron(step, 'step')

        return int(novo_total_pontos), int(step), novo_passo_a

    def coletar_dados(self):
        """Coleta os dados do experimento e armazena na forma de listas do próprio objeto"""
        
        # Podemos adicionar um "tratamento" de dados ou uma coleta com média e desvio padrão
        tensao = self.sr510.ler_valor_saida()
        # self.lista_tensao.append(tensao) --> _antiga_criar_arquivo_csv()
        comprimento_onda = self.comp_atual # Como vamos conseguir esse valor?????

        
        # self.lista_comprimento_onda.append(comprimento_onda) --> _antiga_criar_arquivo_csv()
        self.salvar_linha((comprimento_onda, tensao)) # Novo método de anotar no .csv. Anota durande o experimento, não só ao final

        # ========== Alimenta o buffer para o gráfico ==========
        self.buffer_x.append(comprimento_onda)
        self.buffer_y.append(tensao)
        
    def move_motor(self, step, passo_a):
        """Movimenta o motor do monocromador com base no passo em unidades de comprimento"""

        print(f'Movendo o motor... {step} passos de motor; {passo_a}Angstron')
        self.comp_atual += passo_a # Atualiza onde o programa está no espectro
        self.arduino.mover_motor(step)

    def cria_arquivo_csv(self):
        """Cria o arquivo .csv com os dados coletados no exeperiemento"""

        def nome_excludente(nome_base: str, pasta='.'):
            """
            Cria o nome do arquivo .csv em que serão armazenados os dados do experiemnto

            Args:
                nome_base (str): O nome original (escolhido pelo usuário) do arquivo
                pasta (str, optional): O caminho em que o arquivo será salvo. Defaults to '.'

            Returns:
                str: Um nome de arquivo que não está no caminho expecificado
            """
            from pathlib import Path

            pasta = Path(pasta)
            nome_base = Path(nome_base).stem
            arquivo = pasta / f'{nome_base}.csv'

            contador = 1
            while arquivo.exists():
                arquivo = pasta / f"{nome_base}_{contador}.csv"
                contador += 1

            return arquivo

        self.nome_exclusivo = nome_excludente(self.nome_arquivo)
        with open(self.nome_exclusivo, 'a', newline='', encoding='utf-8') as log:

            for linha in self.metadados: # Escreve os metadados
                log.write(linha + '\n')
            
            log.write('#' + '-'*25 + '\n') # Uma linha divisória para ficar bonito

    def salvar_linha(self, dados):
        from csv import writer
        with open(self.nome_exclusivo, 'a', newline='', encoding='utf-8') as log:
            writer = writer(log)
            writer.writerow(dados)


    def run(self, conexao_lock_in: dict, conexao_arduino: dict):
        """
        Uma função para rodar um experimento inteiro, i.e., coletar dados, mover motores e salvar o arquivo .csv

        Args:
            conexao (dict): Um dicionário com as chaves porta (porta) e o bound rate (boundrate) da comunicação Serial
        """

        total_pontos, step, passo_a = self.calcula_passo()
        self.conectar(conexao_lock_in=conexao_lock_in, conexao_arduino=conexao_arduino)
        print('Criando o arquivo .csv...')
        self.cria_arquivo_csv()
        self.inicializar_grafico()

        print('Iniciando o experimento...\n')
        sleep(2.5)
        for i in range(total_pontos):
            tempo_i = perf_counter()

            # Verifica se ocorreu o pedido de parada
            if self.abortar_experimento:
                break

            # Medir --> mover --> Medir...
            self.coletar_dados()
            self.atualizar_grafico()
            plt.pause(0.01) # Permitir a interatividade durante a execução

            self.move_motor(step, passo_a)
            tempo_f = perf_counter()

            # ===== Calcula o tempo que será gasto
            delta_t = tempo_f - tempo_i
            tempo_total = delta_t * (total_pontos - 1) # Já foi uma iteração
            minutos, segundos = tempo_total // 60, tempo_total % 60
            print(f'Frequência de medida 1 medida por {delta_t}')
            print(f"Tempo restante: {minutos}' {segundos}' --- {i+1}/{total_pontos}\n", '-'*25)
        

        print('Finalizando conexões...')
        self.desconectar()

        if self.abortar_experimento:
            print("Experimento interrompido pelo usuário.")
        else:
            print("Experimento concluído.")
            self.experimento_concluido = True
            # Deixa o gráfico na tela ao final do experimento
            plt.ioff()
            plt.tight_layout()
            plt.show()
#endregion


if __name__ == "__main__":

    texto = """Conjunto de testes para ferificar o correto funcionamento do programa de leitura e automação do monocromador com Python 3"""
    experimento = Experimento('Teste_do_programa', 'João Roberto B. K. Cruz', 100, 105, 0.1, 1, texto)
    experimento.run({'porta': 'COM10', 'boundrate': 9600}, {'porta': 'COM13', 'boundrate': 9600})
