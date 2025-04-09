import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import time

# Función para listar puertos seriales
def listar_puertos():
    puertos = serial.tools.list_ports.comports()
    return [p.device for p in puertos]

# Generación de comandos según configuraciones
def generar_comandos():
    comandos = ["enable", "configure terminal"]

    # === Configuración básica ===
    hostname = hostname_entry.get()
    pass_consola = consola_pass.get()
    pass_enable = enable_pass.get()
    banner = banner_msg.get()
    interfaz_lan = lan_interface.get()
    ip_lan = lan_ip.get()
    mask_lan = lan_mask.get()

    if hostname:
        comandos.append(f"hostname {hostname}")
    if pass_enable:
        comandos.append(f"enable secret {pass_enable}")
    if pass_consola:
        comandos.append("line console 0")
        comandos.append(f"password {pass_consola}")
        comandos.append("login")
        comandos.append("exit")
    if banner:
        comandos.append(f"banner motd #{banner}#")

    if interfaz_lan and ip_lan and mask_lan:
        comandos.append(f"interface {interfaz_lan}")
        comandos.append(f"ip address {ip_lan} {mask_lan}")
        comandos.append("no shutdown")
        comandos.append("exit")
    
    # === Configuración de puerto Serial ===
    serial_puerto = serial_interface.get()
    ip_serial = serial_ip.get()
    mask_serial = serial_mask.get()
    clock_rate = serial_clock_rate.get()
    activar_serial = serial_shutdown_var.get()

    if serial_puerto and ip_serial and mask_serial:
        comandos.append(f"interface {serial_puerto}")
        comandos.append(f"ip address {ip_serial} {mask_serial}")
        if clock_rate:
            comandos.append(f"clock rate {clock_rate}")
        if activar_serial:
            comandos.append("no shutdown")
        comandos.append("exit")
    
    # === SSH ===
    dominio = ssh_dominio.get()
    usuario = ssh_usuario.get()
    clave = ssh_clave.get()

    if dominio and usuario and clave:
        comandos.append(f"ip domain-name {dominio}")
        comandos.append(f"username {usuario} password {clave}")
        comandos.append("crypto key generate rsa")
        comandos.append("1024")
        comandos += [
            "line vty 0 4",
            "transport input ssh",
            "login local",
            "exit"
        ]

    # === Borrar configuración de interfaz ===
    interfaz_borrar = interfaz_borrar_entry.get()
    if interfaz_borrar:
        comandos.append(f"interface {interfaz_borrar}")
        comandos.append("shutdown")
        comandos.append("no ip address")
        comandos.append("no clock rate")
        comandos.append("exit")

    # === DHCP ===
    pool = dhcp_pool.get()
    red = dhcp_red.get()
    mascara = dhcp_mascara.get()
    gateway = dhcp_gateway.get()
    ini = dhcp_rango_ini.get()
    fin = dhcp_rango_fin.get()

    if pool and red and mascara and gateway:
        if ini and fin:
            comandos.append(f"ip dhcp excluded-address {ini} {fin}")
        comandos.append(f"ip dhcp pool {pool}")
        comandos.append(f" network {red} {mascara}")
        comandos.append(f" default-router {gateway}")
    
    # === Enrutamiento dinámico ===
    proto = protocolo_var.get()
    red = ruteo_red.get()
    wc = ruteo_wc.get()
    area = ruteo_area.get()
    asn = ruteo_as.get()

    if proto == "rip" and red:
        comandos.append("router rip")
        comandos.append("version 2")
        comandos.append(f"network {red}")
        comandos.append("exit")

    elif proto == "ospf" and red and wc and area:
        comandos.append("router ospf 1")
        comandos.append(f"network {red} {wc} area {area}")
        comandos.append("exit")

    elif proto == "eigrp" and red and asn:
        comandos.append(f"router eigrp {asn}")
        comandos.append(f"network {red}")
        comandos.append("exit")

    comandos += ["exit", "write memory"]
    return comandos

# Función para vista previa de la configuración
def vista_previa():
    comandos = generar_comandos()
    ventana = tk.Toplevel(root)
    ventana.title("Vista previa de configuración")
    text_area = tk.Text(ventana, height=25, width=60)
    text_area.pack(padx=10, pady=10)
    text_area.insert(tk.END, "\n".join(comandos))
    text_area.config(state="disabled")

