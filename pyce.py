#region Observações
# - A função de coleta de dados tem que ser chamda junto com a de criar um .csv.
# - É necessário dar um nome ao arquivo. Caso contrário a função de nomes diferentes não funcionará corretamente.
#endregion


# ========== Imports ==========
import serial
import matplotlib.pyplot as plt
from time import sleep, perf_counter
from datetime import date, datetime
# Alt + 0197 --> Å


#region Monocromador
class Monocromador:
    """
    Classe destinada a ser o intercâmbio entre o hardware do monocromador (Arduino) e o programa em python. Funciona como uma biblioteca.

    São métodos de leitura e escrita, além de conexão e desconexão da comunicação Serial focados nas funcionalidades do monocromador (Arduino).
    """

    def __init__(self, porta: str, baudrate: int, timeout: None=None):
        """
        Função constutora para a classe de comunicação Python-Arduino

        Args:
            porta (str): A porta 'COM' em que a placa Arduino está conectada
            baudrate (int): A taxa de comunicação Serial
            timeout (None): O tempo máximo que o python espera por uma resposta. None --> Infinito. Defaults to None.
        """
        self.porta = porta
        self.baudrate = baudrate
        self.timeout = timeout

    # ========== Conexão ==========
    def conectar(self):
        """Cria e abre a conexão entre o Arduino e o computador (Python)."""

        self.conexao = serial.Serial(
            port=self.porta,
            baudrate=self.baudrate,
            timeout=self.timeout
         )
        sleep(0.5)
        print(f'Arduino: Conectando na porta {self.porta}...')
        sleep(2.5) # Tempo para garanti que a conxão foi aberta
        print(f'-- Arduino conectado na porta {self.porta}. Canal Serial aberto --')

    def desconectar(self):
        """Fecha a comunicação entre o Arduino e o computador (Python)."""
        
        if self.conexao:
            self.conexao.close()  
    

    # ========== Leitura ==========
    def ler_Serial(self):
        """
        Faz a leitura da saída Serial do Arduino. Lê uma linha e decodifica em "utf-8".

        Returns:
            str: A linha que foi lida, sem espaços e novas linhas (caracteres de terminação)
        """

        # "readline()" lê até um "\n"
        saida = self.conexao.readline().decode("utf-8").rstrip()

        return saida
    

    # ========== Escrita ==========
    def escrever(self, mensagem):
        """
        Envia uma mensagem via comunicação Serial para o Arduino. Escreve na porta Serial

        Args:
            mensagem (None): A mensagem que será enviada para o Arduino
        """

        print(f'PC: Enviando [{mensagem}]...')
        mensagem = str(mensagem)
        mensagem_b = mensagem.encode('ascii')
        self.conexao.write(mensagem_b)


    # ========== Métodos (explícitos) ==========
    def mover_motor(self, steps: int):
        """
        Escreve na porta Serial do Arduino o número de steps que será dado pelo motor. Após isso, aguarda o retorno do arduino para confirmar o final da movimentação. Impime esse retorno no terminal.

        Args:
            passos (int): O número de steps que o motor vai andar.
        """

        self.escrever(steps)
        saida = self.ler_Serial()
        print(f'Arduino: Resposta [{saida}];')



