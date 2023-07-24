import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QCheckBox, QGridLayout, QSizePolicy, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtGui import QIcon, QImage, QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal

from app.business.YOLOv7.track import TrackClass

class SignalManager(QObject):
    button_signal = pyqtSignal(bool, bool, bool, bool)

class DetectionThread(QThread):
    def __init__(self, tracker, source, yolo_weights, classes, conf_thres, iou_thres):
        super().__init__()
        self.tracker = tracker
        self.source = source
        self.yolo_weights = yolo_weights
        self.classes = classes
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres

    def run(self):
        self.tracker.run_detection(source=self.source, 
                                       yolo_weights=self.yolo_weights, 
                                       classes=self.classes,
                                       conf_thres=self.conf_thres,
                                       iou_thres=self.iou_thres)

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.signal_manager = SignalManager()
        self.tracker = TrackClass()
        self.tracker.new_detection.connect(self.on_new_detection)

        self.setWindowTitle('Universidad Católica del Norte')
        # self.resize(854, 480)
        self.resize(1280, 720)

        icono = QIcon("logo-ucn.png")
        self.setWindowIcon(icono)
        self.video_path = None
        self.filtrar_label = None
        self.velocidad_checkbox = None
        self.centroide_checkbox = None
        self.bounding_boxes_checkbox = None
        self.pause_status = None
        self.last_detection_timestamp = 0
        self.velocidades = {}  # Diccionario para almacenar las velocidades
        self.centroides = {}  # Diccionario para almacenar los centroides
        self.bounding_boxes = {}  # Diccionario para almacenar las bounding boxes
        self.start_time = 0  # Variable de tiempo para el inicio de la detección
        self.pause_status = False

        self.grid = QGridLayout()

        # Agregar el logo en la primera fila de la primera columna
        logo_label = QLabel()
        logo_pixmap = QPixmap("logo-ucn.png").scaled(71, 71)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)

        # Agregar texto al lado del logo
        texto_label = QLabel("Sistema de detección peatonal")
        texto_label.setStyleSheet("font-size: 18px; text-align: center;")

        # Crear un QHBoxLayout y agregar el logo y el texto
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(texto_label)
        logo_layout.setAlignment(Qt.AlignCenter)

        # Agregar el QHBoxLayout al grid layout
        self.grid.addLayout(logo_layout, 0, 0, 1, 1)

        # Crear hbox para contener botones y opciones de filtrado
        self.hbox_buttons = QHBoxLayout()

        self.importar_btn = QPushButton("Importar Video")
        self.importar_btn.clicked.connect(self.importar_video)
        self.importar_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)  # Aplica la política de tamaño al botón
        self.hbox_buttons.addWidget(self.importar_btn)

        self.detectar_btn = QPushButton("Detectar Personas")
        self.detectar_btn.clicked.connect(self.detectar_personas)
        self.detectar_btn.setEnabled(False)
        self.detectar_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)  # Aplica la política de tamaño al botón
        self.hbox_buttons.addWidget(self.detectar_btn)

        # Agregar un botón para guardar el frame actual como imagen
        self.guardar_btn = QPushButton("Guardar frame actual")
        self.guardar_btn.setEnabled(True)
        self.guardar_btn.clicked.connect(self.guardar_frame)

        # Agregar un botón para guardar el csv 
        self.guardar_csv_btn = QPushButton("Guardar CSV")
        self.guardar_csv_btn.setEnabled(True)
        self.guardar_csv_btn.clicked.connect(self.guardar_csv)
        
        # Crear una QVBoxLayout y agregar la QHBoxLayout de botones
        self.vbox_left = QVBoxLayout()
        self.vbox_left.addLayout(self.hbox_buttons)

        # Añadir vbox_left a la segunda fila de la primera columna
        self.grid.addLayout(self.vbox_left, 1, 0)

        # Crear vbox_left2 y agregar el botón de guardar frame
        self.vbox_left2 = QVBoxLayout()
        self.vbox_left2.setAlignment(Qt.AlignCenter)
        self.vbox_left2.addWidget(self.guardar_btn)
        # Añadir vbox_left2 a la cuarta fila de la primera columna
        self.grid.addLayout(self.vbox_left2, 6, 0)

        # Crear vbox_left3 y agregar el botón de guardar frame
        self.vbox_left3 = QVBoxLayout()
        self.vbox_left3.setAlignment(Qt.AlignCenter)
        self.vbox_left3.addWidget(self.guardar_csv_btn)
        # Añadir vbox_left3 a la x fila de la primera columna
        self.grid.addLayout(self.vbox_left3, 7, 0)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)  # Aplica la política de tamaño a video_label

        # Añadir video_label al abarcar las primeras 10 filas de la segunda columna
        self.grid.addWidget(self.video_label, 0, 1, 6, 1)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)  # Rango del progreso de 0 a 100

        self.pausa_btn = QPushButton("Pausar")
        self.pausa_btn.setEnabled(True)
        self.pausa_btn.clicked.connect(self.pausar_video)
        self.pausa_btn.setCheckable(True)  # Hacer que el botón sea alternable entre dos estados
        self.pausa_btn.setChecked(False)

        self.stop_btn = QPushButton("Detener")
        self.stop_btn.setEnabled(True)
        
        pausa_progress_layout = QHBoxLayout()
        pausa_progress_layout.addWidget(self.pausa_btn)
        pausa_progress_layout.addWidget(self.stop_btn)

        # Crear un QHBoxLayout para el botón de pausa y la barra de progreso
        pausa_progress_layout = QHBoxLayout()
        pausa_progress_layout.addWidget(self.pausa_btn)
        pausa_progress_layout.addWidget(self.progressBar)
        pausa_progress_layout.addWidget(self.stop_btn)

        # Agregar el QHBoxLayout a la cuadrícula
        self.grid.addLayout(pausa_progress_layout, 6, 1)

        # Añadir un espacio vacío en la parte inferior de la segunda columna
        self.grid.addWidget(QLabel(), 7, 2)

        # Crear la tabla para mostrar los datos de detección
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Configurar el número de columnas de la tabla
        self.table.setHorizontalHeaderLabels(["Frame", "ID", "Centroide", "Velocidad", "Bounding Box"])
        self.grid.addWidget(self.table, 7, 1, 2, 1)

        # Configurar la política de estiramiento de las columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Configurar el estiramiento de la cuadrícula
        for i in range(9):
            self.grid.setRowStretch(i, 1)  # Hacer que cada fila use igual cantidad de altura

        self.grid.setColumnStretch(0, 1)  # Hacer que la columna izquierda use la mitad de la anchura actual
        self.grid.setColumnStretch(1, 2)  # Hacer que la columna derecha use el doble de la anchura actual

        self.setLayout(self.grid)

    def pausar_video(self):
        if self.pausa_btn.isChecked():
            self.pausa_btn.setText("Reanudar")
            self.pause_status = True
        else:
            self.pausa_btn.setText("Pausar")
            self.pause_status = False

    def display_frame(self, frame):
        frame_width = frame.shape[1]
        frame_height = frame.shape[0]
        label_width = self.video_label.width()
        label_height = self.video_label.height()

        # Calcula las proporciones de escalado
        scale_w = label_width / frame_width
        scale_h = label_height / frame_height

        scaled_frame = self.convert_cv_qt(frame, label_height, label_width)

        painter = QPainter(scaled_frame)
        pen = QPen(Qt.green)
        pen.setWidth(7)
        painter.setPen(pen)
        painter.end()

        self.video_label.setPixmap(QPixmap.fromImage(scaled_frame))

    def convert_cv_qt(self, image, screen_height, screen_width):
        h, w, _ = image.shape
        scale = min(screen_width / w, screen_height / h)
        nw, nh = int(scale * w), int(scale * h)
        image_resized = cv2.resize(image, (nw, nh))
        image_paded = np.full(shape=[screen_height, screen_width, 3], fill_value=0)
        dw, dh = (screen_width - nw) // 2, (screen_height - nh) // 2
        image_paded[dh:nh + dh, dw:nw + dw, :] = image_resized
        image_paded = cv2.cvtColor(image_paded.astype('uint8'), cv2.COLOR_BGR2RGBA)
        return QImage(image_paded.data, image_paded.shape[1], image_paded.shape[0], QImage.Format_RGBA8888)


    def on_new_detection(self, frame, ids, centroids, velocities, bounding_boxes):
        # Obtener el progreso en lugar del tiempo
        progreso = self.obtener_progreso_por_frame(frame)
        
        # Actualizar el valor de la barra de progreso
        self.progressBar.setValue(progreso)

        self.signal_manager.button_signal.emit(
            self.velocidad_checkbox.isChecked(),
            self.centroide_checkbox.isChecked(),
            self.bounding_boxes_checkbox.isChecked(),
            self.pause_status
        )

        for i in range(len(ids)):
            id = ids[i]
            centroid = centroids[i]
            speed = velocities[i]
            bounding_box = bounding_boxes[i]

            #print(f'Nueva detección: Frame={frame}, ID={id}, centroide={centroid}')

            # Actualiza los datos de velocidad, centroides y bounding boxes
            self.velocidades[id] = speed
            self.centroides[id] = centroid
            self.bounding_boxes[id] = bounding_box

            # Actualizar la tabla con los datos de detección
            self.actualizar_tabla(frame, id, centroid, speed, bounding_box)

        frame = self.tracker.get_current_frame()  # Obtener el frame actualizado desde la clase TrackClass

        self.display_frame(frame)

    def guardar_frame(self):
        frame = self.tracker.get_current_frame()
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(None, "Guardar imagen", "", "Images (*.png *.jpg)")
        if file_path:
            cv2.imwrite(file_path, frame)
            print("Imagen guardada:", file_path)

    def guardar_csv(self):
        pass

    def actualizar_tabla(self, frame, id, centroid, speed, bounding_box):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(frame)))
        self.table.setItem(row, 1, QTableWidgetItem(str(id)))
        self.table.setItem(row, 2, QTableWidgetItem(str(centroid)))
        self.table.setItem(row, 3, QTableWidgetItem(str(speed)))
        self.table.setItem(row, 4, QTableWidgetItem(str(bounding_box)))

    def obtener_progreso_por_frame(self, frame):
        vid_cap = cv2.VideoCapture(self.video_path)
        total_frames = int(vid_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        vid_cap.release()

        progreso = int((frame / total_frames) * 100)

        return progreso


    def importar_video(self):
        file_dialog = QFileDialog()
        video_path, _ = file_dialog.getOpenFileName(None, "Importar Video", "", "Video Files (*.mp4 *.avi *.mkv)")
        if video_path:
            print("Video importado:", video_path)
            self.video_path = video_path
            self.detectar_btn.setEnabled(True)


    def detectar_personas(self):
        print("Detectando personas en el video...")

        self.eliminar_seccion_filtrar_datos()

        hbox = QHBoxLayout()
        self.velocidad_checkbox = QCheckBox("Velocidad")
        self.centroide_checkbox = QCheckBox("Centroide")
        self.bounding_boxes_checkbox = QCheckBox("Bounding Boxes")
        self.velocidad_checkbox.setChecked(False)
        self.centroide_checkbox.setChecked(False)
        self.bounding_boxes_checkbox.setChecked(False)

        hbox.addWidget(self.velocidad_checkbox)
        hbox.addWidget(self.centroide_checkbox)
        hbox.addWidget(self.bounding_boxes_checkbox)

        self.signal_manager.button_signal.connect(self.tracker.handle_checkboxes_updated)

        self.vbox_left.addLayout(hbox)

        self.detection_thread = DetectionThread(self.tracker,
                                                self.video_path,
                                                'app/business/YOLOv7/yolov7.pt',
                                                0,
                                                0.4,
                                                0.5)
        self.detection_thread.start()

        self.detection_thread.finished.connect(self.on_detection_finished)
    

    def on_detection_finished(self):
        print("La detección de personas ha finalizado.")

    def eliminar_seccion_filtrar_datos(self):
        if self.filtrar_label:
            self.filtrar_label.setParent(None)
            self.velocidad_checkbox.setParent(None)
            self.centroide_checkbox.setParent(None)
            self.bounding_boxes_checkbox.setParent(None)