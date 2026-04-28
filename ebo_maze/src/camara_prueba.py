#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2026 by YOUR NAME HERE
#
#    This file is part of RoboComp
#

# !/usr/bin/python3
# -*- coding: utf-8 -*-

# !/usr/bin/python3
# -*- coding: utf-8 -*-

# !/usr/bin/python3
# -*- coding: utf-8 -*-

from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QApplication
from rich.console import Console
from genericworker import *
import interfaces as ifaces
import sys
import numpy as np
import cv2
from PIL import Image
import io
import math

sys.path.append('/opt/robocomp/lib')
console = Console(highlight=False)


class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, configData, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map, configData)

        # Selección del periodo desde el config
        self.Period = configData["Config"]["Period"]
        self.cont = 0

        # Variables para reconocimiento de FloorLight
        self.floorlight_detected = False
        self.detection_count = 0
        self.last_detection_position = None

        # Rangos de color para el FloorLight (ajusta según el color de tu FloorLight)
        # Por defecto, asumimos que el FloorLight tiene un color específico (ej. rojo, azul, etc.)
        # En HSV (Hue, Saturation, Value)
        self.color_ranges = {
            'red_lower': np.array([0, 100, 100]),
            'red_upper': np.array([10, 255, 255]),
            'red2_lower': np.array([160, 100, 100]),  # Segundo rango para rojo
            'red2_upper': np.array([179, 255, 255]),
            'blue_lower': np.array([100, 100, 100]),
            'blue_upper': np.array([130, 255, 255]),
            'green_lower': np.array([40, 100, 100]),
            'green_upper': np.array([80, 255, 255])
        }

        # Parámetros de detección
        self.min_floorlight_area = 500  # Área mínima en píxeles
        self.max_floorlight_area = 50000  # Área máxima
        self.min_aspect_ratio = 0.5  # Relación de aspecto mínima
        self.max_aspect_ratio = 2.0  # Relación de aspecto máxima

        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        """Destructor"""
        pass

    @Slot()
    def compute(self):
        try:
            # Obtener imagen de la cámara
            image_data = self.camerasimple_proxy.getImage()

            # Convertir la imagen para procesamiento
            frame = self.convert_image_to_cv2(image_data)

            if frame is not None:
                # Detectar FloorLight específicamente
                floorlight_detections = self.detect_floorlight(frame)

                if floorlight_detections:
                    self.floorlight_detected = True
                    self.detection_count += 1
                    self.last_detection_position = floorlight_detections[0]  # Guardar la primera detección

                    console.log(f"[green]✓ FLOORLIGHT DETECTADO! ({self.detection_count} veces)")
                    console.log(
                        f"  - Posición central: ({self.last_detection_position['center_x']}, {self.last_detection_position['center_y']})")
                    console.log(f"  - Área: {self.last_detection_position['area']} px")
                    console.log(f"  - Distancia estimada: {self.last_detection_position['estimated_distance']:.2f} m")

                    # Dibujar información en la imagen
                    self.draw_detection_info(frame, floorlight_detections)

                    # Aquí puedes añadir acciones específicas cuando se detecta el FloorLight
                    # Por ejemplo, mover el robot hacia él o detenerse
                    # self.approach_floorlight()

                else:
                    if self.floorlight_detected:
                        console.log("[yellow]FloorLight ya no está visible")
                        self.floorlight_detected = False
                        self.last_detection_position = None

                # Opcional: guardar imagen cuando se detecta
                if floorlight_detections and self.cont % 30 == 0:
                    self.save_detection_image(frame, floorlight_detections)

            self.cont += 1

        except Exception as e:
            console.log(f"[red]Error en compute: {e}")

        return True

    def convert_image_to_cv2(self, timage):
        """Convierte TImage de RoboComp a formato cv2"""
        try:
            img_bytes = bytes(timage.image)
            nparr = np.frombuffer(img_bytes, np.uint8)

            if timage.compressed:
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                img = nparr.reshape((timage.height, timage.width, timage.depth // 8))
                if timage.depth == 24:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            return img
        except Exception as e:
            console.log(f"[red]Error convirtiendo imagen: {e}")
            return None

    def detect_floorlight(self, frame):
        """
        Detecta específicamente el objeto FloorLight en la imagen
        """
        detections = []

        # Convertir a HSV para mejor detección de color
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Crear máscaras para diferentes colores (ajusta según el color de tu FloorLight)
        masks = []

        # Detectar rojo (que puede estar en dos rangos)
        mask_red1 = cv2.inRange(hsv, self.color_ranges['red_lower'], self.color_ranges['red_upper'])
        mask_red2 = cv2.inRange(hsv, self.color_ranges['red2_lower'], self.color_ranges['red2_upper'])
        masks.append(cv2.bitwise_or(mask_red1, mask_red2))

        # Detectar azul
        mask_blue = cv2.inRange(hsv, self.color_ranges['blue_lower'], self.color_ranges['blue_upper'])
        masks.append(mask_blue)

        # Detectar verde
        mask_green = cv2.inRange(hsv, self.color_ranges['green_lower'], self.color_ranges['green_upper'])
        masks.append(mask_green)

        # Combinar máscaras (o usar solo la que corresponda al color de tu FloorLight)
        combined_mask = masks[0]  # Si tu FloorLight es rojo
        # combined_mask = cv2.bitwise_or(masks[0], masks[1])  # Si puede ser múltiples colores

        # Aplicar operaciones morfológicas para limpiar la máscara
        kernel = np.ones((5, 5), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

        # Encontrar contornos
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Obtener dimensiones del frame para cálculos de distancia
        height, width = frame.shape[:2]

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filtrar por área
            if self.min_floorlight_area < area < self.max_floorlight_area:
                # Obtener rectángulo delimitador
                x, y, w, h = cv2.boundingRect(contour)

                # Verificar relación de aspecto
                aspect_ratio = w / h
                if self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio:
                    # Calcular centro
                    center_x = x + w // 2
                    center_y = y + h // 2

                    # Estimar distancia basada en el área (calibración necesaria)
                    # Asumiendo que a mayor área, más cerca está
                    reference_area = 5000  # Área de referencia a 1 metro (ajusta según tus pruebas)
                    estimated_distance = math.sqrt(reference_area / area) if area > 0 else 0

                    # Calcular ángulo respecto al centro del robot
                    angle_to_center = (center_x - width / 2) * 60 / width  # Asumiendo FOV de 60 grados

                    detection = {
                        'contour': contour,
                        'x': x, 'y': y, 'w': w, 'h': h,
                        'center_x': center_x,
                        'center_y': center_y,
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'estimated_distance': estimated_distance,
                        'angle': angle_to_center
                    }

                    detections.append(detection)

        # Ordenar por área (el más grande primero = más cercano)
        detections.sort(key=lambda d: d['area'], reverse=True)

        return detections

    def draw_detection_info(self, frame, detections):
        """Dibuja información de detección en la imagen"""
        for det in detections:
            # Dibujar rectángulo
            cv2.rectangle(frame, (det['x'], det['y']),
                          (det['x'] + det['w'], det['y'] + det['h']),
                          (0, 255, 0), 2)

            # Dibujar centro
            cv2.circle(frame, (det['center_x'], det['center_y']), 5, (0, 0, 255), -1)

            # Añadir texto con información
            info_text = f"FloorLight: {det['estimated_distance']:.1f}m"
            cv2.putText(frame, info_text, (det['x'], det['y'] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def save_detection_image(self, frame, detections):
        """Guarda la imagen con las detecciones"""
        frame_copy = frame.copy()
        self.draw_detection_info(frame_copy, detections)

        filename = f"floorlight_detection_{self.cont}.jpg"
        cv2.imwrite(filename, frame_copy)
        console.log(f"Imagen guardada: {filename}")

    def approach_floorlight(self):
        """Mueve el robot hacia el FloorLight detectado"""
        if self.last_detection_position:
            distance = self.last_detection_position['estimated_distance']
            angle = self.last_detection_position['angle']

            console.log(f"Acercándose al FloorLight - Distancia: {distance:.2f}m, Ángulo: {angle:.1f}°")

            # Control de movimiento
            if distance > 0.5:  # Si está lejos
                # Ajustar rotación y avance
                rot_speed = -angle * 0.5  # Proporcional al ángulo
                adv_speed = 5.0

                # Limitar velocidades
                rot_speed = max(-5.0, min(5.0, rot_speed))

                # Enviar comandos al robot (ajusta según tu interfaz)
                # self.differentialrobot_proxy.setSpeedBase(adv_speed, rot_speed)
            else:
                # Detenerse cuando está cerca
                # self.differentialrobot_proxy.stopBase()
                console.log("FloorLight alcanzado!")

    def startup_check(self):
        """Verificación inicial"""
        console.log("[blue]Verificando detección de FloorLight...")

        try:
            # Probar conexión con la cámara
            test_image = self.camerasimple_proxy.getImage()
            if test_image:
                console.log("[green]✓ Cámara funcionando correctamente")

                # Probar detección
                frame = self.convert_image_to_cv2(test_image)
                if frame is not None:
                    detections = self.detect_floorlight(frame)
                    if detections:
                        console.log(f"[green]✓ FloorLight detectado en la verificación inicial!")
                    else:
                        console.log("[yellow]⚠ No se detectó FloorLight en la verificación inicial")
            else:
                console.log("[red]✗ Error con la cámara")
        except Exception as e:
            console.log(f"[red]✗ Error en verificación: {e}")

        QTimer.singleShot(200, QApplication.instance().quit)
    ######################
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