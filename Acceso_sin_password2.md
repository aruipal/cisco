# Acceso a router cisco sin password. (Modelos sin botón Mode)
- En routers Cisco antiguos que no tienen botón "Mode", como los Cisco 2500, 2600 o 1700, el proceso de recuperación de contraseña cambia un poco, ya que no hay un botón físico para entrar en el modo ROMMON.
- En estos casos, el proceso implica interrumpir el arranque del router manualmente durante el inicio para entrar en el **modo de recuperación (ROMMON).**

###  Pasos para recuperación de contraseña en routers Cisco antiguos (sin botón Mode)
**1. Conectar al router**
- Conecta tu cable de consola (RS-232 o USB a consola) a tu computadora y al puerto de consola del router.
- Configura tu programa de terminal (como PuTTY o Tera Term) a una velocidad de 9600 baudios.

**2. Apagar el router**
- Desconecta el cable de alimentación del router.

**3. Reiniciar y entrar en modo de recuperación**
- Vuelve a conectar el cable de alimentación.
- En el momento exacto en que el router comienza a arrancar, presiona la tecla Ctrl + Break (en algunos teclados puede ser Ctrl + C o Ctrl + Pause dependiendo del emulador que uses).
- Mantén presionada la tecla **Ctrl + Break** durante 5-10 segundos hasta que el router entre en el modo ROMMON. Si lo haces correctamente, deberías ver un prompt que dice algo como:
```
rommon 1 >
```
- Este es el modo de recuperación ROMMON, que te permite realizar los siguientes pasos.

**4. Inicializar el sistema de archivos**
Una vez en el prompt rommon 1 >, necesitas inicializar el sistema de archivos para que puedas trabajar con los archivos almacenados en el router. Usa el siguiente comando:
```
flash_init
```
- Esto inicializa el sistema de archivos en el router.

**5. Renombrar el archivo de configuración**
Para evitar que el router cargue la configuración actual con la contraseña olvidada, renombra el archivo de configuración con el siguiente comando:
```
rename flash:config.text flash:config.text.old
```
- Este comando cambia el nombre del archivo de configuración actual para que no se cargue automáticamente al arrancar.

**6. Reiniciar el router**
- Ahora, reinicia el router con el siguiente comando para que cargue sin la configuración antigua:
```
boot
```
- El router arrancará sin la configuración guardada y te dará acceso al sistema sin pedir la contraseña.

### Acceso al router sin contraseña
- Una vez que el router haya arrancado, podrás acceder sin contraseña y cambiar la configuración:

**1. Accede al modo privilegiado**
- Escribe el siguiente comando para acceder al modo privilegiado:
```
enable
```
- No te pedirá contraseña porque la configuración de seguridad no está cargada.

**2. Recuperar la configuración original (opcional)**
- Si quieres restaurar la configuración original, renombra el archivo de configuración de nuevo:
```
rename flash:config.text.old flash:config.text
```
**3. Luego, carga la configuración:**
```
copy flash:config.text system:running-config
```
**4. Cambiar la contraseña**
- Ahora puedes cambiar las contraseñas y realizar configuraciones adicionales. Para cambiar la contraseña de acceso privilegiado, usa:
```
conf t
enable secret NuevaContraseña
```
**5. Guardar la configuración**
```
write memory
```
### 📅 Resultado esperado
- El router arrancará sin configuraciones previas, y podrás acceder a él sin que te pida contraseña.
- Podrás configurar el router nuevamente, incluyendo restablecer contraseñas o restaurar configuraciones anteriores.

