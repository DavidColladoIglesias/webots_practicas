#!/usr/bin/python3
# -*- coding: utf-8 -*-



import sys
import time
import cv2
import numpy as np

from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QApplication
from rich.console import Console

# Importaciones locales de RoboComp
from genericworker import *
import interfaces as ifaces

sys.path.append('/opt/robocomp/lib')
console = Console(highlight=False)


class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, configData, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map, configData)
        self.Period = configData["Period"]["Compute"]

        # Parámetros
        self.VEL_AVANCE = 10
        self.VEL_GIRO_RAPIDO = 3.3
        self.VEL_GIRO_SUAVE = 1.6
        self.VEL_GIRO_ESQUINA = 1.8
        self.DIST_UMBRAL = 215
        self.DIST_PARED = 120
        self.MARGEN = 50
        self.DIST_ESQUINA = 200
        self.CORRECCION_DISTANCIA = 0.02
        self.AMORTIGUACION_OSCILACION = 0.08
        self.error_anterior = 0.0

        self.TIEMPO_GIRO_ESQUINA = 0.6
        self.TIEMPO_DOBLAR_ESQUINA = 0.6

        # Variables de estado
        self.estado = "NORMAL"  # NORMAL, EVITANDO_FRONTAL, GIRANDO_ESQUINA, COOLDOWN_ESQUINA, DOBLANDO_ESQUINA
        self.tiempo_estado = 0

        # Bool para reconocimiento
        self.floorlight_detectado = False
        self.arbol_detectado = False

        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        pass

