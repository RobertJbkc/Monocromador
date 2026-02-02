import matplotlib
matplotlib.use('Agg')
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox # ttk traz os widgets com visual mais "moderno" (Windows 7 style)
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # --> Tela de Figura para Tkinter
import threading # Multitarefa
import time
import random
try:
    import pyce # Minha biblioteca
except ImportError:
    print('AVISO: Arquivo "pyce.py" não encontrado na mesma pasta!')

import queue
import sys



# ========== Classes falsas para teste (Mocks) ==========
class MockSR510:
    def conectar(self): print('[SIMULAÇÃO] Lock-in conectado.')
    def ler_sensibilidade(self): return ['500 mV', 0, 0, 1] # Retorna lista fictícia
    def ler_valor_saida(self): return random.uniform(0, 10) # Retorna voltagem aleatória
    def fechar(self): print('[SIMULAÇÃO] Lock-in desconectado.')

class MockMonocromador:
    def conectar(self): print('[SIMULAÇÃO] Arduino conectado.')
    def mover_motor(self, step): pass # Finge que move
    def desconectar(self): print('[SIMULAÇÃO] Arduino desconectado.')



# ========== Herança de classe ==========
class ExperimentoGUI(pyce.Experimento):
    """Classe filha da classe original (Experimento). Herda tudo (métodos e aracterísticas) para permitir alteração não destrutiva."""

    def __init__(self, fig, ax, canvas, modo_simulacao, *args, **kwargs):
        super().__init__(*args, **kwargs) # Garante a "__init___" da original
        
        # Referências da GUI (Onde desenhar)
        self.fig_gui = fig
        self.ax_gui = ax
        self.canvas_gui = canvas
        
        # self.linha_grafico, = self.ax_gui.plot([], [], 'b.-', ms=3, label='Sinal (V)')
        self.linha_grafico, = self.ax_gui.plot([], [], 'ro-', ms=2.5, label='Sinal (V)')
        self.ax_gui.legend(loc='upper right')

        self.modo_simulacao = modo_simulacao

    # ========== SOBRESCREVENDO MÉTODOS ORIGINAIS ==========
    def conectar(self, conexao_lock_in: dict, conexao_arduino: dict):
        # ===== Configura o uso das classes mocks
        if self.modo_simulacao:
            print('MODO SIMULAÇÃO ATIVADO')
            self.sr510 = MockSR510()
            self.arduino = MockMonocromador()
            # Simulando a lógica de ler sensibilidade que existe no original
            raw_sensibilidade = self.sr510.ler_sensibilidade()
            self.sensibilidade_str = raw_sensibilidade[0]
            self.sensibilidade_ordem = raw_sensibilidade[3]
        else:
            # Chama o método original do pyce.py
            super().conectar(conexao_lock_in, conexao_arduino)

    def inicializar_grafico(self):
        # A janela já existe na GUI. Foi criada na "completa_janela()"
        pass

    def atualizar_grafico(self):
        if self.linha_grafico:
            # Atualiza os dados da linha com o buffer da classe mãe
            self.linha_grafico.set_data(self.buffer_x, self.buffer_y)
            
            # Recalcula a escala (Zoom automático)
            if len(self.buffer_y) > 1:
                # Usamos sua lógica original aqui!
                y_min, y_max = min(self.buffer_y), max(self.buffer_y)
                margem = (y_max - y_min) * 0.1 if y_max != y_min else 1.0
                
                self.ax_gui.set_ylim(y_min - margem, y_max + margem)
                self.ax_gui.set_xlim(min(self.comp_i, self.comp_f), max(self.comp_i, self.comp_f))
            # if len(self.buffer_y) > 0:
            #     self.ax_gui.relim()
            #     self.ax_gui.autoscale_view()
            
            self.canvas_gui.draw_idle()
            # self.canvas_gui.draw() --> Vai que...
            # .draw_idle() é melhor que .draw() pois espera o processador "respirar". Desenhe quiando der. Kkkkkk

class TextRedirector:
    def __init__(self, widget, tag='stdout'):
        self.widget = widget
        self.tag = tag
        self.queue = queue.Queue()

    def write(self, str_val):
        self.queue.put(str_val)

    def flush(self):
        pass

