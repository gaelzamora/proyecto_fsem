# Manual Técnico - RetroBox Pi

Documentación técnica detallada del sistema de emulación RetroBox Pi.

## 1. Arquitectura del Sistema

### 1.1 Diagrama de Componentes

```
┌─────────────────────────────────────────┐
│         RetroLauncher (Main)            │
├─────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Video   │  │  Input   │  │  USB   ││
│  │ (OpenCV) │  │ (Pygame) │  │ Thread ││
│  └──────────┘  └──────────┘  └────────┘│
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │   Game   │  │   Icon   │  │ Notify ││
│  │  Loader  │  │ Manager  │  │ System ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
               │
               ▼
        ┌─────────────┐
        │  Mednafen   │
        │ (Emulator)  │
        └─────────────┘
```

### 1.2 Stack Tecnológico

| Componente | Tecnología | Versión | Función |
|------------|------------|---------|---------|
| Lenguaje | Python | 3.7+ | Core de aplicación |
| UI Framework | Pygame | 2.0+ | Renderizado gráfico |
| Video | OpenCV (cv2) | 4.5+ | Video de fondo |
| Emulador | Mednafen | 1.26+ | Ejecución de ROMs |
| Concurrencia | threading | stdlib | Detección USB |

## 2. Estructura del Código

### 2.1 Clase Principal: RetroLauncher

```python
class RetroLauncher:
    def __init__(self):
        # Inicialización de Pygame y pantalla completa
        # Carga de recursos (video, fuentes, iconos)
        # Escaneo de juegos
        # Inicio de hilo USB
```

**Variables de instancia principales:**
- `screen_width`, `screen_height`: Resolución detectada automáticamente
- `screen`: Superficie Pygame para renderizado
- `video_cap`: Capturador OpenCV para video de fondo
- `games`: Lista de juegos detectados
- `selected_index`: Índice del juego seleccionado
- `joystick`: Dispositivo de entrada detectado

### 2.2 Módulos y Funciones Clave

#### Sistema de Video (`load_video`, `update_video_frame`)

**Propósito:** Renderizar video de fondo en loop infinito

```python
def update_video_frame(self):
    ret, frame = self.video_cap.read()
    if not ret:
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reiniciar
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Convertir a superficie Pygame y escalar
```

#### Carga de Juegos (`load_games`)

**Propósito:** Escanear directorio de ROMs y crear lista

```python
def load_games(self):
    extensions = ['*.nes', '*.sfc', '*.smc', '*.gba', '*.gb', '*.gbc']
    for ext in extensions:
        for file_path in glob.glob(os.path.join(ROMS_PATH, ext)):
            # Extraer metadata y agregar a lista
```

**Estructura de datos:**
```python
{
    'name': 'Nombre sin extensión',
    'path': '/ruta/completa/archivo.nes',
    'ext': '.nes'
}
```

#### Detección USB (`usb_scanner_loop`)

**Propósito:** Hilo daemon que monitorea inserción de USB

**Algoritmo:**
```
1. Verificar cada 5 segundos si existe /dev/sda1
2. Si detectado y no procesado:
   a. Montar en /mnt/usb
   b. Escanear archivos ROM
   c. Copiar nuevos juegos a /home/pi/roms/
   d. Desmontar USB
   e. Recargar lista de juegos
   f. Mostrar notificación
3. Si USB removido, resetear flag
```

#### Lanzamiento de Juegos (`launch_game`)

**Propósito:** Ejecutar emulador y monitorear salida

```python
def launch_game(self, game_data):
    # 1. Mostrar pantalla de carga
    # 2. Ejecutar Mednafen como subprocess
    process = subprocess.Popen(['mednafen', '-video.fs', '1', 
                                 '-command.exit', '0', game_path])
    
    # 3. Loop de monitoreo
    while game_running:
        if process.poll() is not None:  # Proceso terminó
            game_running = False
        
        # Detectar combo SELECT+START para salir
        if joystick.get_button(BTN_SELECT) and joystick.get_button(BTN_START):
            process.terminate()
            game_running = False
    
    # 4. Restaurar UI de Pygame
```

## 3. Configuración del Sistema

### 3.1 Variables de Configuración

**Archivo:** `retro_launcher.py` (líneas 14-31)

```python
# Rutas del sistema
ROMS_PATH = "/home/pi/roms"
ICONS_PATH = "/home/pi/icons"
LOGO_PATH = "/home/pi/LogoConsola.png"
VIDEO_PATH = "/home/pi/FondoConsola.mp4"
FONT_PATH = "/home/pi/retro.ttf"

# Configuración USB
USB_DEVICE = "/dev/sda1"
USB_MOUNT_POINT = "/mnt/usb"

# Paleta de colores (RGB)
COLOR_WHITE = (255, 255, 255)
COLOR_YELLOW = (255, 215, 0)
COLOR_RED = (255, 50, 50)
COLOR_GREEN = (50, 255, 50)
```

### 3.2 Mapeo de Botones

