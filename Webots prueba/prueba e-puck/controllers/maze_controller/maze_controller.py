from controller import Robot

# Inicializar instancia del robot
robot = Robot()
timestep = int(robot.getBasicTimeStep())
Vmax = 6.28

# --- CONFIGURACIÓN DE DISPOSITIVOS ---

# Configuración de la cámara
cam = robot.getDevice("camera")
cam.enable(64)
anchura_camara = cam.getWidth()
altura_camara = cam.getHeight()

# print(f"Cámara inicializada: {anchura_camara}x{altura_camara}")
estado_robot= "EXPLORANDO" #dos estados : EXPLORANDO O FINAL
# Configuración de los motores
motor_izquierda = robot.getDevice('left wheel motor')
motor_derecha = robot.getDevice('right wheel motor')

motor_izquierda.setPosition(float('inf'))
motor_derecha.setPosition(float('inf'))

motor_izquierda.setVelocity(0.0)
motor_derecha.setVelocity(0.0)

# Configuración de los sensores de proximidad
prox_sensores = []
for i in range(8):
    nombre_sensor = 'ps' + str(i)
    prox_sensores.append(robot.getDevice(nombre_sensor))
    prox_sensores[i].enable(timestep)

umbral = 80.0
llegado_a_meta = False

# Variables para estabilizar la detección
detecciones_consecutivas = 0
detecciones_necesarias = 3
frame_count = 0

# --- BUCLE PRINCIPAL ---

while robot.step(timestep) != -1:
    
    # 1. PROCESAMIENTO DE IMAGEN (DETECCIÓN DE COLOR ROJO)
    image = cam.getImage()
    
    
    
    # Leer sensores
    pared_delantera = prox_sensores[0].getValue() > umbral or prox_sensores[7].getValue() > umbral
    pared_derecha = prox_sensores[2].getValue() > umbral
    esquina_derecha = prox_sensores[1].getValue() > umbral
    
    # Comportamiento por defecto: avanzar
    velocidad_izquierda = Vmax
    velocidad_derecha = Vmax
    
    if pared_delantera:
        print("Caso 0: Pared delante, girando izquierda")
        velocidad_izquierda = -Vmax
        velocidad_derecha = Vmax
    else:
        if pared_derecha:
            print("Caso 1: Siguiendo pared derecha")
            velocidad_izquierda = Vmax
            velocidad_derecha = Vmax
        else:
            print("Caso 2: Buscando pared derecha")
            velocidad_izquierda = Vmax
            velocidad_derecha = Vmax / 4
        
        if esquina_derecha:
            print("Caso 3: Corrigiendo trayectoria")
            velocidad_izquierda = Vmax / 4
            velocidad_derecha = Vmax
    
    # Aplicar velocidades
    motor_izquierda.setVelocity(velocidad_izquierda)
    motor_derecha.setVelocity(velocidad_derecha)