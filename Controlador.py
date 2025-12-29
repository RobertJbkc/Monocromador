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


# ========== Imports ==========\
# Deveria estar dentro da classe?
import serial
import matplotlib.pyplot as plt
from time import sleep
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

    
    def conectar(self):
        """Cria e abre a conexão entre o Arduino e o computador (Python)"""
        self.conexao = serial.Serial(
            port=self.porta,
            baudrate=self.boundrate,
            timeout=self.timeout
         )
        sleep(2.5) # Tempo para garanti que a conxão foi aberta
        
        
    def ler_Serial(self):
        """
        Faz a leitura da saída Serial do Arduino. Lê uma linha e decodifica em "utf-8"

        Returns:
            str: A linha que foi lida, sem espaços e novas linhas
        """

        # "readline()" lê até um "\n"
        saida = self.conexao.readline().decode("utf-8").rstrip()

        return saida
    
    def escrever(self, mensagem):
        """
        Encia uma mensagem via comunicação Serial para o Arduino. Escreve na porta Serial

        Args:
            mensagem (None): A mensagem que será enviada para o Arduino
        """

        mensagem = str(mensagem)
        mensagem_b = mensagem.encode('ascii')
        self.conexao.write(mensagem_b)

    def desconectar(self):
        """
        Fecha a comunicação entre o Arduino e o computador (Python)
        """
        self.conexao.close()
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
        print('Recebido: ', raw)
        try:
            sensitividade_c = int(raw) # Transforma o texto em número
        except ValueError as e:
            print(f'Erro ao converter a resposta "raw" --> float: {e}')
            sensitividade_c = None

        print('##########=========', sensitividade_c, type(sensitividade_c))
        print(dicionario_traducao[sensitividade_c])

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

        # Para o gráfico
        self.tamanho_buffer = 100
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


    def inicializar_grafico(self):
        """Prepara a janela do gráfico antes de começar o loop"""

        plt.ion() # Ativa o modo interativo
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.ln, = self.ax.plot([], [], 'ro-', animated=False) # 'ro-' --> bola vermelha com linha
        
        self.ax.set_title(f'Espectro em Tempo Real')
        self.ax.set_xlabel('Comprimento de Onda (Å)')
        escala = self.sr510.ler_sensitividade()
        print('########## Escala:', escala)
        self.ax.set_ylabel(f'Sinal ({escala})')
        self.ax.grid(True)
        self.ax.legend(loc='upper right')

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

    def conectar(self, conexao: dict):
        """Cria a conexao (abre o canal), por meio de "SR510", com o Lock-in"""

        self.sr510 = SR510(**conexao) # Cria o objeto da classe "SR510"
        self.sr510.conectar() # Usa o método "conectar()" da classe "SR510" para criar a conexão computador-Lock-in

    def calcula_passo(self):
        """Calcula o total de pontos de medida e o passo em angstrons que deverá ser dado pelo motor"""

        diferenca = abs(self.comp_f - self.comp_i)
        resolucao = self.tamanho_fenda * Experimento.grade
        total_pontos = self.ppr * diferenca / resolucao
        passo_a = diferenca / total_pontos # Unidades de comprimento

        return int(total_pontos), passo_a

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
        
    def move_motor(self, passo_a):
        """Movimenta o motor do monocromador com base no passo em unidades de comprimento"""

        self.comp_atual += passo_a
        print(f'Passo_a: {passo_a}')

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

    def desconectar(self):
        """Desconecta o computador do Lock-in"""

        self.sr510.fechar()

    def run(self, conexao: dict):
        """
        Uma função para rodar um experimento inteiro, i.e., coletar dados, mover motores e salvar o arquivo .csv

        Args:
            conexao (dict): Um dicionário com as chaves porta (porta) e o bound rate (boundrate) da comunicação Serial
        """

        total_pontos, passo_a = self.calcula_passo()
        self.conectar(conexao)
        print('Criando o arquivo .csv')
        self.cria_arquivo_csv()
        self.inicializar_grafico()

        for i in range(total_pontos):
            # Medir --> mover --> Medir...
            self.coletar_dados()
            self.atualizar_grafico()
            self.move_motor(passo_a)
            print(f'{i+1}/{total_pontos}')

        self.desconectar()
#endregion

if __name__ == "__main__":

    texto = """Conjunto de testes para ferificar o correto funcionamento do programa de leitura e automação do monocromador com Python 3"""
    experimento = Experimento('Teste_do_programa', 'João Roberto B. K. Cruz', 100, 110, 0.1, 5, texto)
    experimento.run({'porta': 'COM7', 'boundrate': 9600})