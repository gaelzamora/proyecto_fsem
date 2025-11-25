import os
# Configura variable de entorno para suprimir mensaje de inicio de Pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

import pygame
import subprocess
import glob
import cv2
import shutil
import threading
import time

# Configuración de rutas y archivos
ROMS_PATH = "/home/pi/roms"
ICONS_PATH = "/home/pi/icons"
LOGO_PATH = "/home/pi/LogoConsola.png"
VIDEO_PATH = "/home/pi/FondoConsola.mp4" 
FONT_PATH = "/home/pi/retro.ttf"

# Configuración de montaje USB
USB_DEVICE = "/dev/sda1"
USB_MOUNT_POINT = "/mnt/usb"

# Paleta de colores
COLOR_WHITE = (255, 255, 255)
COLOR_YELLOW = (255, 215, 0)      
COLOR_RED = (255, 50, 50)         
COLOR_GREEN = (50, 255, 50)       
COLOR_LINE = (200, 200, 255)      
COLOR_SHADOW = (0, 0, 0)
COLOR_BLACK_BG = (0, 0, 0, 180)

# Mapeo de botones (Estándar Linux/Xbox)
BTN_A = 0
BTN_B = 1
BTN_X = 2
BTN_Y = 3
BTN_LB = 4
BTN_RB = 5
BTN_SELECT = 6
BTN_START = 7
BTN_XBOX = 8

