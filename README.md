# Proyecto Fundamentos de Sistemas Embebidos

# AUTORES

Hernández Zamora José Gael - 422526108
Lara Acevedo Cristian Alexis - 318204538
Sanchez Alvirde Andrés Iván - 318247225

# RetroBox Pi

Sistema de emulación retro para Raspberry Pi con interfaz gráfica y control por gamepad.

## Descripción

Launcher de videojuegos retro con interfaz visual tipo carrusel, detección automática de ROMs via USB y control completo por gamepad. Soporta NES, SNES, Game Boy, Game Boy Color y Game Boy Advance.

## Características

- Interfaz gráfica con navegación tipo carrusel
- Soporte multi-consola (NES, SNES, GB, GBC, GBA)
- Carga automática de ROMs desde USB
- Video de fondo animado
- Control 100% por gamepad
- Notificaciones visuales
- Apagado seguro del sistema

## Requisitos

**Hardware:**
- Raspberry Pi 3/4/5
- Tarjeta microSD 16GB+ 
- Gamepad USB
- Monitor HDMI

**Software:**
- Raspberry Pi OS
- Python 3.7+
- Pygame, OpenCV, Mednafen

## Instalación

```bash
# Instalar dependencias
sudo apt update && sudo apt install -y python3-pygame python3-opencv mednafen

# Crear directorios
mkdir -p /home/pi/roms /home/pi/icons
sudo mkdir -p /mnt/usb

# Configurar permisos sudo
sudo visudo
# Agregar: pi ALL=(ALL) NOPASSWD: /bin/mount, /bin/umount, /sbin/poweroff

# Copiar archivos del proyecto
cp retro_launcher.py LogoConsola.png FondoConsola.mp4 retro.ttf /home/pi/
cp *.png /home/pi/icons/

# Ejecutar
python3 /home/pi/retro_launcher.py
```*