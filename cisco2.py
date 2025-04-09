import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import serial
import serial.tools.list_ports
import time
import ipaddress
import logging
import re
import json
import os
from threading import Thread
import queue
import webbrowser

# Configuración de constantes
BAUDRATE = 9600
TIMEOUT = 1
DELAY_ENTRE_COMANDOS = 0.3
LOG_FILE = 'router_config.log'
PLANTILLAS_DIR = 'plantillas'
DOCS_FILE = 'documentacion.html'

# Configurar logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.showtip)
        self.widget.bind("<Leave>", self.hidetip)
        self.widget.bind("<ButtonPress>", self.hidetip)

    def showtip(self, event=None):
        "Display tooltip"
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            tw, 
            text=self.text, 
            justify=tk.LEFT,
            background="#ffffe0", 
            relief=tk.SOLID, 
            borderwidth=1,
            font=("Tahoma", "9", "normal"),
            padx=5,
            pady=3
        )
        label.pack()

    def hidetip(self, event=None):
        "Hide tooltip"
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class TerminalSerial(tk.Toplevel):
    def __init__(self, parent, puerto):
        super().__init__(parent)
        self.title(f"Terminal Serial - {puerto}")
        self.puerto = puerto
        self.serial_conn = None
        self.running = True
        
        self.setup_ui()
        self.connect_serial()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.queue = queue.Queue()
        self.after(100, self.process_queue)
    
    def setup_ui(self):
        """Configura la interfaz del terminal"""
        self.text_area = tk.Text(self, wrap=tk.WORD, state='disabled')
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        frame = tk.Frame(self)
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.entry = tk.Entry(frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.send_command)
        
        btn_send = ttk.Button(frame, text="Enviar", command=self.send_command)
        btn_send.pack(side=tk.LEFT, padx=5)
        
        btn_clear = ttk.Button(frame, text="Limpiar", command=self.clear_output)
        btn_clear.pack(side=tk.LEFT)
    
    def connect_serial(self):
        """Establece conexión serial"""
        try:
            self.serial_conn = serial.Serial(
                self.puerto,
                BAUDRATE,
                timeout=TIMEOUT
            )
            Thread(target=self.read_serial, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar: {e}")
            self.destroy()
    
    def read_serial(self):
        """Lee datos del puerto serial en segundo plano"""
        while self.running and self.serial_conn and self.serial_conn.is_open:
            try:
                if self.serial_conn.in_waiting:
                    data = self.serial_conn.read(self.serial_conn.in_waiting).decode('ascii', errors='replace')
                    self.queue.put(data)
            except Exception as e:
                logging.error(f"Error lectura serial: {e}")
                break
    
    def process_queue(self):
        """Procesa los datos recibidos del puerto serial"""
        while not self.queue.empty():
            data = self.queue.get()
            self.text_area.config(state='normal')
            self.text_area.insert(tk.END, data)
            self.text_area.see(tk.END)
            self.text_area.config(state='disabled')
        self.after(100, self.process_queue)
    
    def send_command(self, event=None):
        """Envía un comando al puerto serial"""
        cmd = self.entry.get()
        if cmd and self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write((cmd + "\n").encode())
                self.entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Error al enviar comando: {e}")
    
    def clear_output(self):
        """Limpia el área de texto"""
        self.text_area.config(state='normal')
        self.text_area.delete(1.0, tk.END)
        self.text_area.config(state='disabled')
    
    def on_close(self):
        """Maneja el cierre de la ventana"""
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.destroy()

class RouterConfigurator:
    def __init__(self, root):
        self.root = root
        self.root.title("Configurador de Router Cisco Pro")
        self.plantillas = {}
        self.setup_directorios()
        self.setup_logging()
        self.setup_styles()
        self.setup_ui()
        self.serial_connection = None
        self.cargar_plantillas()
    
    def setup_directorios(self):
        """Crea directorios necesarios si no existen"""
        if not os.path.exists(PLANTILLAS_DIR):
            os.makedirs(PLANTILLAS_DIR)
    
    def setup_logging(self):
        """Configura logging avanzado"""
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Handler para archivo
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def listar_puertos(self):
        """Lista los puertos seriales disponibles"""
        puertos = serial.tools.list_ports.comports()
        return [p.device for p in puertos]
    
    def setup_styles(self):
        """Configura estilos visuales"""
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0")
        style.configure("TNotebook.Tab", padding=[10, 5])
    
    def setup_ui(self):
        """Configura la interfaz gráfica de usuario"""
        self.setup_menu()
        self.setup_port_selection()
        self.setup_notebook()
        self.setup_buttons()
        self.setup_status_bar()
    
    def setup_menu(self):
        """Configura el menú superior"""
        menubar = tk.Menu(self.root)
        
        # Menú Archivo
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Abrir plantilla", command=self.cargar_plantilla_dialog)
        filemenu.add_command(label="Guardar plantilla", command=self.guardar_plantilla_dialog)
        filemenu.add_separator()
        filemenu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=filemenu)
        
        # Menú Herramientas
        toolsmenu = tk.Menu(menubar, tearoff=0)
        toolsmenu.add_command(label="Terminal Serial", command=self.abrir_terminal)
        toolsmenu.add_command(label="Monitorizar interfaces", command=self.monitorear_interfaces)
        toolsmenu.add_command(label="Pruebas de conectividad", command=self.probar_conectividad)
        menubar.add_cascade(label="Herramientas", menu=toolsmenu)
        
        # Menú Ayuda
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Documentación", command=self.mostrar_documentacion)
        helpmenu.add_command(label="Acerca de...", command=self.mostrar_acerca_de)
        menubar.add_cascade(label="Ayuda", menu=helpmenu)
        
        self.root.config(menu=menubar)
    
    def setup_status_bar(self):
        """Configura la barra de estado"""
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message):
        """Actualiza el mensaje en la barra de estado"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def setup_port_selection(self):
        """Configura el frame de selección de puerto"""
        frame_top = tk.Frame(self.root, bg="#f0f0f0")
        frame_top.pack(pady=10, fill=tk.X, padx=10)
        
        tk.Label(
            frame_top, 
            text="Puerto COM:", 
            bg="#f0f0f0"
        ).pack(side=tk.LEFT)
        
        self.puerto_var = tk.StringVar()
        self.puerto_combo = ttk.Combobox(
            frame_top, 
            textvariable=self.puerto_var, 
            values=self.listar_puertos(), 
            width=20
        )
        self.puerto_combo.pack(side=tk.LEFT, padx=5)
        
        btn_refresh = ttk.Button(
            frame_top, 
            text="Actualizar", 
            command=self.actualizar_puertos
        )
        btn_refresh.pack(side=tk.LEFT, padx=5)
        
        btn_terminal = ttk.Button(
            frame_top,
            text="Terminal Serial",
            command=self.abrir_terminal
        )
        btn_terminal.pack(side=tk.LEFT, padx=5)
        
        # Tooltips
        Tooltip(self.puerto_combo, "Selecciona el puerto serial conectado al router")
        Tooltip(btn_refresh, "Actualiza la lista de puertos disponibles")
        Tooltip(btn_terminal, "Abre una terminal serial interactiva")
    
    def abrir_terminal(self):
        """Abre la terminal serial interactiva"""
        puerto = self.puerto_var.get()
        if puerto:
            try:
                TerminalSerial(self.root, puerto)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir terminal: {e}")
        else:
            messagebox.showwarning("Advertencia", "Selecciona un puerto COM primero")
    
    def actualizar_puertos(self):
        """Actualiza la lista de puertos COM disponibles"""
        self.puerto_combo['values'] = self.listar_puertos()
        self.update_status("Lista de puertos COM actualizada")
    
    def setup_notebook(self):
        """Configura el notebook con las pestañas de configuración"""
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # Crear pestañas
        self.setup_basic_tab()
        self.setup_serial_tab()
        self.setup_ssh_tab()
        self.setup_dhcp_tab()
        self.setup_routing_tab()
        self.setup_vlan_tab()
    
    def create_label_with_tooltip(self, parent, text, tooltip, row, column):
        """Crea una etiqueta con tooltip"""
        label = tk.Label(parent, text=text, bg="#f0f0f0")
        label.grid(row=row, column=column, sticky="e", pady=2)
        Tooltip(label, tooltip)
        return label
    
    def create_entry_with_tooltip(self, parent, row, tooltip, **kwargs):
        """Crea un campo de entrada con tooltip"""
        entry = tk.Entry(parent, **kwargs)
        entry.grid(row=row, column=1, pady=2, sticky="ew", padx=(0, 10))
        Tooltip(entry, tooltip)
        return entry
    
    def setup_basic_tab(self):
        """Configura la pestaña de configuración básica"""
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Básico")
        
        # Diccionario con mensajes de ayuda
        help_msgs = {
            'hostname': "Nombre identificativo del router (ej: RouterSucursal1)",
            'consola_pass': "Contraseña para acceso por consola física (mínimo 6 caracteres)",
            'enable_pass': "Contraseña para modo privilegiado (enable mode)",
            'banner': "Mensaje que se muestra al conectarse al router (evitar usar #)",
            'lan_int': "Nombre de interfaz LAN (ej: FastEthernet0/0, GigabitEthernet0/1)",
            'lan_ip': "Dirección IP para la interfaz LAN (ej: 192.168.1.1)",
            'lan_mask': "Máscara de red para la interfaz LAN (ej: 255.255.255.0)",
            'del_int': "Interfaz a resetear (se eliminará su configuración)"
        }
        
        # Hostname
        row = 0
        self.create_label_with_tooltip(tab, "Hostname:", help_msgs['hostname'], row, 0)
        self.hostname_entry = self.create_entry_with_tooltip(tab, row, help_msgs['hostname'])
        
        # Contraseña de consola
        row += 1
        self.create_label_with_tooltip(tab, "Contraseña consola:", help_msgs['consola_pass'], row, 0)
        self.consola_pass = self.create_entry_with_tooltip(tab, row, help_msgs['consola_pass'], show="*")
        
        # Contraseña enable
        row += 1
        self.create_label_with_tooltip(tab, "Contraseña enable:", help_msgs['enable_pass'], row, 0)
        self.enable_pass = self.create_entry_with_tooltip(tab, row, help_msgs['enable_pass'], show="*")
        
        # Banner
        row += 1
        self.create_label_with_tooltip(tab, "Mensaje de banner:", help_msgs['banner'], row, 0)
        self.banner_msg = self.create_entry_with_tooltip(tab, row, help_msgs['banner'])
        
        # Interfaz LAN
        row += 1
        self.create_label_with_tooltip(tab, "Interfaz LAN:", help_msgs['lan_int'], row, 0)
        self.lan_interface = self.create_entry_with_tooltip(tab, row, help_msgs['lan_int'])
        
        row += 1
        self.create_label_with_tooltip(tab, "IP LAN:", help_msgs['lan_ip'], row, 0)
        self.lan_ip = self.create_entry_with_tooltip(tab, row, help_msgs['lan_ip'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Máscara LAN:", help_msgs['lan_mask'], row, 0)
        self.lan_mask = self.create_entry_with_tooltip(tab, row, help_msgs['lan_mask'])
        
        # Interfaz a borrar
        row += 1
        self.create_label_with_tooltip(tab, "Interfaz a borrar:", help_msgs['del_int'], row, 0)
        self.interfaz_borrar_entry = self.create_entry_with_tooltip(tab, row, help_msgs['del_int'])
        
        # Configurar peso de columnas para expansión
        tab.columnconfigure(1, weight=1)
    
    def setup_serial_tab(self):
        """Configura la pestaña de interfaz serial"""
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Serial")
        
        help_msgs = {
            'serial_int': "Nombre de interfaz serial (ej: Serial0/0/0)",
            'serial_ip': "Dirección IP para la interfaz serial",
            'serial_mask': "Máscara de red para la interfaz serial",
            'clock': "Velocidad de reloj en bps (solo para DCE)",
            'shutdown': "Activar/desactivar la interfaz (no shutdown/shutdown)"
        }
        
        row = 0
        self.create_label_with_tooltip(tab, "Puerto Serial:", help_msgs['serial_int'], row, 0)
        self.serial_interface = self.create_entry_with_tooltip(tab, row, help_msgs['serial_int'])
        
        row += 1
        self.create_label_with_tooltip(tab, "IP Serial:", help_msgs['serial_ip'], row, 0)
        self.serial_ip = self.create_entry_with_tooltip(tab, row, help_msgs['serial_ip'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Máscara Serial:", help_msgs['serial_mask'], row, 0)
        self.serial_mask = self.create_entry_with_tooltip(tab, row, help_msgs['serial_mask'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Clock rate:", help_msgs['clock'], row, 0)
        self.serial_clock_rate = self.create_entry_with_tooltip(tab, row, help_msgs['clock'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Activar puerto:", help_msgs['shutdown'], row, 0)
        self.serial_shutdown_var = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(
            tab, 
            variable=self.serial_shutdown_var,
            bg="#f0f0f0",
            activebackground="#f0f0f0"
        )
        chk.grid(row=row, column=1, sticky="w")
        Tooltip(chk, help_msgs['shutdown'])
        
        tab.columnconfigure(1, weight=1)
    
    def setup_ssh_tab(self):
        """Configura la pestaña de SSH"""
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="SSH")
        
        help_msgs = {
            'domain': "Nombre de dominio para las claves SSH",
            'ssh_user': "Nombre de usuario para acceso SSH",
            'ssh_pass': "Contraseña para el usuario SSH"
        }
        
        row = 0
        self.create_label_with_tooltip(tab, "Dominio:", help_msgs['domain'], row, 0)
        self.ssh_dominio = self.create_entry_with_tooltip(tab, row, help_msgs['domain'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Usuario SSH:", help_msgs['ssh_user'], row, 0)
        self.ssh_usuario = self.create_entry_with_tooltip(tab, row, help_msgs['ssh_user'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Contraseña SSH:", help_msgs['ssh_pass'], row, 0)
        self.ssh_clave = self.create_entry_with_tooltip(tab, row, help_msgs['ssh_pass'], show="*")
        
        tab.columnconfigure(1, weight=1)
    
    def setup_dhcp_tab(self):
        """Configura la pestaña de DHCP"""
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="DHCP")
        
        help_msgs = {
            'pool': "Nombre identificativo del pool DHCP",
            'network': "Red a asignar (ej: 192.168.1.0)",
            'netmask': "Máscara de la red DHCP",
            'gateway': "Gateway por defecto para los clientes",
            'range_start': "Inicio del rango de direcciones asignables",
            'range_end': "Fin del rango de direcciones asignables"
        }
        
        row = 0
        self.create_label_with_tooltip(tab, "Nombre pool:", help_msgs['pool'], row, 0)
        self.dhcp_pool = self.create_entry_with_tooltip(tab, row, help_msgs['pool'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Red:", help_msgs['network'], row, 0)
        self.dhcp_red = self.create_entry_with_tooltip(tab, row, help_msgs['network'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Máscara:", help_msgs['netmask'], row, 0)
        self.dhcp_mascara = self.create_entry_with_tooltip(tab, row, help_msgs['netmask'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Gateway:", help_msgs['gateway'], row, 0)
        self.dhcp_gateway = self.create_entry_with_tooltip(tab, row, help_msgs['gateway'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Rango inicial:", help_msgs['range_start'], row, 0)
        self.dhcp_rango_ini = self.create_entry_with_tooltip(tab, row, help_msgs['range_start'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Rango final:", help_msgs['range_end'], row, 0)
        self.dhcp_rango_fin = self.create_entry_with_tooltip(tab, row, help_msgs['range_end'])
        
        tab.columnconfigure(1, weight=1)
    
    def setup_routing_tab(self):
        """Configura la pestaña de enrutamiento"""
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Enrutamiento")
        
        help_msgs = {
            'protocol': "Protocolo de enrutamiento (RIP, OSPF o EIGRP)",
            'network': "Red a anunciar (ej: 192.168.1.0)",
            'wildcard': "Máscara wildcard (para OSPF, ej: 0.0.0.255)",
            'area': "Área OSPF (ej: 0)",
            'asn': "Número de sistema autónomo (para EIGRP)"
        }
        
        row = 0
        self.create_label_with_tooltip(tab, "Protocolo:", help_msgs['protocol'], row, 0)
        self.protocolo_var = tk.StringVar()
        protocolo_combo = ttk.Combobox(
            tab, 
            textvariable=self.protocolo_var, 
            values=["rip", "ospf", "eigrp"], 
            state="readonly"
        )
        protocolo_combo.grid(row=row, column=1, sticky="ew", pady=2)
        Tooltip(protocolo_combo, help_msgs['protocol'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Red:", help_msgs['network'], row, 0)
        self.ruteo_red = self.create_entry_with_tooltip(tab, row, help_msgs['network'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Wildcard:", help_msgs['wildcard'], row, 0)
        self.ruteo_wc = self.create_entry_with_tooltip(tab, row, help_msgs['wildcard'])
        
        row += 1
        self.create_label_with_tooltip(tab, "Área OSPF:", help_msgs['area'], row, 0)
        self.ruteo_area = self.create_entry_with_tooltip(tab, row, help_msgs['area'])
        
        row += 1
        self.create_label_with_tooltip(tab, "ASN EIGRP:", help_msgs['asn'], row, 0)
        self.ruteo_as = self.create_entry_with_tooltip(tab, row, help_msgs['asn'])
        
        tab.columnconfigure(1, weight=1)
    
    def setup_vlan_tab(self):
        """Configura la pestaña de VLANs"""
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="VLANs")
        
        help_msgs = {
            'vlan_id': "ID de VLAN (1-4094)",
            'vlan_name': "Nombre descriptivo de la VLAN",
            'vlan_int': "Interfaz a asignar (ej: FastEthernet0/1)",
            'vlan_mode': "Modo de puerto (access o trunk)"
        }
        
        # Frame para lista de VLANs
        frame_list = ttk.Frame(tab)
        frame_list.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview para mostrar VLANs configuradas
        self.vlan_tree = ttk.Treeview(frame_list, columns=('id', 'name', 'interface', 'mode'), show='headings')
        self.vlan_tree.heading('id', text='ID')
        self.vlan_tree.heading('name', text='Nombre')
        self.vlan_tree.heading('interface', text='Interfaz')
        self.vlan_tree.heading('mode', text='Modo')
        self.vlan_tree.pack(fill=tk.BOTH, expand=True)
        
        # Frame para controles
        frame_controls = ttk.Frame(tab)
        frame_controls.pack(fill=tk.X, pady=5)
        
        # Campos para nueva VLAN
        row = 0
        self.create_label_with_tooltip(frame_controls, "ID VLAN:", help_msgs['vlan_id'], row, 0)
        self.vlan_id_entry = self.create_entry_with_tooltip(frame_controls, row, help_msgs['vlan_id'])
        
        row += 1
        self.create_label_with_tooltip(frame_controls, "Nombre VLAN:", help_msgs['vlan_name'], row, 0)
        self.vlan_name_entry = self.create_entry_with_tooltip(frame_controls, row, help_msgs['vlan_name'])
        
        row += 1
        self.create_label_with_tooltip(frame_controls, "Interfaz:", help_msgs['vlan_int'], row, 0)
        self.vlan_interface_entry = self.create_entry_with_tooltip(frame_controls, row, help_msgs['vlan_int'])
        
        row += 1
        self.create_label_with_tooltip(frame_controls, "Modo:", help_msgs['vlan_mode'], row, 0)
        self.vlan_mode_var = tk.StringVar()
        vlan_mode_combo = ttk.Combobox(
            frame_controls, 
            textvariable=self.vlan_mode_var, 
            values=["access", "trunk"], 
            state="readonly"
        )
        vlan_mode_combo.grid(row=row, column=1, sticky="ew", pady=2)
        Tooltip(vlan_mode_combo, help_msgs['vlan_mode'])
        
        # Botones para manejar VLANs
        btn_frame = ttk.Frame(frame_controls)
        btn_frame.grid(row=row+1, column=0, columnspan=2, pady=5)
        
        btn_add = ttk.Button(btn_frame, text="Agregar VLAN", command=self.agregar_vlan)
        btn_add.pack(side=tk.LEFT, padx=5)
        
        btn_remove = ttk.Button(btn_frame, text="Eliminar VLAN", command=self.eliminar_vlan)
        btn_remove.pack(side=tk.LEFT, padx=5)
        
        tab.columnconfigure(1, weight=1)
    
    def agregar_vlan(self):
        """Agrega una nueva VLAN a la lista"""
        vlan_id = self.vlan_id_entry.get()
        vlan_name = self.vlan_name_entry.get()
        vlan_interface = self.vlan_interface_entry.get()
        vlan_mode = self.vlan_mode_var.get()
        
        if not vlan_id or not vlan_name or not vlan_interface or not vlan_mode:
            messagebox.showwarning("Advertencia", "Todos los campos son requeridos")
            return
        
        try:
            vlan_id_num = int(vlan_id)
            if not (1 <= vlan_id_num <= 4094):
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "ID de VLAN debe ser un número entre 1 y 4094")
            return
        
        self.vlan_tree.insert('', tk.END, values=(vlan_id, vlan_name, vlan_interface, vlan_mode))
        
        # Limpiar campos después de agregar
        self.vlan_id_entry.delete(0, tk.END)
        self.vlan_name_entry.delete(0, tk.END)
        self.vlan_interface_entry.delete(0, tk.END)
        self.vlan_mode_var.set('')
    
    def eliminar_vlan(self):
        """Elimina la VLAN seleccionada"""
        selected_item = self.vlan_tree.selection()
        if selected_item:
            self.vlan_tree.delete(selected_item)
        else:
            messagebox.showwarning("Advertencia", "Selecciona una VLAN para eliminar")
    
    def setup_buttons(self):
        """Configura los botones inferiores"""
        frame_bottom = tk.Frame(self.root, bg="#f0f0f0")
        frame_bottom.pack(pady=10, fill=tk.X, padx=10)
        
        buttons = [
            ("Vista previa", self.vista_previa, "Muestra los comandos que se generarán"),
            ("Guardar configuración", self.guardar_como_txt, "Guarda los comandos en un archivo"),
            ("Enviar configuración", self.iniciar_envio_config, "Envía los comandos al router"),
            ("Hacer Backup", self.hacer_backup, "Descarga la configuración actual del router")
        ]
        
        for text, command, tooltip in buttons:
            btn = ttk.Button(
                frame_bottom, 
                text=text, 
                command=command
            )
            btn.pack(side=tk.LEFT, padx=5)
            Tooltip(btn, tooltip)
    
    def validar_ip(self, ip):
        """Valida que una cadena sea una dirección IP válida"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def validar_formato_ip(self, ip):
        """Valida formato de IP con expresiones regulares"""
        patron_ip = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if not re.match(patron_ip, ip):
            return False
        return all(0 <= int(octeto) <= 255 for octeto in ip.split('.'))
    
    def generar_comandos_basicos(self):
        """Genera los comandos de configuración básica"""
        comandos = ["enable", "configure terminal"]
        
        # Hostname
        if hostname := self.hostname_entry.get().strip():
            comandos.append(f"hostname {hostname}")
        
        # Contraseñas
        if enable_pass := self.enable_pass.get().strip():
            comandos.append(f"enable secret {enable_pass}")
        
        if consola_pass := self.consola_pass.get().strip():
            comandos.extend([
                "line console 0",
                f"password {consola_pass}",
                "login",
                "exit"
            ])
        
        # Banner
        if banner := self.banner_msg.get().strip():
            delimitador = "$" if "$" not in banner else "#"
            comandos.append(f"banner motd {delimitador}{banner}{delimitador}")
        
        # Interfaz LAN
        if (interfaz := self.lan_interface.get().strip()) and \
           (ip := self.lan_ip.get().strip()) and \
           (mask := self.lan_mask.get().strip()):
            if self.validar_ip(ip):
                comandos.extend([
                    f"interface {interfaz}",
                    f"ip address {ip} {mask}",
                    "no shutdown",
                    "exit"
                ])
            else:
                logging.warning(f"IP LAN no válida: {ip}")
        
        # Borrar interfaz
        if interfaz := self.interfaz_borrar_entry.get().strip():
            comandos.extend([
                f"interface {interfaz}",
                "shutdown",
                "no ip address",
                "no clock rate",
                "exit"
            ])
        
        return comandos
    
    def generar_comandos_serial(self):
        """Genera los comandos para interfaz serial"""
        comandos = []
        
        if (interfaz := self.serial_interface.get().strip()) and \
           (ip := self.serial_ip.get().strip()) and \
           (mask := self.serial_mask.get().strip()):
            
            if not self.validar_ip(ip):
                logging.warning(f"IP serial no válida: {ip}")
                return comandos
                
            comandos.extend([
                f"interface {interfaz}",
                f"ip address {ip} {mask}"
            ])
            
            if clock_rate := self.serial_clock_rate.get().strip():
                if clock_rate.isdigit():
                    comandos.append(f"clock rate {clock_rate}")
                else:
                    logging.warning(f"Clock rate no válido: {clock_rate}")
            
            if self.serial_shutdown_var.get():
                comandos.append("no shutdown")
            
            comandos.append("exit")
        
        return comandos
    
    def generar_comandos_ssh(self):
        """Genera los comandos para configuración SSH"""
        comandos = []
        
        if (dominio := self.ssh_dominio.get().strip()) and \
           (usuario := self.ssh_usuario.get().strip()) and \
           (clave := self.ssh_clave.get().strip()):
            
            comandos.extend([
                f"ip domain-name {dominio}",
                f"username {usuario} password {clave}",
                "crypto key generate rsa",
                "1024",  # Tamaño de clave
                "line vty 0 4",
                "transport input ssh",
                "login local",
                "exit"
            ])
        
        return comandos
    
    def generar_comandos_dhcp(self):
        """Genera los comandos para configuración DHCP"""
        comandos = []
        
        if (pool := self.dhcp_pool.get().strip()) and \
           (red := self.dhcp_red.get().strip()) and \
           (mascara := self.dhcp_mascara.get().strip()) and \
           (gateway := self.dhcp_gateway.get().strip()):
            
            if ini := self.dhcp_rango_ini.get().strip():
                if fin := self.dhcp_rango_fin.get().strip():
                    if self.validar_ip(ini) and self.validar_ip(fin):
                        comandos.append(f"ip dhcp excluded-address {ini} {fin}")
                    else:
                        logging.warning("Rango DHCP no válido")
            
            comandos.extend([
                f"ip dhcp pool {pool}",
                f"network {red} {mascara}",
                f"default-router {gateway}"
            ])
        
        return comandos
    
    def generar_comandos_ruteo(self):
        """Genera los comandos para enrutamiento dinámico"""
        comandos = []
        proto = self.protocolo_var.get()
        
        if proto == "rip" and (red := self.ruteo_red.get().strip()):
            comandos.extend([
                "router rip",
                "version 2",
                f"network {red}",
                "exit"
            ])
        
        elif proto == "ospf" and (red := self.ruteo_red.get().strip()) and \
             (wc := self.ruteo_wc.get().strip()) and \
             (area := self.ruteo_area.get().strip()):
            
            comandos.extend([
                "router ospf 1",
                f"network {red} {wc} area {area}",
                "exit"
            ])
        
        elif proto == "eigrp" and (red := self.ruteo_red.get().strip()) and \
             (asn := self.ruteo_as.get().strip()):
            
            if asn.isdigit():
                comandos.extend([
                    f"router eigrp {asn}",
                    f"network {red}",
                    "exit"
                ])
            else:
                logging.warning("ASN debe ser numérico")
        
        return comandos
    
    def generar_comandos_vlans(self):
        """Genera comandos para configuración de VLANs"""
        comandos = []
        
        for child in self.vlan_tree.get_children():
            vlan_id, vlan_name, interface, mode = self.vlan_tree.item(child)['values']
            
            comandos.extend([
                f"vlan {vlan_id}",
                f"name {vlan_name}",
                "exit",
                f"interface {interface}",
                f"switchport mode {mode}",
                f"switchport access vlan {vlan_id}" if mode == "access" else "",
                "no shutdown",
                "exit"
            ])
        
        return [cmd for cmd in comandos if cmd]  # Elimina cadenas vacías
    
    def generar_comandos(self):
        """Genera todos los comandos de configuración"""
        try:
            comandos = []
            comandos.extend(self.generar_comandos_basicos())
            comandos.extend(self.generar_comandos_serial())
            comandos.extend(self.generar_comandos_ssh())
            comandos.extend(self.generar_comandos_dhcp())
            comandos.extend(self.generar_comandos_ruteo())
            comandos.extend(self.generar_comandos_vlans())
            
            # Comandos finales
            comandos.extend(["exit", "write memory"])
            
            logging.info("Comandos generados correctamente")
            return comandos
        
        except Exception as e:
            logging.error(f"Error al generar comandos: {str(e)}")
            messagebox.showerror("Error", f"Error al generar comandos:\n{str(e)}")
            return []
    
    def vista_previa(self):
        """Muestra una vista previa de la configuración"""
        comandos = self.generar_comandos()
        
        if not comandos:
            return
            
        ventana = tk.Toplevel(self.root)
        ventana.title("Vista previa de configuración")
        
        frame = tk.Frame(ventana)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_area = tk.Text(
            frame, 
            height=25, 
            width=60, 
            yscrollcommand=scrollbar.set,
            wrap=tk.NONE,
            font=('Courier', 10)
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text_area.yview)
        
        text_area.insert(tk.END, "\n".join(comandos))
        text_area.config(state="disabled")
        
        # Botón para copiar al portapapeles
        btn_copy = tk.Button(
            ventana, 
            text="Copiar", 
            command=lambda: self.copiar_al_portapapeles("\n".join(comandos))
        )
        btn_copy.pack(pady=5)
    
    def copiar_al_portapapeles(self, texto):
        """Copia texto al portapapeles"""
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self.update_status("Configuración copiada al portapapeles")
    
    def guardar_como_txt(self):
        """Guarda la configuración en un archivo de texto"""
        comandos = self.generar_comandos()
        
        if not comandos:
            return
            
        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            try:
                with open(archivo, "w") as f:
                    f.write("\n".join(comandos))
                
                messagebox.showinfo("Guardado", f"Configuración guardada en:\n{archivo}")
                logging.info(f"Configuración guardada en {archivo}")
                self.update_status(f"Configuración guardada en {os.path.basename(archivo)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{str(e)}")
                logging.error(f"Error al guardar archivo: {str(e)}")
                self.update_status("Error al guardar configuración")
    
    def cargar_plantillas(self):
        """Carga las plantillas guardadas"""
        self.plantillas = {}
        if os.path.exists(PLANTILLAS_DIR):
            for file in os.listdir(PLANTILLAS_DIR):
                if file.endswith('.json'):
                    try:
                        with open(os.path.join(PLANTILLAS_DIR, file), 'r') as f:
                            self.plantillas[file[:-5]] = json.load(f)
                    except Exception as e:
                        logging.error(f"Error cargando plantilla {file}: {e}")
    
    def guardar_plantilla_dialog(self):
        """Diálogo para guardar plantilla"""
        nombre = simpledialog.askstring("Guardar plantilla", "Nombre de la plantilla:")
        if nombre:
            self.guardar_plantilla(nombre)
    
    def guardar_plantilla(self, nombre):
        """Guarda la configuración actual como plantilla"""
        config = {
            'hostname': self.hostname_entry.get(),
            'consola_pass': self.consola_pass.get(),
            'enable_pass': self.enable_pass.get(),
            'banner': self.banner_msg.get(),
            'lan_interface': self.lan_interface.get(),
            'lan_ip': self.lan_ip.get(),
            'lan_mask': self.lan_mask.get(),
            # ... todos los campos relevantes
        }
        
        try:
            with open(os.path.join(PLANTILLAS_DIR, f"{nombre}.json"), 'w') as f:
                json.dump(config, f, indent=2)
            
            self.cargar_plantillas()
            messagebox.showinfo("Éxito", f"Plantilla '{nombre}' guardada correctamente")
            self.update_status(f"Plantilla '{nombre}' guardada")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la plantilla:\n{str(e)}")
            logging.error(f"Error guardando plantilla: {str(e)}")
    
    def cargar_plantilla_dialog(self):
        """Diálogo para cargar plantilla"""
        if not self.plantillas:
            messagebox.showinfo("Información", "No hay plantillas guardadas")
            return
            
        ventana = tk.Toplevel(self.root)
        ventana.title("Cargar plantilla")
        
        tk.Label(ventana, text="Selecciona una plantilla:").pack(pady=5)
        
        listbox = tk.Listbox(ventana)
        for nombre in self.plantillas.keys():
            listbox.insert(tk.END, nombre)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        btn_frame = tk.Frame(ventana)
        btn_frame.pack(pady=5)
        
        btn_cargar = tk.Button(btn_frame, text="Cargar", command=lambda: self.cargar_plantilla_seleccionada(listbox, ventana))
        btn_cargar.pack(side=tk.LEFT, padx=5)
        
        btn_cancelar = tk.Button(btn_frame, text="Cancelar", command=ventana.destroy)
        btn_cancelar.pack(side=tk.LEFT)
    
    def cargar_plantilla_seleccionada(self, listbox, ventana):
        """Carga la plantilla seleccionada"""
        seleccion = listbox.curselection()
        if seleccion:
            nombre = listbox.get(seleccion[0])
            self.cargar_plantilla(nombre)
            ventana.destroy()
    
    def cargar_plantilla(self, nombre):
        """Carga una plantilla en los campos"""
        if nombre in self.plantillas:
            config = self.plantillas[nombre]
            
            # Limpiar campos primero
            self.hostname_entry.delete(0, tk.END)
            self.consola_pass.delete(0, tk.END)
            self.enable_pass.delete(0, tk.END)
            self.banner_msg.delete(0, tk.END)
            # ... limpiar otros campos
            
            # Llenar con datos de la plantilla
            if 'hostname' in config:
                self.hostname_entry.insert(0, config['hostname'])
            if 'consola_pass' in config:
                self.consola_pass.insert(0, config['consola_pass'])
            if 'enable_pass' in config:
                self.enable_pass.insert(0, config['enable_pass'])
            if 'banner' in config:
                self.banner_msg.insert(0, config['banner'])
            # ... llenar otros campos
            
            self.update_status(f"Plantilla '{nombre}' cargada")
            messagebox.showinfo("Éxito", f"Plantilla '{nombre}' cargada correctamente")
        else:
            messagebox.showerror("Error", f"Plantilla '{nombre}' no encontrada")
    
    def hacer_backup(self):
        """Descarga la configuración actual del router"""
        puerto = self.puerto_var.get()
        if not puerto:
            messagebox.showerror("Error", "Selecciona un puerto COM.")
            return
            
        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt"), ("Todos los archivos", "*.*")],
            title="Guardar backup como"
        )
        
        if not archivo:
            return
            
        try:
            with serial.Serial(puerto, BAUDRATE, timeout=TIMEOUT) as ser:
                time.sleep(2)  # Esperar inicialización
                
                # Enviar comando para obtener configuración
                ser.write(b"enable\n")
                time.sleep(0.5)
                ser.write(b"show running-config\n")
                time.sleep(0.5)
                
                # Leer configuración
                config = []
                start_time = time.time()
                while time.time() - start_time < 10:  # Timeout de 10 segundos
                    if ser.in_waiting:
                        data = ser.read(ser.in_waiting).decode('ascii', errors='replace')
                        config.append(data)
                        if "end" in data.lower():  # Fin de la configuración
                            break
                
                # Guardar en archivo
                with open(archivo, 'w') as f:
                    f.write(''.join(config))
                
                messagebox.showinfo("Éxito", f"Backup guardado en:\n{archivo}")
                self.update_status(f"Backup guardado en {os.path.basename(archivo)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo hacer backup:\n{e}")
            logging.error(f"Error haciendo backup: {e}")
            self.update_status("Error al hacer backup")
    
    def monitorear_interfaces(self):
        """Muestra estadísticas de interfaces"""
        puerto = self.puerto_var.get()
        if not puerto:
            messagebox.showerror("Error", "Selecciona un puerto COM.")
            return
            
        ventana = tk.Toplevel(self.root)
        ventana.title("Monitor de Interfaces")
        
        text_area = tk.Text(ventana, wrap=tk.WORD, state='disabled')
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def actualizar_datos():
            try:
                with serial.Serial(puerto, BAUDRATE, timeout=TIMEOUT) as ser:
                    time.sleep(2)
                    
                    # Obtener estado de interfaces
                    ser.write(b"enable\n")
                    time.sleep(0.5)
                    ser.write(b"show ip interface brief\n")
                    time.sleep(1)
                    
                    # Leer respuesta
                    output = []
                    start_time = time.time()
                    while time.time() - start_time < 5:  # Timeout de 5 segundos
                        if ser.in_waiting:
                            data = ser.read(ser.in_waiting).decode('ascii', errors='replace')
                            output.append(data)
                    
                    # Mostrar en el área de texto
                    text_area.config(state='normal')
                    text_area.delete(1.0, tk.END)
                    text_area.insert(tk.END, ''.join(output))
                    text_area.config(state='disabled')
                    
                    # Programar próxima actualización
                    ventana.after(5000, actualizar_datos)
                    
            except Exception as e:
                text_area.config(state='normal')
                text_area.insert(tk.END, f"Error: {str(e)}")
                text_area.config(state='disabled')
        
        # Botón para actualizar manualmente
        btn_frame = tk.Frame(ventana)
        btn_frame.pack(pady=5)
        
        btn_update = tk.Button(btn_frame, text="Actualizar", command=actualizar_datos)
        btn_update.pack(side=tk.LEFT, padx=5)
        
        btn_close = tk.Button(btn_frame, text="Cerrar", command=ventana.destroy)
        btn_close.pack(side=tk.LEFT)
        
        # Iniciar primera actualización
        actualizar_datos()
    
    def probar_conectividad(self):
        """Realiza pruebas de ping y traceroute"""
        target = simpledialog.askstring("Pruebas de conectividad", "Introduce la IP o dominio a probar:")
        if not target:
            return
            
        puerto = self.puerto_var.get()
        if not puerto:
            messagebox.showerror("Error", "Selecciona un puerto COM.")
            return
            
        ventana = tk.Toplevel(self.root)
        ventana.title(f"Pruebas de conectividad a {target}")
        
        notebook = ttk.Notebook(ventana)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña de Ping
        ping_tab = ttk.Frame(notebook)
        notebook.add(ping_tab, text="Ping")
        
        ping_text = tk.Text(ping_tab, wrap=tk.WORD, state='disabled')
        ping_text.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de Traceroute
        trace_tab = ttk.Frame(notebook)
        notebook.add(trace_tab, text="Traceroute")
        
        trace_text = tk.Text(trace_tab, wrap=tk.WORD, state='disabled')
        trace_text.pack(fill=tk.BOTH, expand=True)
        
        def ejecutar_pruebas():
            try:
                with serial.Serial(puerto, BAUDRATE, timeout=TIMEOUT) as ser:
                    time.sleep(2)
                    
                    # Ejecutar ping
                    ser.write(b"enable\n")
                    time.sleep(0.5)
                    ser.write(f"ping {target}\n".encode())
                    time.sleep(3)  # Tiempo para el ping
                    
                    # Leer resultado del ping
                    ping_output = []
                    while ser.in_waiting:
                        data = ser.read(ser.in_waiting).decode('ascii', errors='replace')
                        ping_output.append(data)
                    
                    # Mostrar ping
                    ping_text.config(state='normal')
                    ping_text.delete(1.0, tk.END)
                    ping_text.insert(tk.END, ''.join(ping_output))
                    ping_text.config(state='disabled')
                    
                    # Ejecutar traceroute
                    ser.write(f"traceroute {target}\n".encode())
                    time.sleep(5)  # Tiempo para el traceroute
                    
                    # Leer resultado del traceroute
                    trace_output = []
                    while ser.in_waiting:
                        data = ser.read(ser.in_waiting).decode('ascii', errors='replace')
                        trace_output.append(data)
                    
                    # Mostrar traceroute
                    trace_text.config(state='normal')
                    trace_text.delete(1.0, tk.END)
                    trace_text.insert(tk.END, ''.join(trace_output))
                    trace_text.config(state='disabled')
                    
            except Exception as e:
                ping_text.config(state='normal')
                ping_text.insert(tk.END, f"Error: {str(e)}")
                ping_text.config(state='disabled')
                
                trace_text.config(state='normal')
                trace_text.insert(tk.END, f"Error: {str(e)}")
                trace_text.config(state='disabled')
        
        # Botón para ejecutar pruebas
        btn_frame = tk.Frame(ventana)
        btn_frame.pack(pady=5)
        
        btn_run = tk.Button(btn_frame, text="Ejecutar Pruebas", command=ejecutar_pruebas)
        btn_run.pack(side=tk.LEFT, padx=5)
        
        btn_close = tk.Button(btn_frame, text="Cerrar", command=ventana.destroy)
        btn_close.pack(side=tk.LEFT)
    
    def mostrar_documentacion(self):
        """Muestra documentación de comandos Cisco"""
        try:
            if os.path.exists(DOCS_FILE):
                webbrowser.open(f"file://{os.path.abspath(DOCS_FILE)}")
            else:
                webbrowser.open("https://www.cisco.com/c/en/us/support/docs/ip/routing-information-protocol-rip/13788-3.html")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la documentación:\n{str(e)}")
    
    def mostrar_acerca_de(self):
        """Muestra información acerca de la aplicación"""
        messagebox.showinfo(
            "Acerca de",
            "Configurador de Router Cisco Pro\n\n"
            "Versión 2.0\n\n"
            "Herramienta para configurar routers Cisco mediante interfaz serial\n"
            "Incluye terminal interactivo, monitorización y gestión de configuraciones"
        )
    
    def iniciar_envio_config(self):
        """Inicia el envío de configuración en un hilo separado"""
        if not self.puerto_var.get():
            messagebox.showerror("Error", "Selecciona un puerto COM.")
            return
            
        # Deshabilitar botones durante el envío
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.DISABLED)
        
        # Mostrar ventana de progreso
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Enviando configuración...")
        
        tk.Label(self.progress_window, text="Enviando comandos al router...").pack(pady=10)
        
        self.progress_var = tk.IntVar()
        progress_bar = ttk.Progressbar(
            self.progress_window,
            orient=tk.HORIZONTAL,
            length=300,
            mode='indeterminate',
            variable=self.progress_var
        )
        progress_bar.pack(pady=10, padx=20)
        progress_bar.start()
        
        # Iniciar hilo para el envío
        Thread(target=self.enviar_config, daemon=True).start()
    
    def enviar_config(self):
        """Envía la configuración al router (ejecutado en hilo separado)"""
        puerto = self.puerto_var.get()
        comandos = self.generar_comandos()
        
        if not comandos:
            if hasattr(self, 'progress_window'):
                self.progress_window.destroy()
            self.habilitar_botones()
            return
            
        try:
            with serial.Serial(puerto, BAUDRATE, timeout=TIMEOUT) as ser:
                time.sleep(2)  # Esperar inicialización
                
                total_comandos = len(comandos)
                for i, cmd in enumerate(comandos, 1):
                    ser.write((cmd + "\n").encode())
                    logging.info(f"Enviado: {cmd}")
                    
                    # Actualizar progreso
                    if hasattr(self, 'progress_window'):
                        self.progress_var.set((i/total_comandos)*100)
                        self.progress_window.update()
                    
                    time.sleep(DELAY_ENTRE_COMANDOS)
                    
                    # Leer respuesta (opcional)
                    if ser.in_waiting:
                        respuesta = ser.read(ser.in_waiting).decode().strip()
                        if respuesta:
                            logging.info(f"Respuesta: {respuesta}")
                
                messagebox.showinfo("Éxito", "Configuración enviada al router.")
                logging.info("Configuración enviada correctamente")
                self.update_status("Configuración enviada correctamente")
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo enviar configuración:\n{str(e)}")
            logging.error(f"Error al enviar configuración: {str(e)}")
            self.update_status("Error al enviar configuración")
        
        finally:
            if hasattr(self, 'progress_window'):
                self.progress_window.destroy()
            self.habilitar_botones()
    
    def habilitar_botones(self):
        """Habilita todos los botones de la interfaz"""
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = RouterConfigurator(root)
    root.mainloop()