class Interface:

    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title('Central de comando')
        self.raiz.geometry('900x700') # Largura x Altura inicial

        # ========== Variáveis que serão definidas pelo usuário ==========
        self.var_nome = tk.StringVar()
        self.var_operador = tk.StringVar()
        self.var_texto = tk.StringVar()
        self.var_inicio = tk.DoubleVar()
        self.var_fim = tk.DoubleVar()
        self.var_fenda = tk.DoubleVar(value=100)
        self.var_ppr = tk.IntVar(value=5) # Valor padrão
        self.var_porta_lockin = tk.StringVar(value='COM10')
        self.var_porta_arduino = tk.StringVar(value='COM13')
        # Checkbox para Simulação
        self.var_simulacao = tk.BooleanVar(value=True)

        # Método que desenha a tela
        self.completa_janela() # Quando o Objeto for criado (instanciado), a janela será aberta e preenchida

        # Configurar redirecionamento de logs
        self.redirector = TextRedirector(self.txt_log)
        self.check_log_queue()


    # region Operação
    def inicia_thread(self):
        """Essa função é cahmada quando o botão de início recebe um clique."""

        if not self.var_nome.get():
            messagebox.showwarning('Atenção', 'O campo "Nome do Arquivo" é obrigatório.')
            return
        
        # Bloqueia input durante execução
        self.sys_stdout_original = sys.stdout
        sys.stdout = self.redirector # Redireciona prints

        self.botao_iniciar.config(state='disabled') # Trava o botão, evita o duplo clique
        self.botao_parar.config(state='nomal')
        self.log_status.config(text='Status: Inicializando...', foreground='orange')

        # Limpa o gráfico anterior
        self.ax.cla()
        self.ax.set_title('Espectro em Tempo Real')
        self.ax.set_xlabel('Comprimento de Onda (Å)')
        self.ax.set_ylabel('Sinal (V)')
        self.ax.grid(True, linestyle='--')
        self.canvas.draw()
        
        # ========== Criar a thread ==========
        # target --> a função que vai rodar na thread secundária
        t = threading.Thread(target=self.rodar_pyce)
        t.daemon = True # Se fechar a janela, a thread morre junto
        t.start()

    def rodar_pyce(self):
        print('Thread: Iniciando experimento...')
        
        pyce.plt.show = lambda: None  # Anula o "show()", pois trava a thread; "Monkey Patching"; Redefine o plt.show!!!!!
        pyce.plt.pause = lambda x: time.sleep(x) # Troca pause por sleep (mais leve)

        try:
            # Instanciando a filha da classe original com os dados da tela
            # ".get()" para pegar o valor das variáveis
            self.experimento_atual = ExperimentoGUI(
                fig=self.fig,
                ax=self.ax,
                canvas=self.canvas,
                modo_simulacao=self.var_simulacao.get(),
                nome_arquivo=self.var_nome.get(),
                operador=self.var_operador.get(),
                comp_i=self.var_inicio.get(),
                comp_f=self.var_fim.get(),
                tamanho_fenda=self.var_fenda.get(),
                ppr=self.var_ppr.get(),
                descricao=self.var_texto.get()
            )

            # Prepara dicionários de conexão
            conexao_lockin = {'porta': self.var_porta_lockin.get(), 'baudrate': 9600}
            conexao_arduino = {'porta': self.var_porta_arduino.get(), 'baudrate': 9600}

            print('Thread: Conectando equipamentos...')
            self.experimento_atual.conectar(conexao_lockin, conexao_arduino)
            self.raiz.after(0, lambda: self.log_status.config(text='Status: Rodando...', foreground='green'))
            
            print('Thread: Executando run()...')
            self.experimento_atual.run() # Roda o loop principal do pyce.py
            self.nome_excluivo = self.experimento_atual.nome_exclusivo
            self.raiz.after(0, lambda: self.log_status.config(text='Status: Concluído.', foreground='blue'))

        except Exception as e:
            print(f'ERRO NA THREAD: {e}')
            self.raiz.after(0, lambda: messagebox.showerror('Erro no Experimento', str(e)))
            self.raiz.after(0, lambda: self.log_status.config(text='Status: Erro', foreground='red'))

        finally:
            sys.stdout = self.sys_stdout_original # Restaura print normal
            self.experimento_atual = None
            self.raiz.after(0, self.resetar_botoes)
            
            
            self.fig.tight_layout()
            self.fig.set_size_inches(8, 5)
            self.fig.savefig(f'{self.nome_excluivo}.jpg', dpi=300)

    def parar_experimento(self):
        """Ativada caso o botão de parada seja acionado."""

        if self.experimento_atual:
            self.log_status.config(text='Status: Parando...', foreground='red')
            # Define a flag que existe na classe Experimento original
            self.experimento_atual.evento_abortar_experimento = True
        else:
            print('Nenhum experimento rodando para parar.')

    def resetar_botoes(self):
        """Garnate o estado original dos botões."""

        self.botao_iniciar.config(state='normal')
        self.botao_parar.config(state='disabled')
    
    def check_log_queue(self):
        """Verifica se há mensagens na fila do print para exibir na GUI"""
        while not self.redirector.queue.empty():
            msg = self.redirector.queue.get()
            self.txt_log.configure(state='normal')
            self.txt_log.insert(tk.END, msg)
            self.txt_log.see(tk.END)
            self.txt_log.configure(state='disabled')
        self.raiz.after(100, self.check_log_queue)
    # endregion
    
    def completa_janela(self):
        
        # Frame Principal que será dividido em esquerda (Controles) e direita (Gráfico)
        main_frame = ttk.Frame(self.raiz)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # ===== Cria painel esquerdo
        painel_esquerdo = ttk.LabelFrame(main_frame, text='Parâmetros do Experimento')
        painel_esquerdo.pack(side='left', fill='y', padx=10, pady=10) # Gruda na esquerda e preenche apenas em y

        # ===== Cria painel direito
        painel_direito = ttk.Frame(main_frame)
        painel_direito.pack(side='right', fill='both', expand=True)


        # ========== Esquerda ==========
        # ===== Campos de preenchimento
        campos = [
            ('Nome do Arquivo:', self.var_nome),
            ('Operador:', self.var_operador),
            ('Texto informativo:', self.var_texto),
            ('Início (Å):', self.var_inicio),
            ('Fim (Å):', self.var_fim),
            ('Fenda (µm):', self.var_fenda),
            ('Pontos/Resolução:', self.var_ppr),
            ('Porta Lockin:', self.var_porta_lockin),
            ('Porta Arduino:', self.var_porta_arduino)

        ]
        for i, (texto, variavel) in enumerate(campos):
            # Label (Rótulo)
            label = ttk.Label(painel_esquerdo, text=texto)
            label.grid(row=i, column=0, sticky='w', pady=5, padx=5)
            
            # Entry (Caixa de digitar)
            entrada = ttk.Entry(painel_esquerdo, textvariable=variavel)
            entrada.grid(row=i, column=1, pady=5, padx=5)

        # ===== Botões
        # OBS: command quer uma referência para a função
        self.botao_iniciar = ttk.Button(painel_esquerdo, text='Iniciar experimento', command=self.inicia_thread) # --> Chama o método preparar thread
        self.botao_iniciar.grid(row=len(campos), columnspan=2, pady=(20, 5), sticky='ew')

        self.botao_parar = ttk.Button(painel_esquerdo, text='Parar experimento', command=self.parar_experimento, state='disabled')
        self.botao_parar.grid(row=len(campos) + 1, columnspan=2, pady=(5, 10), sticky='ew')

        # ===== Checkbox de simulação
        chk_sim = ttk.Checkbutton(painel_esquerdo, text='Modo Simulação (Teste)', variable=self.var_simulacao)
        chk_sim.grid(row=len(campos) + 2, columnspan=2, pady=5)

        # ===== Log de status simples
        self.log_status = ttk.Label(painel_esquerdo, text='Status: Aguardando...', foreground='blue')
        self.log_status.grid(row=len(campos) + 3, columnspan=2, pady=15)

        # ===== Texto rolável
        frame_log = ttk.Frame(painel_esquerdo)
        frame_log.grid(row=len(campos) + 4, column=0, columnspan=2, pady=10, sticky='ew')
        self.txt_log = scrolledtext.ScrolledText(frame_log, width=30, height=12, state='disabled') # Largura em caracteres
        self.txt_log.pack(fill='both', expand=True)


        # ========== Direita (Gráfico) ==========
        self.fig = Figure(dpi=100) # figsize=(5, 4)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title('Espectro em Tempo Real')
        self.ax.set_xlabel('Comprimento de Onda (Å)')
        self.ax.set_ylabel('Sinal (V)')
        self.ax.grid(True, linestyle='--')

        self.canvas = FigureCanvasTkAgg(self.fig, master=painel_direito)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
    


if __name__ == '__main__':
    raiz = tk.Tk()
    app = Interface(raiz)
    raiz.mainloop() # Um loop infinito que espera um ação --> Mantém a janela aberta