#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2026 by YOUR NAME HERE
#
#    This file is part of RoboComp
#

#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from rich.console import Console
from genericworker import *
import interfaces as ifaces
import sys
import time

sys.path.append('/opt/robocomp/lib')
console = Console(highlight=False)


class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, configData, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map, configData)
        self.Period = configData["Period"]["Compute"]

        # --- Parámetros ---
        self.VEL_AVANCE = 10   # mm/s
        self.VEL_GIRO_RAPIDO = 4.1 # rad/s
        self.VEL_GIRO_SUAVE = 2.1   # rad/s
        self.DIST_UMBRAL = 95  # mm (distancia para detectar obstáculo frontal)
        self.DIST_PARED = 150  # mm (distancia objetivo a la pared derecha)
        self.MARGEN = 40  # mm

        # Detección de esquina derecha
        self.DIST_ESQUINA = 200  # mm

        self.TIEMPO_GIRO_ESQUINA = 0.6  # segundos

        # Variables de estado
        self.estado = "NORMAL"  # NORMAL, EVITANDO_FRONTAL, GIRANDO_ESQUINA
        self.tiempo_estado = 0

        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        pass

#PRE: Tenemos un robot con los laseres inicializados
#EXP: Se obtiene las distancias (depuradas en mm) de lo que percibe cada laser
#POST: devuelve variables de las distancias de lo que detectan los laseres delanteros, los frontales y la "esquina derecha" (teniendo en cuenta el último laser delantero (8)
    def _distancias(self, lidar):
        # Láseres 4-8: frontales (índices 3-7)
        frontal = min(lidar[i].dist for i in range(3, 8))

        # Láseres 9-11: derecha (índices 8-10)
        der = min(lidar[i].dist for i in range(8, 11))

        # Láser diagonal derecha (el más frontal de la derecha, índice 8)
        esquina_derecha = lidar[8].dist if len(lidar) > 8 else 1000

        # IZQUIERDA SE IGNORA COMPLETAMENTE
        return frontal, der, esquina_derecha

#PRE: el modulo _distancias debe de haber sido ejecutado con anterioridad
#Exp: detecta si hay una pared delante
#POst: frontal : TRUE si la distancia de la pared frontal es menor al umbral propuesto, FALSE en caso contrario
    def hay_pared_delante(self, frontal):
        """Detecta si hay una pared justo delante"""
        return frontal < self.DIST_UMBRAL

#PRE: el modulo _distancias debe de haber sido ejecutado con anterioridad
#Exp: detecta si hay una esquina a la derecha
#POst: esquina derecha : TRUE si la distancia de la pared derecha es menor al umbral propuesto, FALSE en caso contrario
    def hay_esquina_derecha(self, esquina_derecha):
        """Detecta si hay una esquina a la derecha"""
        return esquina_derecha < self.DIST_ESQUINA

#PRE: el modulo _distancias debe de haber sido ejecutado con anterioridad
#Exp: detecta si hay una pared delante
#POst: frontal : TRUE si la distancia de la pared frontal es menor al umbral propuesto, FALSE en caso contrario
    def hay_pared_derecha(self, der):
        """Detecta si hay pared a la derecha"""
        return der < self.DIST_PARED + self.MARGEN

    @QtCore.Slot()
    def compute(self):
        try:
            laser_data = self.laser_proxy.getLaserData()
            frontal, der, esquina_derecha = self._distancias(laser_data)

            console.print(
                f"Estado: {self.estado} | F:{frontal:.0f} D:{der:.0f} E:{esquina_derecha:.0f}"
            )

            avance, rotacion = self.seguir_pared(frontal, der, esquina_derecha)
            self.differentialrobot_proxy.setSpeedBase(avance, rotacion)

        except Exception as e:
            console.print(f"[red]Error en compute: {e}[/red]")
            self.differentialrobot_proxy.setSpeedBase(0, 0)


#Exp: logica del laberinto, algoritmo de la mano derecha
    def seguir_pared(self, frontal, der, esquina_derecha):

        #Actualizamos tiempo de estado
        self.tiempo_estado += self.Period / 1000.0


        #CASO 0:Pared delante -> giramos izquierda
        if self.hay_pared_delante(frontal):
            console.print("CASO 0: Pared delante - Girando izquierda")
            self.estado = "EVITANDO_FRONTAL"
            self.tiempo_estado = 0
            return 0.0, self.VEL_GIRO_RAPIDO   # Giro izquierda (positivo)


        #CASO 3:Esquina derecha (pared en diagonal derecha) -> corregimos trayectoria
        if self.hay_esquina_derecha(esquina_derecha) and not self.hay_pared_delante(frontal):
            if self.estado != "GIRANDO_ESQUINA":
                console.print("CASO 3: Esquina derecha - Corrigiendo (girando derecha suave)")
                self.estado = "GIRANDO_ESQUINA"
                self.tiempo_estado = 0
                return self.VEL_AVANCE * 0.8, -self.VEL_GIRO_SUAVE  # Giro derecha (negativo)

        #Estado de giro de esquina
        if self.estado == "GIRANDO_ESQUINA":
            if self.tiempo_estado < self.TIEMPO_GIRO_ESQUINA:
                console.print(f"Girando en esquina... {self.tiempo_estado:.1f}s")
                return self.VEL_AVANCE * 0.4, -self.VEL_GIRO_SUAVE
            else:
                console.print("Esquina superada")
                self.estado = "NORMAL"
                self.tiempo_estado = 0

        #Estado: SEGUIMIENTO NORMAL (MANO DERECHA) ---
        if self.estado == "NORMAL":
            #CASO 1: Hay pared derecha -> avanzamos recto (mientras seguimos pared)
            if self.hay_pared_derecha(der):
                console.print("CASO 1: Siguiendo pared derecha - Avanzando recto")
                #Corregimos para mantener una buena distancia de la mano derecha
                error = der - self.DIST_PARED
                correcion = 0.006
                rot =correcion * error
                rot = max(-self.VEL_GIRO_SUAVE * 0.5, min(self.VEL_GIRO_SUAVE * 0.5, rot))

                avance = self.VEL_AVANCE
                if abs(error) > 50:
                    avance = self.VEL_AVANCE * 0.7

                return avance, rot

            #CASO 2: No hay pared derecha -> buscamos pared (giramos a la derecha)
            else:
                console.print("CASO 2: Sin pared derecha - Buscando (girando derecha)")
                return self.VEL_AVANCE * 0.4, -self.VEL_GIRO_SUAVE * 0.7

        #Estado: EVITANDO_FRONTAL (continuar giro izquierda)
        if self.estado == "EVITANDO_FRONTAL":
            if self.tiempo_estado < 1.0:
                console.print(f"Evitando frontal... {self.tiempo_estado:.1f}s")
                return 0.0, self.VEL_GIRO_RAPIDO * 0.8
            else:
                console.print("Frontal evitado")
                self.estado = "NORMAL"
                self.tiempo_estado = 0
                return self.VEL_AVANCE * 0.6, 0.0

        # Fallback
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



