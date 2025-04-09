# Cisco project :snake:
Proyecto configurador cisco

### Para empaquetar tu aplicación de Python con Tkinter en un archivo .exe y poder ejecutarlo en Windows sin necesidad de tener Python instalado, puedes utilizar una herramienta como PyInstaller.
- **En Visual Studio Code:**<br>

**1. Instalar PyInstaller**<br>
Primero, necesitas instalar PyInstaller si no lo tienes. Puedes hacerlo usando pip en la terminal de Windows:
```
pip install pyinstaller
```
**2. Crear el archivo ejecutable**<br>
Una vez que tienes PyInstaller instalado, navega hasta el directorio donde está tu script (cisco.py) y ejecuta el siguiente comando en la terminal:
```
pyinstaller --onefile --windowed cisco.py
```
--onefile: Esto empaquetará todo en un solo archivo .exe.

--windowed: Esto evita que se abra una ventana de consola cuando ejecutas la aplicación (ideal para aplicaciones GUI como Tkinter).

**3. Buscar el archivo .exe**<br>
Después de ejecutar el comando, PyInstaller creará varias carpetas y archivos. El archivo .exe estará en la carpeta dist, en el directorio donde ejecutaste el comando. Por ejemplo:
```
/tu_directorio
    /dist
        cisco.exe
    /build
    cisco.spec
```
**4. Probar el .exe**<br>
Ve a la carpeta dist y busca el archivo cisco.exe. Haz doble clic en él para verificar que todo funciona como esperas.