class RetroLauncher:
    def __init__(self):
        pygame.init()
        
        # Configuración de pantalla completa dinámica
        display_info = pygame.display.Info()
        self.screen_width = display_info.current_w
        self.screen_height = display_info.current_h
        
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), 
            pygame.FULLSCREEN | pygame.DOUBLEBUF
        )
        
        # Ocultar cursor y capturar eventos exclusivos
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        
        pygame.display.set_caption("RetroBox Pi")
        self.clock = pygame.time.Clock()
        
        # Inicialización de componentes
        self.video_cap = None
        self.load_video()
        self.load_fonts()
        
        self.icons = self.load_icons()
        self.games = self.load_games()
        self.logo_img = self.load_logo()
        self.selected_index = 0
        
        # Inicialización de Joystick
        pygame.joystick.init()
        self.joystick = None
        self.input_timer = 0
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        # Variables para gestión de notificaciones USB
        self.show_notification = False
        self.notification_timer = 0
        self.notification_lines = []
        
        # Verificación de punto de montaje
        if not os.path.exists(USB_MOUNT_POINT):
            try: os.makedirs(USB_MOUNT_POINT)
            except: pass

        # Hilo demonio para monitoreo de USB en segundo plano
        self.usb_thread = threading.Thread(target=self.usb_scanner_loop, daemon=True)
        self.usb_thread.start()

    def load_fonts(self):
        """Carga fuentes y calcula tamaños relativos a la resolución."""
        title_size = int(self.screen_height * 0.08)
        big_size = int(self.screen_height * 0.07)
        small_size = int(self.screen_height * 0.04)
        tiny_size = int(self.screen_height * 0.025)
        
        # Tamaño reducido para la leyenda inferior (1.8% de la altura para evitar desbordes)
        legend_size = int(self.screen_height * 0.018) 

        if os.path.exists(FONT_PATH):
            try:
                self.font_title = pygame.font.Font(FONT_PATH, title_size)
                self.font_game_big = pygame.font.Font(FONT_PATH, big_size)
                self.font_game_small = pygame.font.Font(FONT_PATH, small_size)
                self.font_notify = pygame.font.Font(FONT_PATH, tiny_size)
                self.font_legend = pygame.font.Font(FONT_PATH, legend_size)
                return
            except:
                print("Fallo al cargar fuente personalizada.")

        # Fuentes por defecto en caso de error
        self.font_title = pygame.font.Font(None, title_size)
        self.font_game_big = pygame.font.Font(None, int(self.screen_height * 0.1))
        self.font_game_small = pygame.font.Font(None, int(self.screen_height * 0.05))
        self.font_notify = pygame.font.Font(None, 24) 
        self.font_legend = pygame.font.Font(None, 18)

    def load_video(self):
        if os.path.exists(VIDEO_PATH):
            self.video_cap = cv2.VideoCapture(VIDEO_PATH)

    def load_logo(self):
        if os.path.exists(LOGO_PATH):
            try:
                img = pygame.image.load(LOGO_PATH)
                h = int(self.screen_height * 0.08)
                w = int(img.get_width() * (h / img.get_height()))
                return pygame.transform.scale(img, (w, h))
            except:
                return None
        return None

    def load_icons(self):
        icon_map = {}
        extensions = ['nes', 'sfc', 'smc', 'gba', 'gb', 'gbc']
        base_w = int(self.screen_width * 0.25)
        base_h = int(base_w * 0.75)
        
        if not os.path.exists(ICONS_PATH):
            try: os.makedirs(ICONS_PATH)
            except: pass

        for ext in extensions:
            img_path = os.path.join(ICONS_PATH, f"{ext}.png")
            try:
                if os.path.exists(img_path):
                    image = pygame.image.load(img_path)
                    image = pygame.transform.scale(image, (base_w, base_h)) 
                else:
                    raise FileNotFoundError
            except:
                # Generación de placeholder si no existe imagen
                image = pygame.Surface((base_w, base_h))
                image.fill((80, 80, 80))
                text = pygame.font.Font(None, 50).render(ext.upper(), True, COLOR_WHITE)
                rect = text.get_rect(center=(base_w//2, base_h//2))
                image.blit(text, rect)
                pygame.draw.rect(image, COLOR_WHITE, (0,0,base_w,base_h), 4)
            icon_map[f".{ext}"] = image
        return icon_map

    def load_games(self):
        games = []
        extensions = ['*.nes', '*.sfc', '*.smc', '*.gba', '*.gb', '*.gbc']
        if not os.path.exists(ROMS_PATH): os.makedirs(ROMS_PATH)

        for ext in extensions:
            for file_path in glob.glob(os.path.join(ROMS_PATH, ext)):
                filename = os.path.basename(file_path)
                clean_name = os.path.splitext(filename)[0]
                games.append({
                    'name': clean_name,
                    'path': file_path,
                    'ext': os.path.splitext(filename)[1].lower()
                })
        games.sort(key=lambda x: x['name'])
        return games
    
    def usb_scanner_loop(self):
        """Detecta inserción de USB, monta, copia ROMs y notifica."""
        usb_processed = False 
        while True:
            try:
                if os.path.exists(USB_DEVICE):
                    if not usb_processed:
                        subprocess.run(["sudo", "mount", USB_DEVICE, USB_MOUNT_POINT], check=False)
                        
                        added_games = []
                        extensions = ['.nes', '.sfc', '.smc', '.gba', '.gb', '.gbc']
                        
                        for root, dirs, files in os.walk(USB_MOUNT_POINT):
                            for file in files:
                                ext = os.path.splitext(file)[1].lower()
                                if ext in extensions:
                                    source_path = os.path.join(root, file)
                                    dest_path = os.path.join(ROMS_PATH, file)
                                    
                                    if not os.path.exists(dest_path):
                                        shutil.copy2(source_path, dest_path)
                                        added_games.append(file)
                        
                        subprocess.run(["sudo", "umount", USB_MOUNT_POINT], check=False)
                        
                        if len(added_games) > 0:
                            self.games = self.load_games()
                            self.notification_lines = ["¡Juegos Nuevos!"] + added_games[:5]
                            if len(added_games) > 5:
                                self.notification_lines.append(f"...y {len(added_games)-5} mas")
                            
                            self.show_notification = True
                            self.notification_timer = 150 
                        
                        usb_processed = True
                else:
                    usb_processed = False
            except Exception as e:
                print(f"Error proceso USB: {e}")
            time.sleep(5)

    def run(self):
        running = True
        pygame.mouse.set_visible(False)
        
        while running:
            self.update_video_frame()
            
            # Control de inputs y temporizador de repetición
            current_time = pygame.time.get_ticks()
            if self.joystick:
                if current_time - self.input_timer > 150:
                    axis_x = self.joystick.get_axis(0)
                    hat = self.joystick.get_hat(0)
                    
                    if axis_x < -0.5 or hat[0] == -1:
                        self.selected_index = (self.selected_index - 1) % len(self.games)
                        self.input_timer = current_time
                    elif axis_x > 0.5 or hat[0] == 1:
                        self.selected_index = (self.selected_index + 1) % len(self.games)
                        self.input_timer = current_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT: self.selected_index = (self.selected_index - 1) % len(self.games)
                    elif event.key == pygame.K_RIGHT: self.selected_index = (self.selected_index + 1) % len(self.games)
                    elif event.key == pygame.K_RETURN: 
                        if self.games: self.launch_game(self.games[self.selected_index])
                    elif event.key == pygame.K_ESCAPE: running = False
                
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button == BTN_A or event.button == BTN_START:
                        # A o START para iniciar juego
                        if self.games: self.launch_game(self.games[self.selected_index])
                    
                    elif event.button == BTN_XBOX:
                        self.draw_shutdown_msg()
                        subprocess.run(['sudo', 'poweroff'])
            
            self.draw()
            self.clock.tick(30)
        
        if self.video_cap: self.video_cap.release()
        pygame.quit()

    def update_video_frame(self):
        """Lee frame de video y gestiona el reinicio del bucle."""
        if self.video_cap:
            ret, frame = self.video_cap.read()
            if not ret:
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.video_cap.read()
                if not ret:
                    self.video_cap.release()
                    self.load_video()
                    if self.video_cap: ret, frame = self.video_cap.read()
            
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Transformaciones para alinear formato OpenCV a Pygame
                frame = cv2.transpose(frame)
                frame = cv2.flip(frame, 0)
                frame = cv2.flip(frame, 0)
                frame = cv2.transpose(frame)
                video_surf = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
                self.current_video_frame = pygame.transform.scale(video_surf, (self.screen_width, self.screen_height))

    def draw_text_with_outline(self, text, font, color, x, y, outline_color=(0,0,0), thickness=3, center=False):
        text_surf = font.render(text, True, color)
        outline_surf = font.render(text, True, outline_color)
        
        if center:
            rect = text_surf.get_rect(center=(x, y))
            x, y = rect.topleft

        # Dibujado de contorno en 4 direcciones
        self.screen.blit(outline_surf, (x - thickness, y))
        self.screen.blit(outline_surf, (x + thickness, y))
        self.screen.blit(outline_surf, (x, y - thickness))
        self.screen.blit(outline_surf, (x, y + thickness))
        self.screen.blit(text_surf, (x, y))
        return text_surf.get_width()

    def draw_shutdown_msg(self):
        self.screen.fill((0,0,0))
        msg = self.font_game_big.render("APAGANDO SISTEMA...", True, COLOR_RED)
        rect = msg.get_rect(center=(self.screen_width//2, self.screen_height//2))
        self.screen.blit(msg, rect)
        pygame.display.flip()
        pygame.time.delay(1000)

    def draw(self):
        if hasattr(self, 'current_video_frame') and self.current_video_frame:
            self.screen.blit(self.current_video_frame, (0, 0))
        else:
            self.screen.fill((20, 20, 40))

        # Renderizado de notificación USB
        if self.show_notification and self.notification_timer > 0:
            box_w = 400
            box_h = 30 + (len(self.notification_lines) * 25)
            bg_surface = pygame.Surface((box_w, box_h))
            bg_surface.set_alpha(210)
            bg_surface.fill((0,0,0))
            
            start_x = self.screen_width - box_w - 20
            start_y = 20
            self.screen.blit(bg_surface, (start_x, start_y))
            
            for i, line in enumerate(self.notification_lines):
                color = COLOR_GREEN if i == 0 else COLOR_WHITE
                text_surf = self.font_notify.render(line, True, color)
                self.screen.blit(text_surf, (start_x + 15, start_y + 10 + (i * 25)))
            
            self.notification_timer -= 1
        elif self.notification_timer <= 0:
            self.show_notification = False

        if not self.games: return

        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        spacing = int(self.screen_width * 0.35)

        # Fondo de área de selección
        bar_height = int(self.screen_height * 0.65) 
        bar_y = center_y - (bar_height // 2)
        
        bar_surface = pygame.Surface((self.screen_width, bar_height))
        bar_surface.set_alpha(160)
        bar_surface.fill((0, 0, 0))
        self.screen.blit(bar_surface, (0, bar_y))
        
        pygame.draw.line(self.screen, COLOR_LINE, (0, bar_y), (self.screen_width, bar_y), 4)
        pygame.draw.line(self.screen, COLOR_LINE, (0, bar_y + bar_height), (self.screen_width, bar_y + bar_height), 4)

        # Renderizado de lista de juegos
        for i, game in enumerate(self.games):
            offset = i - self.selected_index
            x_pos = center_x + (offset * spacing)
            
            if -spacing < x_pos < self.screen_width + spacing:
                icon = self.icons.get(game['ext'], self.icons.get('.nes'))
                if i == self.selected_index:
                    scale = 1.2; alpha = 255; text_color = COLOR_YELLOW; font_to_use = self.font_game_big; shadow_offset = 4
                else:
                    scale = 0.6; alpha = 200; text_color = COLOR_WHITE; font_to_use = self.font_game_small; shadow_offset = 2

                w = int(icon.get_width() * scale)
                h = int(icon.get_height() * scale)
                scaled_icon = pygame.transform.scale(icon, (w, h))
                scaled_icon.set_alpha(alpha)
                
                icon_rect = scaled_icon.get_rect(center=(x_pos, center_y - 20))
                self.screen.blit(scaled_icon, icon_rect)
                
                text_y = center_y + (h // 2) + 20
                self.draw_text_with_outline(game['name'], font_to_use, text_color, x_pos, text_y, thickness=shadow_offset, center=True)

        # Renderizado de Cabecera
        margin_left = 50
        top_margin = 50
        if self.logo_img:
            self.screen.blit(self.logo_img, (margin_left, top_margin))
            margin_left += self.logo_img.get_width() + 15
        w1 = self.draw_text_with_outline("RETRO", self.font_title, COLOR_RED, margin_left, top_margin)
        margin_left += w1 + 5
        w2 = self.draw_text_with_outline("BOX", self.font_title, COLOR_GREEN, margin_left, top_margin)
        margin_left += w2 + 10
        w3 = self.draw_text_with_outline("PI", self.font_title, COLOR_RED, margin_left, top_margin)
        margin_left += w3 + 15 
        if self.logo_img: self.screen.blit(self.logo_img, (margin_left, top_margin))

        # Panel de Leyenda de Controles
        # Fondo negro inferior
        legend_bg = pygame.Surface((self.screen_width, 30)) 
        legend_bg.fill((0,0,0))
        self.screen.blit(legend_bg, (0, self.screen_height - 30))
        
        y_pos = self.screen_height - 22 
        x_cursor = 20 
        
        # Renderizado compacto de la leyenda
        self.draw_text_with_outline("[Cruz/Joy]", self.font_legend, COLOR_GREEN, x_cursor, y_pos, thickness=1)
        x_cursor += self.font_legend.size("[Cruz/Joy]")[0] + 8
        self.draw_text_with_outline("Mover", self.font_legend, COLOR_WHITE, x_cursor, y_pos, thickness=1)
        x_cursor += self.font_legend.size("Mover")[0] + 20
        
        self.draw_text_with_outline("[A/B]", self.font_legend, (255, 100, 100), x_cursor, y_pos, thickness=1)
        x_cursor += self.font_legend.size("[A/B]")[0] + 8
        self.draw_text_with_outline("Basicos juego/Entrar", self.font_legend, COLOR_WHITE, x_cursor, y_pos, thickness=1)
        x_cursor += self.font_legend.size("Basicos juego/Entrar")[0] + 20

        self.draw_text_with_outline("[Y]", self.font_legend, (100, 100, 255), x_cursor, y_pos, thickness=1)
        x_cursor += self.font_legend.size("[Y]")[0] + 8
        self.draw_text_with_outline("Menu juego", self.font_legend, COLOR_WHITE, x_cursor, y_pos, thickness=1)
        x_cursor += self.font_legend.size("Menu juego")[0] + 20
        
        self.draw_text_with_outline("[XBOX]", self.font_legend, COLOR_WHITE, x_cursor, y_pos, thickness=1)
        x_cursor += self.font_legend.size("[XBOX]")[0] + 8
        self.draw_text_with_outline("Apagar", self.font_legend, COLOR_WHITE, x_cursor, y_pos, thickness=1)
        x_cursor += self.font_legend.size("Apagar")[0] + 20

        self.draw_text_with_outline("[Sel+Start]", self.font_legend, COLOR_RED, x_cursor, y_pos, thickness=1)
        x_cursor += self.font_legend.size("[Sel+Start]")[0] + 8
        self.draw_text_with_outline("Salir Juego", self.font_legend, COLOR_WHITE, x_cursor, y_pos, thickness=1)

        pygame.display.flip()
    
    def launch_game(self, game_data):
        self.screen.fill((0,0,0))
        msg = self.font_game_small.render(f"Cargando {game_data['name']}...", True, COLOR_WHITE)
        rect = msg.get_rect(center=(self.screen_width//2, self.screen_height//2))
        self.screen.blit(msg, rect)
        pygame.display.flip()

        full_path = game_data['path']
        js = self.joystick 

        try:
            # Ejecución de emulador en subproceso
            launch_cmd = [
                'mednafen', 
                '-video.fs', '1', 
                '-command.exit', '0', 
                full_path
            ]

            process = subprocess.Popen(launch_cmd)
            
            time.sleep(3)
            self.screen.fill((0,0,0))
            pygame.display.flip()
            
            # Bucle de espera para detectar combo de salida
            game_running = True
            while game_running:
                if process.poll() is not None:
                    game_running = False
                    break

                pygame.event.pump() 
                
                try:
                    if js.get_button(BTN_SELECT) and js.get_button(BTN_START):
                        process.terminate() 
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill() 
                        game_running = False
                except:
                    pass
                
                time.sleep(0.1)
            
            # Restauración de interfaz gráfica
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height), 
                pygame.FULLSCREEN | pygame.DOUBLEBUF
            )
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
            
            # Reinicialización del subsistema de Joystick
            pygame.joystick.quit()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
            
            # Pantalla de salida
            self.screen.fill((0,0,0))
            msg_out = self.font_game_small.render(f"Saliendo de {game_data['name']}...", True, (255, 100, 100))
            rect_out = msg_out.get_rect(center=(self.screen_width//2, self.screen_height//2))
            self.screen.blit(msg_out, rect_out)
            pygame.display.flip()
            
            pygame.time.delay(2000)

            if self.video_cap: self.video_cap.grab()

        except Exception as e:
            print(f"Error ejecución: {e}")

if __name__ == "__main__":
    launcher = RetroLauncher()
    launcher.run()