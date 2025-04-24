# Acceso a router cisco sin password. (Modelos con botón Mode)

### :point_right:	:accessibility:	[Para modelos sin botón Mode.](https://github.com/aruipal/cisco/blob/main/Acceso_sin_password2.md)
___

- Método común para recuperar el acceso a un router Cisco, especialmente cuando se ha olvidado la contraseña. 
- Se le llama a veces "nuking" porque borra toda la configuración del dispositivo.

🔧 **¿Qué es esto?**
- Es un procedimiento para recuperar el acceso a un router Cisco cuando se ha perdido la contraseña.
- Para hacerlo, se interrumpe el proceso de arranque (boot) y se borra la configuración almacenada (incluyendo contraseñas).

⚠️ **Advertencia Importante**
- ¡Se borrará toda la configuración actual del dispositivo!
- Si no tienes un respaldo (backup), perderás toda la configuración previa.
- Necesitas tener acceso por consola (cable de consola) y usar una terminal (como PuTTY o Tera Term) a 9600 baudios.

## ✅ Pasos del Proceso
**1. Prepara el cable de consola**
- Conecta tu PC al switch usando un cable de consola.
- Asegúrate de usar un programa de terminal con la configuración de 9600 baudios.

**2. Apaga el router**
- Desconecta el cable de alimentación del router.

**3. Accede al modo de recuperación**
- Enciende el router y mantén presionado el botón "Mode" en el router. Este botón se encuentra en la parte frontal de los modelos de routers Cisco, en la parte inferior.
- Mantén presionado el botón "Mode" durante 10-15 segundos hasta que el LED de "SYS" (sistema) cambie de color. Esto indica que el router está en modo de recuperación.

**5. El router entra en modo ROMMON**
- Una vez que el LED cambie y el router arranque, aparecerá una línea de comandos en tu terminal que te llevará al modo ROMMON (modo de recuperación).

**6. Inicializa el sistema de archivos**
En la consola, escribe el siguiente comando para inicializar el sistema de archivos en el router:
```
flash_init
```
**8. Cargar la ayuda del sistema (opcional)**
- Aunque no siempre es necesario, puedes cargar los archivos de ayuda con:
```
load_helper
```
**9. Renombrar el archivo de configuración actual**
El siguiente paso es renombrar el archivo de configuración existente para evitar que se cargue la configuración con la contraseña olvidada. Usa este comando:
```
rename flash:config.text flash:config.text.old
```
**10. Reiniciar el router**
Una vez renombrado el archivo de configuración, reinicia el router con el siguiente comando:
```
boot
```
**El router arrancará sin la configuración anterior.**

### 🟢 Acceso al router sin contraseña:
- Cuando el router haya arrancado, accederás al sistema sin que te pida la contraseña. Ahora podrás cambiar o eliminar las contraseñas:
**1. Accede al modo privilegiado**
En el prompt, escribe:
```
enable
```
**2. Recupera la configuración original**
- Si deseas restaurar la configuración original, renombra el archivo de configuración que guardaste antes con el siguiente comando:
```
rename flash:config.text.old flash:config.text
```
**3. Y luego recarga la configuración:**
```
copy flash:config.text system:running-config
```
**4. Cambia la contraseña**
- Una vez que hayas cargado la configuración, puedes cambiar la contraseña:
```
conf t
enable secret NuevaContraseña
```
**5. Guarda la configuración**
- Finalmente, guarda los cambios:
```
write memory
```
### 📅 Resultado esperado
- El router arranca sin pedirte contraseña.
- Tendrás acceso completo para configurarlo de nuevo o restaurar la configuración.
