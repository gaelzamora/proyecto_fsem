# Tutorial de Instalación - RetroBox Pi

Guía paso a paso para instalar y configurar RetroBox Pi en Raspberry Pi.

## 1. Preparación del Hardware

### Materiales Necesarios
- Raspberry Pi 3/4/5
- Tarjeta microSD 16GB-32GB (Clase 10)
- Fuente de alimentación oficial
- Cable HDMI
- Gamepad USB
- Teclado USB (solo para configuración inicial)

### Conexiones
1. Insertar microSD en la Raspberry Pi
2. Conectar HDMI al monitor
3. Conectar gamepad y teclado USB
4. Conectar alimentación (enciende automáticamente)

## 2. Instalar Raspberry Pi OS

### En tu computadora:
1. Descargar **Raspberry Pi Imager**: https://www.raspberrypi.com/software/
2. Ejecutar Imager y seleccionar:
   - **OS**: Raspberry Pi OS (64-bit) Desktop
   - **Storage**: Tu microSD
3. Configurar (⚙️):
   - Usuario: `pi` / Contraseña: `raspberry`
   - Habilitar SSH (opcional)
   - Configurar WiFi si es necesario
4. Click en **WRITE** y esperar

### Primera vez en Raspberry Pi:
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y
```

## 3. Instalar Dependencias

```bash
# Paquetes del sistema
sudo apt install -y python3-pygame python3-opencv mednafen python3-pip git

# Verificar instalación
python3 --version
mednafen --help
```

## 4. Configurar Directorios

```bash
# Crear estructura
mkdir -p /home/pi/roms
mkdir -p /home/pi/icons
sudo mkdir -p /mnt/usb

# Verificar
ls -la /home/pi/
```

## 5. Configurar Permisos

### Permisos de usuario:
```bash
sudo usermod -aG plugdev pi
sudo usermod -aG input pi
```

### Permisos sudo para USB y apagado:
```bash
sudo visudo
```

**Agregar al final:**
```
pi ALL=(ALL) NOPASSWD: /bin/mount, /bin/umount, /sbin/poweroff
```

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

## 6. Copiar Archivos del Proyecto

### Opción A: Desde USB
```bash
# Montar USB
sudo mount /dev/sda1 /mnt/usb

# Copiar archivos
cp /mnt/usb/Proyecto_FSE/retro_launcher.py /home/pi/
cp /mnt/usb/Proyecto_FSE/*.png /home/pi/icons/
cp /mnt/usb/Proyecto_FSE/LogoConsola.png /home/pi/
cp /mnt/usb/Proyecto_FSE/FondoConsola.mp4 /home/pi/
cp /mnt/usb/Proyecto_FSE/retro.ttf /home/pi/

# Desmontar
sudo umount /mnt/usb
```

### Opción B: Desde Git (si tienes repositorio)
```bash
cd /home/pi
git clone [URL_DEL_REPOSITORIO]
cp Proyecto_FSE/src/* /home/pi/
cp Proyecto_FSE/src/*.png /home/pi/icons/
```

## 7. Verificar Instalación

```bash
# Verificar archivos
ls -lh /home/pi/ | grep -E 'retro|Logo|Fondo'
ls -lh /home/pi/icons/

# Debería mostrar:
# retro_launcher.py
# LogoConsola.png
# FondoConsola.mp4
# retro.ttf
# icons/*.png
```

## 8. Configurar Gamepad

### Verificar detección:
```bash
ls /dev/input/js*
# Debería mostrar: /dev/input/js0
```

### Probar gamepad:
```bash
sudo apt install joystick
jstest /dev/input/js0
```

Presiona botones para verificar que responde.

## 9. Primera Ejecución

```bash
cd /home/pi
python3 retro_launcher.py
```

**Controles:**
- `Joystick/Cruceta`: Navegar
- `A`: Seleccionar
- `ESC`: Salir (solo teclado, primera vez)

## 10. Agregar ROMs

### Método 1: USB automático
1. Copiar ROMs a una USB (formatos: `.nes`, `.sfc`, `.smc`, `.gb`, `.gbc`, `.gba`)
2. Insertar USB en la Raspberry Pi
3. Esperar notificación en pantalla
4. Juegos aparecen automáticamente

### Método 2: Manual
```bash
# Copiar ROMs directamente
cp /ruta/a/tus/roms/*.nes /home/pi/roms/
cp /ruta/a/tus/roms/*.sfc /home/pi/roms/
```

## 11. Inicio Automático (Opcional)

Para que RetroBox Pi inicie al encender:

```bash
nano ~/.bashrc
```

**Agregar al final:**
```bash
# Auto-inicio RetroBox Pi
if [ -z "$SSH_CLIENT" ]; then
    python3 /home/pi/retro_launcher.py
fi
```

Guardar y reiniciar:
```bash
sudo reboot
```

## 12. Solución de Problemas

### Video no se reproduce
```bash
sudo apt install libavcodec-extra ffmpeg
```

### Gamepad no responde
```bash
# Verificar permisos
sudo usermod -aG input pi
# Reiniciar
sudo reboot
```

### USB no se detecta
```bash
# Verificar dispositivo
lsblk
# Si no es /dev/sda1, editar en retro_launcher.py línea 21
```

### Error de permisos
```bash
# Revisar sudoers
sudo visudo
# Verificar línea: pi ALL=(ALL) NOPASSWD: /bin/mount, /bin/umount, /sbin/poweroff
```

### Pantalla negra al ejecutar
```bash
# Verificar archivos multimedia
ls -lh /home/pi/FondoConsola.mp4
ls -lh /home/pi/LogoConsola.png
```

## 13. Comandos Útiles

```bash
# Ver logs de errores
python3 /home/pi/retro_launcher.py 2>&1 | tee error.log

# Listar ROMs instaladas
ls -lh /home/pi/roms/

# Verificar espacio disponible
df -h

# Temperatura de la Raspberry Pi
vcgencmd measure_temp

# Reiniciar desde terminal
sudo reboot

# Apagar desde terminal
sudo poweroff
```

## Resumen de Rutas Importantes

| Componente | Ruta |
|------------|------|
| Código principal | `/home/pi/retro_launcher.py` |
| ROMs | `/home/pi/roms/` |
| Iconos | `/home/pi/icons/` |
| Logo | `/home/pi/LogoConsola.png` |
| Video | `/home/pi/FondoConsola.mp4` |
| Fuente | `/home/pi/retro.ttf` |
| Montaje USB | `/mnt/usb` |

---

**¡Instalación completada!** Disfruta de RetroBox Pi 🎮