# Función para guardar la configuración como archivo .txt
def guardar_como_txt():
    comandos = generar_comandos()
    archivo = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivo de texto", "*.txt")])
    if archivo:
        with open(archivo, "w") as f:
            f.write("\n".join(comandos))
        messagebox.showinfo("Guardado", f"Configuración guardada en:\n{archivo}")

# Función para enviar la configuración al router
def enviar_config():
    puerto = puerto_var.get()
    comandos = generar_comandos()

    if not puerto:
        messagebox.showerror("Error", "Selecciona un puerto COM.")
        return

    try:
        ser = serial.Serial(puerto, 9600, timeout=1)
        time.sleep(2)
        for cmd in comandos:
            ser.write((cmd + "\n").encode())
            time.sleep(0.3)
        ser.close()
        messagebox.showinfo("Éxito", "Configuración enviada al router.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo enviar configuración:\n{e}")

# === GUI ===
root = tk.Tk()
root.title("Configurador de Router Cisco")

# Selección de puerto serial
frame_top = tk.Frame(root)
frame_top.pack(pady=10)

tk.Label(frame_top, text="Puerto COM:").pack(side=tk.LEFT)
puerto_var = tk.StringVar()
puerto_combo = ttk.Combobox(frame_top, textvariable=puerto_var, values=listar_puertos(), width=15)
puerto_combo.pack(side=tk.LEFT, padx=5)

# Cuaderno de pestañas
tabs = ttk.Notebook(root)
tabs.pack(padx=10, pady=10)

# === Pestaña Configuración Básica ===
basico_tab = ttk.Frame(tabs)
tabs.add(basico_tab, text="Básico")

tk.Label(basico_tab, text="Hostname:").grid(row=0, column=0, sticky="e")
hostname_entry = tk.Entry(basico_tab)
hostname_entry.grid(row=0, column=1)

tk.Label(basico_tab, text="Contraseña de consola:").grid(row=1, column=0, sticky="e")
consola_pass = tk.Entry(basico_tab, show="*")
consola_pass.grid(row=1, column=1)

tk.Label(basico_tab, text="Contraseña enable:").grid(row=2, column=0, sticky="e")
enable_pass = tk.Entry(basico_tab, show="*")
enable_pass.grid(row=2, column=1)

tk.Label(basico_tab, text="Mensaje de banner:").grid(row=3, column=0, sticky="e")
banner_msg = tk.Entry(basico_tab)
banner_msg.grid(row=3, column=1)

# Interfaz LAN
tk.Label(basico_tab, text="Interfaz LAN (ej: FastEthernet0/0):").grid(row=4, column=0, sticky="e")
lan_interface = tk.Entry(basico_tab)
lan_interface.grid(row=4, column=1)

tk.Label(basico_tab, text="IP LAN:").grid(row=5, column=0, sticky="e")
lan_ip = tk.Entry(basico_tab)
lan_ip.grid(row=5, column=1)

tk.Label(basico_tab, text="Máscara LAN:").grid(row=6, column=0, sticky="e")
lan_mask = tk.Entry(basico_tab)
lan_mask.grid(row=6, column=1)

tk.Label(basico_tab, text="Interfaz a borrar (ej: FastEthernet0/0):").grid(row=7, column=0, sticky="e")
interfaz_borrar_entry = tk.Entry(basico_tab)
interfaz_borrar_entry.grid(row=7, column=1)

# === Pestaña Configuración de Puertos Serial ===

serial_tab = ttk.Frame(tabs)
tabs.add(serial_tab, text="Serial")

tk.Label(serial_tab, text="Puerto Serial (ej: Serial0/0):").grid(row=0, column=0, sticky="e")
serial_interface = tk.Entry(serial_tab)
serial_interface.grid(row=0, column=1)

tk.Label(serial_tab, text="IP Puerto Serial:").grid(row=1, column=0, sticky="e")
serial_ip = tk.Entry(serial_tab)
serial_ip.grid(row=1, column=1)

tk.Label(serial_tab, text="Máscara Puerto Serial:").grid(row=2, column=0, sticky="e")
serial_mask = tk.Entry(serial_tab)
serial_mask.grid(row=2, column=1)

tk.Label(serial_tab, text="Clock rate (si aplica):").grid(row=3, column=0, sticky="e")
serial_clock_rate = tk.Entry(serial_tab)
serial_clock_rate.grid(row=3, column=1)