#PRE: Simulacion iniciada y Floorlight en el mapa
#Exp Activa la camara y cuando detecta el objeto floorloght en la simulación, se detiene
#POst: Abre una ventana con la camara y si detecta el objeto , el robot se detiene indefinidamente (META)
    def reconocer_floorlight(self, imagen):
        color = np.frombuffer(imagen.image, np.uint8).reshape(imagen.height, imagen.width, 3)
        cv2.imshow('Camera EBO', color)
        cv2.waitKey(1)
        bgr = cv2.cvtColor(color, cv2.COLOR_RGB2BGR)
        h, w = bgr.shape[:2]
        gris = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        roi = gris[:h // 2, :]
        roi_blur = cv2.GaussianBlur(roi, (9, 9), 2)

        # Detectamos círculos en la imagen
        circulos = cv2.HoughCircles(
            roi_blur,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=50,#!/usr/bin/python3
# -*- coding: utf-8 -*-



import sys
import time
import cv2
import numpy as np

from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QApplication
from rich.console import Console

# Importaciones locales de RoboComp
from genericworker import *
import interfaces as ifaces

sys.path.append('/opt/robocomp/lib')
console = Console(highlight=False)


class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, configData, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map, configData)
        self.Period = configData["Period"]["Compute"]

        # Parámetros
        self.VEL_AVANCE = 10
        self.VEL_GIRO_RAPIDO = 3.3
        self.VEL_GIRO_SUAVE = 1.6
        self.VEL_GIRO_ESQUINA = 1.8
        self.DIST_UMBRAL = 215
        self.DIST_PARED = 120
        self.MARGEN = 50
        self.DIST_ESQUINA = 200
        self.CORRECCION_DISTANCIA = 0.02
        self.AMORTIGUACION_OSCILACION = 0.08
        self.error_anterior = 0.0

        self.TIEMPO_GIRO_ESQUINA = 0.6
        self.TIEMPO_DOBLAR_ESQUINA = 0.6

        # Variables de estado
        self.estado = "NORMAL"  # NORMAL, EVITANDO_FRONTAL, GIRANDO_ESQUINA, COOLDOWN_ESQUINA, DOBLANDO_ESQUINA
        self.tiempo_estado = 0

        # Bool para reconocimiento
        self.floorlight_detectado = False
        self.arbol_detectado = False

        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        pass

#PRE: Simulacion iniciada y Floorlight en el mapa
#Exp Activa la camara y cuando detecta el objeto floorloght en la simulación, se detiene
#POst: Abre una ventana con la camara y si detecta el objeto , el robot se detiene indefinidamente (META)
    def reconocer_floorlight(self, imagen):
        color = np.frombuffer(imagen.image, np.uint8).reshape(imagen.height, imagen.width, 3)
        cv2.imshow('Camera EBO', color)
        cv2.waitKey(1)
        bgr = cv2.cvtColor(color, cv2.COLOR_RGB2BGR)
        h, w = bgr.shape[:2]
        gris = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        roi = gris[:h // 2, :]
        roi_blur = cv2.GaussianBlur(roi, (9, 9), 2)

        # Detectamos círculos en la imagen
        circulos = cv2.HoughCircles(
            roi_blur,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            param1=50,
            param2=25,
            minRadius=30,
            maxRadius=120
        )

        if circulos is None:
            return False, 0

        circulos = np.round(circulos[0]).astype(int)

        for (cx, cy, r) in circulos:
            mascara = np.zeros(roi.shape, dtype=np.uint8)
            cv2.circle(mascara, (cx, cy), r, 255, -1)
            brillo_medio = cv2.mean(roi, mask=mascara)[0]

            if brillo_medio < 200:
                continue

            poste_x1 = cx - 8
            poste_x2 = cx + 8
            poste_y1 = cy + r
            poste_y2 = min(h, cy + r + int(h * 0.45))

            if poste_y2 <= poste_y1 or poste_x2 >= w or poste_x1 < 0:
                continue

            roi_poste = gris[poste_y1:poste_y2, poste_x1:poste_x2]

            if roi_poste.size == 0:
                continue

            brillo_poste = np.mean(roi_poste)
            std_poste = np.std(roi_poste)

            tiene_poste = (40 < brillo_poste < 200) and (std_poste < 60)

            if not tiene_poste:
                continue

            margen = int(w * 0.08)
            if cx < margen or cx > (w - margen):
                continue

            return True, len(circulos)

        return False, 0

#PRE: Simulación iniciada y árbol en maceta visible en el mapa
#Exp: Analiza la imagen buscando la combinación de verde vegetal (hojas) y marrón (maceta)
#Post: Devuelve True si detecta el árbol, False en caso contrario
    def reconocer_arbol(self, imagen):
        color = np.frombuffer(imagen.image, np.uint8).reshape(imagen.height, imagen.width, 3)
        cv2.imshow('Camera EBO', color)
        cv2.waitKey(1)
        bgr = cv2.cvtColor(color, cv2.COLOR_RGB2BGR)
        h, w = bgr.shape[:2]
        gris = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        roi = gris[:h // 2, :]
        roi_blur = cv2.GaussianBlur(roi, (9, 9), 2)

        # Detección de color sobre bgr
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        # Verde en mitad superior
        lower_verde = np.array([25, 20, 20])
        upper_verde = np.array([95, 255, 210])
        mascara_verde = cv2.inRange(hsv, lower_verde, upper_verde)
        mascara_verde[h // 2:, :] = 0
        proporcion_verde = cv2.countNonZero(mascara_verde) / (w * h // 2)

        # Marrón en mitad inferior
        lower_marron = np.array([3, 60, 40])
        upper_marron = np.array([20, 255, 200])
        mascara_marron = cv2.inRange(hsv, lower_marron, upper_marron)
        mascara_marron[:h // 2, :] = 0
        proporcion_marron = cv2.countNonZero(mascara_marron) / (w * h // 2)

        #console.print(f"ARBOL DEBUG:  verde:{proporcion_verde:.3f} marron:{proporcion_marron:.3f}")

        if proporcion_verde < 0.05:
            return False, 0
        if proporcion_marron < 0.005:
            return False, 0

        #maceta y hojas alineadas horizontalmente
        mv = cv2.moments(mascara_verde)
        mm = cv2.moments(mascara_marron)
        if mv["m00"] == 0 or mm["m00"] == 0:
            return False, 0

        cx_verde = int(mv["m10"] / mv["m00"])
        cx_marron = int(mm["m10"] / mm["m00"])
        #console.print(f"ARBOL DEBUG → diff:{abs(cx_verde - cx_marron)} limite:{w * 0.40:.0f}")

        if abs(cx_verde - cx_marron) > w * 0.40:
            return False, 0

        console.print("ÁRBOL DETECTADO")
        return True, cv2.countNonZero(mascara_verde)

#PRE: simulacion iniciada, robot EBO iniciado
#Exp: detecta , a través de los laseres del EBO, el tipo de pared que tiene alrededor suya
#Post: Devuelve tres flags indicando las paredes que rodean al EBO
    def _distancias(self, lidar):
        frontal = min(lidar[i].dist for i in range(3, 8))
        der = min(lidar[i].dist for i in range(9, 12))
        esquina_derecha = lidar[8].dist if len(lidar) > 8 else 1000
        return frontal, der, esquina_derecha

#PRE: ... y el modulo __distancias iniciado
#Exp: Compara frontal con la variable DIST_umbral
#POst: en caso de de que el frontal supere la distancia minima del umbral, devuelve true, en caso contrario, false
    def hay_pared_delante(self, frontal):
        return frontal < self.DIST_UMBRAL

#PRE: ... y el modulo __distancias iniciado
#Exp: Compara esquina derecha con la variable DIST_ESQUINA
#POst: en caso de de que la esquina derecha supere la distancia minima del umbral, devuelve true, en cas
    def hay_esquina_derecha(self, esquina_derecha):
        return esquina_derecha < self.DIST_ESQUINA

#PRE: ... y el modulo __distancias iniciado
#Exp: Compara pared derecha con la variable DIST_PARED más un margen ampliado para detectar la pared
#POst: en caso de de que la pared derecha supere la distancia minima del umbral, devuelve true, en caso contrario, false
    def hay_pared_derecha(self, der):
        return der < self.DIST_PARED + self.MARGEN + 150

    @Slot()
    def compute(self):
        laser_data = self.laser_proxy.getLaserData()
        frontal, der, esquina_derecha = self._distancias(laser_data)
        camara_data = self.camerasimple_proxy.getImage()

        if camara_data is not None:
            detectado_fl, area = self.reconocer_floorlight(camara_data)
            detectado_arbol, _ = self.reconocer_arbol(camara_data)

            if detectado_fl:
                self.floorlight_detectado = True
                console.print("META ALCANZADA: FloorLight detectado - PARANDO")
                self.differentialrobot_proxy.setSpeedBase(0, 0)
                self.timer.stop()
                return

            if detectado_arbol:
                self.arbol_detectado = True
                console.print("[green]ÁRBOL DETECTADO - PARANDO[/green]")
                self.differentialrobot_proxy.setSpeedBase(0, 0)
                self.timer.stop()
                return

        console.print(f"Estado: {self.estado} | F:{frontal:.0f} D:{der:.0f} E:{esquina_derecha:.0f}")
        avance, rotacion = self.seguir_pared(frontal, der, esquina_derecha)
        self.differentialrobot_proxy.setSpeedBase(avance, rotacion)

    def seguir_pared(self, frontal, der, esquina_derecha):
        self.tiempo_estado += self.Period / 1000.0

        # EMERGENCIA: pared frontal
        if self.hay_pared_delante(frontal) and self.estado != "EVITANDO_FRONTAL":
            self.estado = "EVITANDO_FRONTAL"
            self.tiempo_estado = 0
            return 0.0, self.VEL_GIRO_RAPIDO * 1.2

        if self.estado == "EVITANDO_FRONTAL":
            if not self.hay_pared_delante(frontal):
                self.estado = "NORMAL"
                self.tiempo_estado = 0
                return self.VEL_AVANCE * 0.6, 0.0
            return self.VEL_AVANCE * 0.2, self.VEL_GIRO_RAPIDO

        # CORRECCIÓN ESQUINA
        if self.estado == "GIRANDO_ESQUINA":
            if self.tiempo_estado < self.TIEMPO_GIRO_ESQUINA:
                return self.VEL_AVANCE * 0.4, -self.VEL_GIRO_SUAVE
            self.estado = "COOLDOWN_ESQUINA"
            self.tiempo_estado = 0
            return self.VEL_AVANCE * 0.5, 0.0

        if self.estado == "COOLDOWN_ESQUINA":
            if self.tiempo_estado < 0.4:
                return self.VEL_AVANCE * 0.5, 0.0
            self.estado = "NORMAL"
            self.tiempo_estado = 0

        # DOBLANDO ESQUINA
        if self.estado == "DOBLANDO_ESQUINA":
            if self.tiempo_estado < self.TIEMPO_DOBLAR_ESQUINA:
                return self.VEL_AVANCE * 0.5, -self.VEL_GIRO_ESQUINA
            self.estado = "NORMAL"
            self.tiempo_estado = 0

        # NORMAL
        if self.estado == "NORMAL":
            if self.hay_pared_delante(frontal):
                self.estado = "EVITANDO_FRONTAL"
                return 0.0, self.VEL_GIRO_RAPIDO

            if self.hay_esquina_derecha(esquina_derecha):
                self.estado = "GIRANDO_ESQUINA"
                return self.VEL_AVANCE * 0.8, -self.VEL_GIRO_SUAVE

            if self.hay_pared_derecha(der):
                error = der - self.DIST_PARED
                derivada = error - self.error_anterior
                self.error_anterior = error
                rot = -(self.CORRECCION_DISTANCIA * error + self.AMORTIGUACION_OSCILACION * derivada)
                rot = max(-self.VEL_GIRO_SUAVE, min(self.VEL_GIRO_SUAVE, rot))
                return self.VEL_AVANCE * (1.0 - min(abs(error) / 200.0, 0.5)), rot

            self.estado = "DOBLANDO_ESQUINA"
            return self.VEL_AVANCE * 0.5, -self.VEL_GIRO_ESQUINA

        return self.VEL_AVANCE * 0.5, 0.0

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

######
        # From the RoboCompCameraSimple you can call this methods:
        # RoboCompCameraSimple.TImage self.camerasimple_proxy.getImage()

        ######################
        # From the RoboCompCameraSimple you can use this types:
        # ifaces.RoboCompCameraSimple.TImage

        ######################
        # From the RoboCompDifferentialRobot you can call this methods:
        # RoboCompDifferentialRobot.void self.differentialrobot_proxy.correctOdometer(int x, int z, float alpha)
        # RoboCompDifferentialRobot.void self.differentialrobot_proxy.getBasePose(int x, int z, float alpha)
        # RoboCompDifferentialRobot.void self.differentialrobot_proxy.getBaseState(RoboCompGenericBase.TBaseState state)
        # RoboCompDifferentialRobot.void self.differentialrobot_proxy.resetOdometer()
        # RoboCompDifferentialRobot.void self.differentialrobot_proxy.setOdometer(RoboCompGenericBase.TBaseState state)
        # RoboCompDifferentialRobot.void self.differentialrobot_proxy.setOdometerPose(int x, int z, float alpha)
        # RoboCompDifferentialRobot.void self.differentialrobot_proxy.setSpeedBase(float adv, float rot)
        # RoboCompDifferentialRobot.void self.differentialrobot_proxy.stopBase()

        ######################
        # From the RoboCompDifferentialRobot you can use this types:
        # ifaces.RoboCompDifferentialRobot.TMechParams

        ######################
        # From the RoboCompLaser you can call this methods:
        # RoboCompLaser.TLaserData self.laser_proxy.getLaserAndBStateData(RoboCompGenericBase.TBaseState bState)
        # RoboCompLaser.LaserConfData self.laser_proxy.getLaserConfData()
        # RoboCompLaser.TLaserData self.laser_proxy.getLaserData()

        ######################
        # From the RoboCompLaser you can use this types:
        # ifaces.RoboCompLaser.LaserConfData
        # ifaces.RoboCompLaser.TData