#region SR510
class SR510:
    """
    Classe para traduzir o idioma Serial falado pelo Lock-in SR510 em um idioma de funções Python.
    
    Os métodos são leituras ou escritas de comandos do Lock-in obtidos a partir do manual do equipamento.

    A base de funcionamento é o módulo pySerial.
    """

    def __init__(self, porta: str, baudrate: int):
        """
        Função construtora da classe SR510.

        Args:
            porta (str): A porta Serial em que o Lock-in está conectado.
            baudrate (int): A taxa de comunicação Serial entre o computador e o Lock-in.
        """

        self.porta = porta
        self.baudrate = baudrate
        self.conexao = None


    # ========== Conexão ==========
    def conectar(self):
        """Cria (e abre) a conexão Serial entre computador e Lock-in"""
         
        self.conexao = serial.Serial(
            port=self.porta,
            baudrate=self.baudrate, # Configurado nas chaves 1, 2 e 3
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE, # Configurado nas chaves 4 e 5
            stopbits=serial.STOPBITS_TWO, # O SR510 exige 2 em 9600 baud
            timeout=0.05
         )
        sleep(0.5)
        print(f'Lock-in: Conectando na porta {self.porta}...')
        sleep(2.5) # Tempo para garanti que a conxão foi aberta
        print(f'-- SR510 conectado na porta {self.porta}. Canal Serial aberto --')

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
    
    def ler_sensibilidade(self):
        """
        Lê o valor de sensibilidade escolhido no Lock-in e traduz em várias forma diferenrtes de interpretar/usar o valor.

        Returns:
            tuple: Uma tupla (Sensibilidade str, O código enviado pelo Lock-in, O valor float, A ordem de grandeza).
        """

        dicionario_traducao = {
            1: ('10 nV', 1, 10e-9, pow(10, -9)),
            2: ('20 nV', 2, 20e-9, pow(10, -9)),
            3: ('50 nV', 3, 50e-9, pow(10, -9)),
            4: ('100 nV', 4, 100e-9, pow(10, -9)),
            5: ('200 nV', 5, 200e-9, pow(10, -9)),
            6: ('500 nV', 6, 500e-9, pow(10, -9)),
            7: ('1 µV', 7, 1e-6, pow(10, -6)),
            8: ('2 µV', 8, 2e-6, pow(10, -6)),
            9: ('5 µV', 9, 5e-6, pow(10, -6)),
            10: ('10 µV', 10, 10e-6, pow(10, -6)),
            11: ('20 µV', 11, 20e-6, pow(10, -6)),
            12: ('50 µV', 12, 50e-6, pow(10, -6)),
            13: ('100 µV', 13, 100e-6, pow(10, -6)),
            14: ('200 µV', 14, 200e-6, pow(10, -6)),
            15: ('500 µV', 15, 500e-6, pow(10, -6)),
            16: ('1 mV', 16, 1e-3, pow(10, -3)),
            17: ('2 mV', 17, 2e-3, pow(10, -3)),
            18: ('5 mV', 18, 5e-3, pow(10, -3)),
            19: ('10 mV', 19, 10e-3, pow(10, -3)),
            20: ('20 mV', 20, 20e-3, pow(10, -3)),
            21: ('50 mV', 21, 50e-3, pow(10, -3)),
            22: ('100 mV', 22, 100e-3, pow(10, -3)),
            23: ('200 mV', 23, 200e-3, pow(10, -3)),
            24: ('500 mV', 24, 500e-3, pow(10, -3)),
        }
        self.conexao.write(b'G\r')
        raw = self.conexao.readline().decode('utf-8').strip()
        try:
            sensibilidade_c = int(raw) # Transforma o texto em número
        except ValueError as e:
            print(f'Erro ao converter a resposta "raw" --> float: {e}')
            sensibilidade_c = None

        return dicionario_traducao[sensibilidade_c]

    
    # ========== Escrita ==========
    def set_tempo_espera(self, t):
        """
        Define no Lock-in o tempo de leitura entre cada caracter. O Lock-in sempre liga em 6.

        Args:
            t (int): Um inteiro de 1 a 6 em que 1 é o menor tempo.
        """

        comando = f'W{t}\r'
        self.conexao.write(comando.encode('ascii')) # Envia o comando

    def set_sensibilidade(self, valor: int):
        """
        Define um valor de sensibilidade no Lock-in. O "valor" é um número inteiro de 1 a 24

        Args:
            valor (int): Número inteiro de 1 a 24 onde o maior número é uma sensibilidade menor.
        """

        comando = f'G{valor}\r'
        self.conexao.write(comando.encode('ascii')) # Envia o comando
#endregion



