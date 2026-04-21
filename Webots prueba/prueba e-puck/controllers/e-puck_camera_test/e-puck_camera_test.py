from controller import Robot

robot = Robot()
timestep = int(robot.getBasicTimeStep())

# --- Configuración Cámara ---
cam = robot.getDevice("camera")
cam.enable(timestep)
width = cam.getWidth()   # Será 52
height = cam.getHeight() # Será 39

# --- Configuración Motores ---
left_motor = robot.getDevice('left wheel motor')
right_motor = robot.getDevice('right wheel motor')
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))

# Variable de estado del algoritmo del laberinto
estado_robot = "EXPLORANDO" # Puede ser "EXPLORANDO" o "STOP_FINAL"

# Velocidad de exploración
VELOCIDAD_BASE = 3.0

while robot.step(timestep) != -1:
    
    image = cam.getImage()
    
    # Analizaremos una pequeña ventana central (ej: 10x10 píxeles en el centro)
    # para no procesar toda la imagen y ser más rápidos.
    ventana_scan = 10
    start_x = (width // 2) - (ventana_scan // 2)
    start_y = (height // 2) - (ventana_scan // 2)
    
    pixeles_rojos_detectados = 0
    total_pixeles_ventana = ventana_scan * ventana_scan

    # Umbral de color: Definimos qué es "Rojo STOP"
    # El e-puck real tiene ruido, en simulación es más fácil.
    UMBRAL_ROJO_MIN = 150 # El canal rojo debe ser alto
    UMBRAL_G_B_MAX = 50   # Verde y Azul deben ser bajos (para que sea rojo puro)

    for x in range(start_x, start_x + ventana_scan):
        for y in range(start_y, start_y + ventana_scan):
            # Obtener componentes RGB del píxel
            r = cam.imageGetRed(image, width, x, y)
            g = cam.imageGetGreen(image, width, x, y)
            b = cam.imageGetBlue(image, width, x, y)
            
            # Comprobar si el píxel es dominantemente rojo
            if r > UMBRAL_ROJO_MIN and g < UMBRAL_G_B_MAX and b < UMBRAL_G_B_MAX:
                pixeles_rojos_detectados += 1

    # Decisión: ¿Es una pared de STOP?
    # Si más del 80% de la ventana central es roja, paramos.
    sensibilidad_parada = 0.80 
    if pixeles_rojos_detectados > (total_pixeles_ventana * sensibilidad_parada):
        if estado_robot != "STOP_FINAL":
            print("¡VISUAL STOP DETECTADO! Pared roja confirmada.")
            estado_robot = "STOP_FINAL"

    # ---------------------------------------------------------
    # 2. LÓGICA DE MOVIMIENTO (OBVIANDO TU ALGORITMO)
    # ---------------------------------------------------------

    vel_izq = 0.0
    vel_der = 0.0

    if estado_robot == "STOP_FINAL":
        # Parada de emergencia
        vel_izq = 0.0
        vel_der = 0.0
    else:
        # --- AQUÍ VA TU LÓGICA DE MOVERSE POR EL LABERINTO ---
        # (Ejemplo simple de ir recto)
        vel_izq = VELOCIDAD_BASE
        vel_der = VELOCIDAD_BASE
        # -----------------------------------------------------

    # Aplicar velocidades finales
    left_motor.setVelocity(vel_izq)
    right_motor.setVelocity(vel_der)