```python
# Estándar Linux/Xbox (líneas 33-42)
BTN_A = 0
BTN_B = 1
BTN_X = 2
BTN_Y = 3
BTN_LB = 4
BTN_RB = 5
BTN_SELECT = 6
BTN_START = 7
BTN_XBOX = 8
```

**Para otros gamepads:** Usar `jstest /dev/input/js0` y ajustar valores

### 3.3 Resoluciones Soportadas

El sistema detecta automáticamente la resolución usando:

```python
display_info = pygame.display.Info()
self.screen_width = display_info.current_w
self.screen_height = display_info.current_h
```

**Resoluciones probadas:**
- 1920x1080 (Full HD)
- 1280x720 (HD)
- 1024x768 (XGA)

## 4. Flujo de Ejecución

### 4.1 Secuencia de Inicio

```
1. Importar librerías (pygame, cv2, subprocess, etc.)
2. __init__():
   a. pygame.init()
   b. Configurar pantalla completa
   c. Ocultar cursor
   d. Cargar video de fondo
   e. Cargar fuentes tipográficas
   f. Cargar iconos de consolas
   g. Escanear juegos
   h. Detectar joystick
   i. Iniciar hilo USB daemon
3. run():
   a. Loop principal a 30 FPS
   b. Actualizar frame de video
   c. Procesar eventos (input)
   d. Renderizar UI
   e. Mostrar notificaciones
```

### 4.2 Ciclo Principal (Main Loop)

```python
while running:
    # 1. Actualizar video de fondo
    self.update_video_frame()
    
    # 2. Leer input del joystick
    if joystick:
        axis_x = self.joystick.get_axis(0)
        # Navegar con joystick analógico
    
    # 3. Procesar eventos de Pygame
    for event in pygame.event.get():
        if event.type == pygame.JOYBUTTONDOWN:
            # Manejar botones
    
    # 4. Renderizar UI completa
    self.draw()
    
    # 5. Limitar a 30 FPS
    self.clock.tick(30)
```

## 5. Renderizado de UI

### 5.1 Sistema de Capas

```
Capa 1: Video de fondo (self.current_video_frame)
Capa 2: Barra semitransparente (área de selección)
Capa 3: Iconos de juegos (escala dinámica)
Capa 4: Texto con outline (nombres de juegos)
Capa 5: Cabecera (logo + título)
Capa 6: Notificaciones USB (esquina superior derecha)
Capa 7: Leyenda de controles (barra inferior)
```

### 5.2 Escalado Dinámico

Los tamaños se calculan relativos a la resolución:

```python
# Fuentes (load_fonts)
title_size = int(self.screen_height * 0.08)
big_size = int(self.screen_height * 0.07)
small_size = int(self.screen_height * 0.04)

# Iconos (load_icons)
base_w = int(self.screen_width * 0.25)
base_h = int(base_w * 0.75)

# Juego seleccionado
scale = 1.2  # 120%
# Juegos adyacentes
scale = 0.6  # 60%
```

### 5.3 Efecto de Outline en Texto

```python
def draw_text_with_outline(self, text, font, color, x, y, 
                           outline_color=(0,0,0), thickness=3):
    # Renderizar outline en 4 direcciones
    for dx, dy in [(-thickness,0), (thickness,0), (0,-thickness), (0,thickness)]:
        self.screen.blit(outline_surf, (x+dx, y+dy))
    # Renderizar texto principal
    self.screen.blit(text_surf, (x, y))
```

## 6. Gestión de Procesos

### 6.1 Subprocess para Mednafen

```python
launch_cmd = [
    'mednafen',
    '-video.fs', '1',           # Pantalla completa
    '-command.exit', '0',       # No mostrar mensaje salida
    game_path
]

process = subprocess.Popen(launch_cmd)
```

### 6.2 Monitoreo y Terminación

```python
while game_running:
    # Verificar si el proceso terminó naturalmente
    if process.poll() is not None:
        game_running = False
    
    # Detectar combo de salida forzada
    if SELECT and START pressed:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()  # Forzar si no responde
```

### 6.3 Restauración de Estado

Después de cerrar el emulador:

```python
# Recrear ventana de Pygame
self.screen = pygame.display.set_mode(
    (self.screen_width, self.screen_height),
    pygame.FULLSCREEN | pygame.DOUBLEBUF
)

# Reinicializar joystick
pygame.joystick.quit()
pygame.joystick.init()
if pygame.joystick.get_count() > 0:
    self.joystick = pygame.joystick.Joystick(0)
    self.joystick.init()
```

## 7. Optimización de Rendimiento

### 7.1 Control de FPS

```python
# Raspberry Pi 3
self.clock.tick(24)  # 24 FPS

# Raspberry Pi 4/5
self.clock.tick(30)  # 30 FPS
```

### 7.2 Reducción de Carga de Video

Si hay lag, reducir resolución del video:

```python
def update_video_frame(self):
    ret, frame = self.video_cap.read()
    if ret:
        frame = cv2.resize(frame, (1280, 720))  # Escalar antes
        # Continuar procesamiento...
```

### 7.3 Desactivar Video (solo fondo estático)

```python
# Comentar en __init__
# self.load_video()

# En draw(), usar color sólido
self.screen.fill((20, 20, 40))
```

## 8. Debugging

### 8.1 Logs de Sistema

```bash
# Ejecutar con output de errores
python3 /home/pi/retro_launcher.py 2>&1 | tee debug.log
```

### 8.2 Verificación de Recursos

```bash
# Verificar archivos existen
ls -lh /home/pi/*.{py,mp4,png,ttf}

# Verificar ROMs
ls -lh /home/pi/roms/

# Verificar iconos
ls -lh /home/pi/icons/
```

### 8.3 Test de Gamepad

```bash
# Instalar herramientas
sudo apt install joystick

# Listar dispositivos
ls -la /dev/input/js*

# Probar gamepad
jstest /dev/input/js0
```

## 9. Extensibilidad

### 9.1 Agregar Nuevas Consolas

1. **Agregar extensión a las listas:**
```python
extensions = ['nes', 'sfc', 'smc', 'gba', 'gb', 'gbc', 'md']  # Sega Genesis
```

2. **Crear icono:**
```bash
# Icono debe ser PNG, nombrado como extensión
cp md.png /home/pi/icons/
```

3. **Verificar soporte en Mednafen:**
```bash
mednafen --help | grep -i genesis
```

### 9.2 Cambiar Emulador

Para usar RetroArch en lugar de Mednafen:

```python
def launch_game(self, game_data):
    core_map = {
        '.nes': '/usr/lib/libretro/nestopia_libretro.so',
        '.sfc': '/usr/lib/libretro/snes9x_libretro.so',
    }
    
    core = core_map.get(game_data['ext'])
    launch_cmd = ['retroarch', '-L', core, '-f', game_data['path']]
    process = subprocess.Popen(launch_cmd)
```

## 10. Seguridad

### 10.1 Permisos Sudo

El archivo `/etc/sudoers` permite operaciones específicas sin contraseña:

```
pi ALL=(ALL) NOPASSWD: /bin/mount, /bin/umount, /sbin/poweroff
```

**Importante:** Solo permite estos comandos, no acceso root completo.

### 10.2 Montaje USB

El sistema monta USB como solo lectura implícitamente al copiar archivos.

```python
subprocess.run(["sudo", "mount", USB_DEVICE, USB_MOUNT_POINT], check=False)
# Solo lectura de archivos, no escritura en USB
```

## 11. Requisitos de Hardware

### 11.1 Especificaciones Mínimas

- **CPU:** ARM Cortex-A53 (Raspberry Pi 3) @ 1.2 GHz
- **RAM:** 1GB (funcional), 2GB+ (recomendado)
- **GPU:** VideoCore IV
- **Almacenamiento:** 100MB app + ROMs
- **USB:** Puerto USB 2.0/3.0 para gamepad y USB

### 11.2 Especificaciones Recomendadas

- **CPU:** ARM Cortex-A72 (Raspberry Pi 4) @ 1.5 GHz
- **RAM:** 4GB
- **GPU:** VideoCore VI
- **Almacenamiento:** 32GB microSD Clase 10

## 12. Formato de Archivos

### 12.1 ROMs Soportadas

| Extensión | Consola | Tamaño típico |
|-----------|---------|---------------|
| `.nes` | Nintendo NES | 40KB - 512KB |
| `.sfc`, `.smc` | Super Nintendo | 512KB - 6MB |
| `.gb` | Game Boy | 32KB - 1MB |
| `.gbc` | Game Boy Color | 128KB - 8MB |
| `.gba` | Game Boy Advance | 4MB - 32MB |

### 12.2 Recursos Multimedia

- **Video:** MP4 (H.264), max 1080p
- **Imágenes:** PNG (transparencia soportada)
- **Fuentes:** TTF (TrueType)

## 13. Mantenimiento

### 13.1 Actualizar Sistema

```bash
# Actualizar dependencias
sudo apt update && sudo apt upgrade -y

# Actualizar Python packages
pip3 install --upgrade pygame opencv-python
```

### 13.2 Limpiar ROMs Duplicadas

```bash
# Listar duplicados
fdupes -r /home/pi/roms/

# Eliminar duplicados (cuidado)
fdupes -rdN /home/pi/roms/
```

### 13.3 Backup

```bash
# Backup de ROMs
tar -czvf roms_backup.tar.gz /home/pi/roms/

# Backup completo del proyecto
tar -czvf retrobox_backup.tar.gz /home/pi/*.py /home/pi/*.mp4 /home/pi/*.png /home/pi/roms/ /home/pi/icons/
```

---

**Documento técnico - RetroBox Pi v1.0**  
**Autores:** Hernández Zamora José Gael, Lara Acevedo Cristian Alexis, Sanchez Alvirde Andrés Iván
