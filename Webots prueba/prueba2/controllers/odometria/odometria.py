"""odometria controller."""
from controller import Robot
import math # Importante para las funciones seno y coseno

def run_robot(robot):
    # Obtener el paso de tiempo del mundo actual
    timestep = int(robot.getBasicTimeStep()) 
    
    # Creamos la instancia del motor
    izquierda_motor = robot.getDevice('motor1')  
    derecha_motor = robot.getDevice('motor2')  
    
    izquierda_motor.setPosition(float('inf'))
    izquierda_motor.setVelocity(0.0)
    
    derecha_motor.setPosition(float('inf'))
    derecha_motor.setVelocity(0.0)
    
    # Creamos las instancias del sensor
    izquierda_ps = robot.getDevice('ps1') 
    derecha_ps = robot.getDevice('ps2')  
  
    # Usamos enable
    izquierda_ps.enable(timestep)
    derecha_ps.enable(timestep)
    
    ps_valores = [0, 0]
    distancia_valores = [0, 0] 
    
    # Parámetros Físicos del Robot 
    radio_rueda = 0.025
    distancia_entre_ruedas = 0.09
    
    # Velocidad para mover el robot
    velocidad = 3.0  
    
    posicion_del_robot = [0, 0, 0] # x, y, theta (orientación)
    ultimos_val_ps = [0, 0]
    
    # Main loop
    while robot.step(timestep) != -1:
        
        # Obtenemos los valores actuales de los encoders (en radianes)
        ps_valores[0] = izquierda_ps.getValue()
        ps_valores[1] = derecha_ps.getValue()
        
        # CÁLCULOS DE FÍSICA Y ODOMETRÍA 
        
        #Calculamos cuánto ha girado cada rueda desde el último paso
        diff_izq = ps_valores[0] - ultimos_val_ps[0]
        diff_der = ps_valores[1] - ultimos_val_ps[1]
        
        # Convertimos el giro (radianes) en distancia lineal recorrida (metros)
        # Fórmula: s = r * theta
        distancia_valores[0] = diff_izq * radio_rueda
        distancia_valores[1] = diff_der * radio_rueda
        
        # Calculamos el avance lineal promedio (v) y el cambio de orientación (omega)
        distancia_lineal = (distancia_valores[0] + distancia_valores[1]) / 2.0
        # El cambio de ángulo depende de la diferencia de recorrido entre ruedas
        delta_theta = (distancia_valores[1] - distancia_valores[0]) / distancia_entre_ruedas
        
        # Actualizamos la orientación del robot (Theta)
        posicion_del_robot[2] += delta_theta
        
        # Descomponemos el movimiento lineal en los ejes X e Y usando la orientación actual
        vx = distancia_lineal * math.cos(posicion_del_robot[2])
        vy = distancia_lineal * math.sin(posicion_del_robot[2])
        
        # Actualizamos las coordenadas globales
        posicion_del_robot[0] += vx
        posicion_del_robot[1] += vy
        
        # Mostrar resultados
        print("---------------------------")
        print("Posición: X:{:.2f} Y:{:.2f} Theta:{:.2f}".format(
            posicion_del_robot[0], posicion_del_robot[1], posicion_del_robot[2]))
        
        # MOVER EL ROBOT
        izquierda_motor.setVelocity(-velocidad)   
        derecha_motor.setVelocity(velocidad)  
        
        # Guardamos valores actuales para la siguiente iteración
        ultimos_val_ps[0] = ps_valores[0]
        ultimos_val_ps[1] = ps_valores[1]

if __name__ == "__main__":
    my_robot = Robot()
    run_robot(my_robot)