#region Experimento
class Experimento:
    """
    A classe armazena todos os métodos necessários para realizar um experimento com o monocromador conectado ao Lock-in amplifier SR510.
    
    Ela conta com os métodos intermediários e com um método final "run()" para rodar um experimento inteiro.

    A nova definição parte do presuposto que o experimento sópode ser rodado se a conexão entre os equipamentos já existir, assim é necessário conectar antes de rodar. O método "run()" não realiza a conexão.

    A base de funcionamento é o módulo pySerial.
    """

    # Todo experimento tem isso igual. Verifiar se esse é o estilo correto
    grade = 16 # parametro_de_grade Å / mm
    fator_calibracao = 10.6170 # Steps por Å

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

        # ========== Atributos iniciais do objeto ==========
        self.nome_arquivo = nome_arquivo
        self.operador = operador
        self.comp_i = comp_i
        self.comp_f = comp_f
        self.tamanho_fenda = tamanho_fenda / 1000 # --> Micro metro para mm
        self.ppr = ppr
        self.descricao = descricao

        # ===== Novas características que não são definidas pelo usuário
        self.comp_atual = self.comp_i
        self.tempo_atual = datetime.now().time() # Obtem a hora atual
        self.hoje = date.today() # Obtém a data atual (YYYY-MM-DD)

        # ===== Eventos
        self.eventos = []
        self.evento_abortar_experimento = False

        # ===== Para o gráfico
        self.buffer_x = []
        self.buffer_y = []

    
    # ========== Conexão ==========
    def conectar(self, conexao_lock_in: dict, conexao_arduino: dict):
        """
        Cria a conexao (abre o canal), por meio de "SR510", com o Lock-in e por meio de "Monocromador" com o Arduino.

        Args:
            conexao_lock_in (dict): O dicionário a porta (porta) o baudrate (baudrate) e o timeout (timeot) para a conexão.
            conexao_arduino (dict): O dicionário a porta (porta) o baudrate (baudrate) e o timeout (timeot) para a conexão.
        """

        self.sr510 = SR510(**conexao_lock_in) # Cria o objeto da classe "SR510"
        self.arduino = Monocromador(**conexao_arduino)
        self.sr510.conectar() # Usa o método "conectar()" de "SR510" para criar a conexão computador-Lock-in
        self.arduino.conectar()

        # ===== Coletar dados iniciais dos equipamentos
        raw_sensibilidade = self.sr510.ler_sensibilidade()
        self.sensibilidade_str = raw_sensibilidade[0] # A string de sensibilidade
        self.sensibilidade_ordem = raw_sensibilidade[3] # A ordem de grandeza da sensibilidade

    def desconectar(self):
        """Desconecta o computador do Lock-in"""

        self.sr510.fechar()
        self.arduino.desconectar()


    # ========== Responsividade ==========
    def fechamento(self, evento):
        """Função executada caso a janela de plotagem seja fechada. Encerra o programa."""

        # Não uso o "evnto", mas preciso desse argumeto para o Matplot não reclamar
        if self.evento_experimento_concluido:
            return
        
        print('\nAVISO: Janela fechada. Abortando experimento...')
        self.evento_abortar_experimento = True

    def tecla_pressionada(self, evento):
        """
        Função chamada quando o programa detecta a pressão em alguma tecla NA JANELA DE PLOTAGEM.

        Args:
            evento (_type_): O sinal do Matplotlib para a ativação da função. Carrega informações sobre o evento (qual a tecla...)
        """

        if evento.key == 'escape' or evento.key == 'q':
            print('\nAVISO: Tecla de parada pressionada. Encerrando...')
            self.evento_abortar_experimento = True

    # ========== Gráfico ==========
    def inicializar_grafico(self):
        """Prepara a janela do gráfico antes de começar o loop, além de ativar a interatividade"""

        # ========== Cria a janela e a linha ==========
        plt.ion() # Ativa o modo interativo
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.linha_grafico, = self.ax.plot([], [], 'ro-', ms=2.5, animated=False, label='Sinal') # 'ro-' --> bola vermelha com linha

        # ========== Conectar eventos a funções via Matplotlib ==========
        self.fig.canvas.mpl_connect('close_event', self.fechamento) # Detecta se a janela foi fechada
        self.fig.canvas.mpl_connect('key_press_event', self.tecla_pressionada) # Detecta teclas pressionada
        
        # ========== Legendas e estilo ==========
        self.ax.set_title(f'Espectro em Tempo Real')
        self.ax.set_xlabel('Comprimento de Onda (Å)')
        self.ax.set_ylabel(f'Sinal ({self.sensibilidade_str})')
        self.ax.grid(True)
        self.ax.legend(loc='upper left')
        self.ax.set_xlim(min(self.comp_i, self.comp_f), max(self.comp_i, self.comp_f)) # Limites em x
        plt.tight_layout()
        plt.show()

    def atualizar_grafico(self):
        """Atualiza constantemente o gráfico, corrigindo os limites do eixo y para que o gráfico sempre seja visível."""

        if self.linha_grafico:
            self.linha_grafico.set_data(self.buffer_x, self.buffer_y) # Atualiza o gráfico
            margem = (max(self.buffer_y) - min(self.buffer_y)) * 0.1 # Margem do gráfico
            self.ax.set_ylim(min(self.buffer_y) - margem, max(self.buffer_y) + margem) # Limites em y (escala)
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()


    # ========== Funcionalidades ==========
    def calcula_passo(self):
        """
        Calcula o total de pontos de medida e o passo step (unidade de passo de motor) que o motor deverá dar a cada loop. CErtifica que esse número seja inteiro aplicando um procedimento de correção.

        Returns:
            tuple: Uma tupla com o total de pontos (int), o total de steps (int) e o passo em Å que será dado (float) arredondado para a terceira casa decimal.
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

            Experimento.fator_calibracao = 10.6170 # Steps por Å
            if ang_step == 'ang': # ===== Å --para-> step
                return Experimento.fator_calibracao * valor
            else: # ===== Step --para-> Å
                return (1/Experimento.fator_calibracao) * valor

        def acerta_passo(total_pontos_original: int, passo_a: float):
            """
            Garante que o step não é um número fracionário e que todo o range de medida escolhido será contemplado com resolução melhor ou igual à original

            Args:
                total_pontos_original (int): O número de pntos de medida
                passo_a (float): O passo em Å que seria dado

            Returns:
                tuple: Uma tupla --> (total de pontos de medida, passo do motor "step" emunidades de passo de motor)
            """

            total_pontos_original = ceil(total_pontos_original) # Gaante que é inteiro
            step_basico = conversor_angstron_step_step_angstron(passo_a, 'ang')
            fracionaria, step = modf(step_basico) # Tupla --> (parte fracionária, parte inteira(float))
            falta = fracionaria * total_pontos_original # Em unidades de passo de motor
            ciclos_extras = ceil(falta / step) # Número de ciclos extras que serão necessários para varrer o espectro
            total_pontos = total_pontos_original + ciclos_extras

            return total_pontos, step
        
        diferenca = abs(self.comp_f - self.comp_i)
        resolucao = self.tamanho_fenda * Experimento.grade
        total_pontos = self.ppr * (diferenca / resolucao) # Total de ciclos
        passo_a = diferenca / total_pontos # Unidades de comprimento Å
        novo_total_pontos, step = acerta_passo(total_pontos, passo_a)
        novo_passo_a = conversor_angstron_step_step_angstron(step, 'step')

        return int(novo_total_pontos), int(step), round(novo_passo_a, 3)
    
    def cria_arquivo_csv(self):
        """Cria o arquivo .csv para receber os dados coletados no exeperiemento"""

        def nome_excludente(nome_base: str, pasta='Gráficos'):
            """
            Cria o nome do arquivo .csv em que serão armazenados os dados do experiemnto. Garante que o nome é único.

            Args:
                nome_base (str): O nome original (escolhido pelo usuário) do arquivo
                pasta (str, optional): O caminho em que o arquivo será salvo. Defaults to '.'

            Returns:
                str: Um nome de arquivo que não está no caminho expecificado
            """

            from pathlib import Path

            pasta = Path(pasta)
            pasta.mkdir(exist_ok=True)
            nome_base = Path(nome_base).stem
            arquivo = pasta / f'{nome_base}.csv'

            contador = 1
            while arquivo.exists():
                arquivo = pasta / f'{nome_base}_{contador}.csv'
                contador += 1

            return pasta / arquivo.stem
        
        #region Metadados
        self.metadados = [
            f'# Experimento: {self.descricao}',
            f'# Data: [{self.hoje}] [{self.tempo_atual}]',
            f'# Operador: {self.operador}',
            f'# Comprimento de onda inicial: {self.comp_i}',
            f'# Comprimento de onda final: {self.comp_f}',
            f'# Tamanho da fenda {self.tamanho_fenda}',
            f'# Ponto Por Resolução (PPR): {self.ppr}',
            f'# Sensibilidade: {self.sensibilidade_str}'
        ]
        #endregion
        self.nome_exclusivo = nome_excludente(self.nome_arquivo)
        self.nome_arquivo_csv = f'{self.nome_exclusivo}.csv'
        with open(self.nome_arquivo_csv, 'a', newline='', encoding='utf-8') as log:

            for linha in self.metadados: # Escreve os metadados
                log.write(linha + '\n')
            
            log.write('#' + '-'*25 + '\n') # Uma linha divisória para ficar bonito e legível

    def escreve_eventos(self):
        """Escreve, ao final, os eventos que ocorreram durande a execução"""
        with open(self.nome_arquivo_csv, 'a', newline='', encoding='utf-8') as log:

            log.write('#' + '-'*25 + '\n') # Uma linha divisória para ficar bonito
            for linha in self.eventos: # Escreve os eventos
                log.write(linha + '\n')

    # ========== Operação ==========
    def coletar_dados(self):
        """Coleta os dados do experimento e os salva no arquivo .csv e na forma de listas (buffer) do próprio objeto"""

        def salvar_linha(dados):
            """
            Salva os dados que foram fornecidos no arquivo .csv do experimento no formato csv

            Args:
                dados (Any): O  que será escrito no arquivo.
            """

            # Implementar a lógica de verifica se o arquivo foi criado
            from csv import writer
            with open(self.nome_arquivo_csv, 'a', newline='', encoding='utf-8') as log:
                writer = writer(log)
                writer.writerow(dados)
        
        raw_tensao = self.sr510.ler_valor_saida() # Saída do Lock-in
        tensao = round((raw_tensao / self.sensibilidade_ordem), 3)
        comprimento_onda = round(self.comp_atual, 3) # Vem da movimentação do motor
        salvar_linha((comprimento_onda, tensao)) # Salva os dados

        # ===== Alimenta o buffer para o gráfico
        self.buffer_x.append(comprimento_onda)
        self.buffer_y.append(tensao)

    def move_motor(self, step, passo_a):
        """Movimenta o motor do monocromador com base em passos de motor (steps)"""

        print(f'Motor: {step} steps -- {passo_a}Å...')
        print(f'Posição atual: {round(self.comp_atual, 3)}Å')
        self.comp_atual += passo_a # Atualiza onde o programa está no espectro
        self.arduino.mover_motor(step)

    def run(self):
        """
        Uma função para rodar um experimento inteiro, i.e., coletar dados, mover motores e salvar o arquivo .csv

        Args:
            conexao (dict): Um dicionário com as chaves porta (porta) e o bound rate (baudrate) da comunicação Serial
        """

        total_pontos, step, passo_a = self.calcula_passo()
        print('PC: Criando o arquivo .csv...')
        self.inicializar_grafico()
        self.cria_arquivo_csv()
        sleep(1.5)
        print('PC: Iniciando o experimento...\n', '#'*25)
        sleep(2.5)

        for i in range(total_pontos):
            tempo_i = perf_counter()

            # Verifica se ocorreu o pedido de parada
            if self.evento_abortar_experimento:
                print('Experimento interrompido pelo usuário.')
                self.eventos.append(f'# [{self.tempo_atual}]: O experimento foi interrompido pelo usuário')
                break

            # Medir --> mover --> Medir...
            self.coletar_dados()
            self.atualizar_grafico()
            plt.pause(0.01) # Permitir a interatividade durante a execução. É uma pausa
            self.move_motor(step, passo_a)

            tempo_f = perf_counter()

            # ===== Calcula o tempo que será gasto
            delta_t = tempo_f - tempo_i
            tempo_total = round(delta_t * (total_pontos - i + 1), 1) # i: 0 --> total_pontos - 1
            minutos, segundos = tempo_total // 60, tempo_total % 60
            print(f"Tempo restante: {minutos}' {segundos}''")
            print(f'Ciclo {i+1}/{total_pontos}\n', '-'*25, '\n')
        

        print('PC: Finalizando conexões...')
        self.desconectar()

        if self.evento_abortar_experimento:
            self.escreve_eventos()
            

        else:
            print('PC: Experimento concluído.')
            self.eventos.append(f'Conclusão: [{self.tempo_atual}]')
            self.escreve_eventos()

            # Deixa o gráfico na tela ao final do experimento
            plt.ioff()
            plt.tight_layout()
            plt.savefig(f'{self.nome_exclusivo}.jpg')
            plt.show()
#endregion



if __name__ == "__main__":

    # ========== Sessão destinada à alteração ==========
    NOME = 'NOME'
    OPERADOR = ''
    COPRIMENTO_DE_ONDA_INICIAL = 1000 # Å
    COMPRIMENTO_DE_ONDA_FINAL = 1100 # Å
    ABERTURA_DA_FENDA = 100 # micro metro
    PONTOS_POR_RESOLUCAO = 3
    TEXTO = """Conjunto de testes para verificar o correto funcionamento do programa de leitura e automação do monocromador com Python 3"""

    PORTA_LOCK_IN = 'COM10'
    PORTA_ARDUINO = 'COM13'

    # ==============================
    # ========== Programa ==========
    experimento = Experimento(
        NOME,
        OPERADOR,
        COPRIMENTO_DE_ONDA_INICIAL,
        COMPRIMENTO_DE_ONDA_FINAL,
        ABERTURA_DA_FENDA,
        PONTOS_POR_RESOLUCAO,
        TEXTO
    )

    experimento.conectar(
        conexao_lock_in={
            'porta': PORTA_LOCK_IN,
            'baudrate': 9600
        },
        conexao_arduino={
            'porta': PORTA_ARDUINO,
            'baudrate': 9600,
            'timeout': None
        }
    )
    experimento.run()