tk.Label(serial_tab, text="Activar puerto (no shutdown):").grid(row=4, column=0, sticky="e")
serial_shutdown_var = tk.BooleanVar()
serial_shutdown = tk.Checkbutton(serial_tab, variable=serial_shutdown_var)
serial_shutdown.grid(row=4, column=1)

# === Pestaña SSH ===
ssh_tab = ttk.Frame(tabs)
tabs.add(ssh_tab, text="SSH")

tk.Label(ssh_tab, text="Dominio:").grid(row=0, column=0, sticky="e")
ssh_dominio = tk.Entry(ssh_tab)
ssh_dominio.grid(row=0, column=1)

tk.Label(ssh_tab, text="Nombre de usuario:").grid(row=1, column=0, sticky="e")
ssh_usuario = tk.Entry(ssh_tab)
ssh_usuario.grid(row=1, column=1)

tk.Label(ssh_tab, text="Contraseña de usuario:").grid(row=2, column=0, sticky="e")
ssh_clave = tk.Entry(ssh_tab, show="*")
ssh_clave.grid(row=2, column=1)

# === Pestaña DHCP ===
dhcp_tab = ttk.Frame(tabs)
tabs.add(dhcp_tab, text="DHCP")

tk.Label(dhcp_tab, text="Nombre del pool:").grid(row=0, column=0, sticky="e")
dhcp_pool = tk.Entry(dhcp_tab)
dhcp_pool.grid(row=0, column=1)

tk.Label(dhcp_tab, text="Red:").grid(row=1, column=0, sticky="e")
dhcp_red = tk.Entry(dhcp_tab)
dhcp_red.grid(row=1, column=1)

tk.Label(dhcp_tab, text="Máscara:").grid(row=2, column=0, sticky="e")
dhcp_mascara = tk.Entry(dhcp_tab)
dhcp_mascara.grid(row=2, column=1)

tk.Label(dhcp_tab, text="Gateway:").grid(row=3, column=0, sticky="e")
dhcp_gateway = tk.Entry(dhcp_tab)
dhcp_gateway.grid(row=3, column=1)

tk.Label(dhcp_tab, text="Rango inicial:").grid(row=4, column=0, sticky="e")
dhcp_rango_ini = tk.Entry(dhcp_tab)
dhcp_rango_ini.grid(row=4, column=1)

tk.Label(dhcp_tab, text="Rango final:").grid(row=5, column=0, sticky="e")
dhcp_rango_fin = tk.Entry(dhcp_tab)
dhcp_rango_fin.grid(row=5, column=1)

# === Pestaña Enrutamiento ===
ruteo_tab = ttk.Frame(tabs)
tabs.add(ruteo_tab, text="Enrutamiento")

tk.Label(ruteo_tab, text="Protocolo:").grid(row=0, column=0, sticky="e")
protocolo_var = tk.StringVar()
protocolo_combo = ttk.Combobox(ruteo_tab, textvariable=protocolo_var, values=["rip", "ospf", "eigrp"], state="readonly")
protocolo_combo.grid(row=0, column=1)

tk.Label(ruteo_tab, text="Red:").grid(row=1, column=0, sticky="e")
ruteo_red = tk.Entry(ruteo_tab)
ruteo_red.grid(row=1, column=1)

tk.Label(ruteo_tab, text="Wildcard:").grid(row=2, column=0, sticky="e")
ruteo_wc = tk.Entry(ruteo_tab)
ruteo_wc.grid(row=2, column=1)

tk.Label(ruteo_tab, text="Área OSPF:").grid(row=3, column=0, sticky="e")
ruteo_area = tk.Entry(ruteo_tab)
ruteo_area.grid(row=3, column=1)

tk.Label(ruteo_tab, text="ASN EIGRP:").grid(row=4, column=0, sticky="e")
ruteo_as = tk.Entry(ruteo_tab)
ruteo_as.grid(row=4, column=1)

# === Botones ===
frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=10)

boton_vista = tk.Button(frame_bottom, text="Vista previa", command=vista_previa)
boton_vista.pack(side=tk.LEFT, padx=10)

boton_guardar = tk.Button(frame_bottom, text="Guardar configuración", command=guardar_como_txt)
boton_guardar.pack(side=tk.LEFT, padx=10)

boton_enviar = tk.Button(frame_bottom, text="Enviar configuración", command=enviar_config)
boton_enviar.pack(side=tk.LEFT, padx=10)

root.mainloop()
