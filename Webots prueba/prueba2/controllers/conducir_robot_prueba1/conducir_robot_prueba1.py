"""conducir_robot_prueba1 controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor




from controller import Robot

# El main
if __name__ == "__main__":
    # Crear la instancia del Robot
    robot = Robot()

    # Obtenemos el paso de tiempo del mundo actual
    timestep = int(robot.getBasicTimeStep())
    
    # Establecemos la velocidad máxima (en radianes por segundo)//VELOCIDAD ANGULAR
    Vmax = 6.28
    
    # Identificamos los motores 
    motor_izquierda = robot.getDevice('motor1')
    motor_derecha = robot.getDevice('motor2')
    
    # Configuramos los motores para modo velocidad (posición infinita)
    motor_izquierda.setPosition(float('inf'))
    motor_izquierda.setVelocity(0.0)
    
    motor_derecha.setPosition(float('inf'))
    motor_derecha.setVelocity(0.0)
    
    # Probemos con dar vueltas a un cuadrado
    num_lados = 4
    tam_lados = 0.25  #Probamos con un cuadrado
    
    # Transformarmos la velocidad angular en velocidad linear (V= r *Vangular)
    radio_rueda = 0.025
    vel_linear = radio_rueda * Vmax
    
    # Calculamos la duracionn que tardariamos en recorrer ese cuadrado
    duracion_de_lado = tam_lados / vel_linear 
    
    # Objetivo de giro (6.28= 2Pi)
    angulo_rotacion = 6.28 / num_lados
    
    # Calculamos el giro diferencial 
    distancia_entre_ruedas = 0.090
    # La velocidad angular del robot sobre su eje es: (Vder - Vizq) / distancia_entre_ruedas
    # Si una rueda va a Vmax y la otra a -Vmax:
    cantidad_de_rotacion = (2 * vel_linear) / distancia_entre_ruedas
    
    # TIempo de ejecucion (v=d/t -> t=d/v)
    tiempo_rotacion = angulo_rotacion / cantidad_de_rotacion
    
    # Obtenemos el tiempo de empezar del robnot
    start_time = robot.getTime() 
    
    # Tiempos de fase inicial
    tiempo_inicio_rotacion_robot = start_time + duracion_de_lado
    tiempo_final_rotacion_robot = tiempo_inicio_rotacion_robot + tiempo_rotacion
    
    # Bucle principal de control
    while robot.step(timestep) != -1:
        current_time = robot.getTime() # Definimos current_time para que funcione el if
        
        # Definimos velocidades por defecto (Avanzar)
        Vizqu = Vmax
        Vder = Vmax
        
        # La lógica de estados por tiempo
        if tiempo_inicio_rotacion_robot < current_time < tiempo_final_rotacion_robot:
            # Estado: Rotando
            Vizqu = -Vmax
            Vder = Vmax
        elif current_time > tiempo_final_rotacion_robot:
            # Estado: Resetear ciclo para el siguiente lado
            tiempo_inicio_rotacion_robot = current_time + duracion_de_lado
            tiempo_final_rotacion_robot = tiempo_inicio_rotacion_robot + tiempo_rotacion
        
        # Aplicamos la velocidad a los motores
        motor_izquierda.setVelocity(Vizqu)
        motor_derecha.setVelocity(Vder)