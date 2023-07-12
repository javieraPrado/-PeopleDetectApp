import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QCheckBox
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from app.business.detection_manager import DetectionManager

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        #Configuración de la ventana del video y los componentes
        self.setWindowTitle('Video Player')
        self.resize(800, 600)

        #Crear reproductor de video y botón de reproducción
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(400, 300)
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_video)

        #Configurar el diseño de la interfaz
        vbox = QVBoxLayout()
        vbox.addWidget(self.video_widget)
        vbox.addWidget(self.play_button)
        self.setLayout(vbox)

        #Configurar reproductor multimedia
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.stateChanged.connect(self.handle_state_changed)

    def set_video(self, video_path):
        # Configura el video para reproducir en el reproductor multimedia
        video_url = QUrl.fromLocalFile(video_path)
        video_content = QMediaContent(video_url)
        self.media_player.setMedia(video_content)

        # Anteriormente se reproducía el video inmediatamente
        # self.media_player.play()

        # Ahora el botón de reproducción se habilita pero no se reproduce el video automáticamente
        self.play_button.setEnabled(True)

    def play_video(self):
        #Evento del clic del botón de reproducción
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def handle_state_changed(self, state):
        #Maneja el evento de "pause" o "play" en el botón de reproducción
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("Pause")
        elif state == QMediaPlayer.PausedState or state == QMediaPlayer.StoppedState:
            self.play_button.setText("Play")

class DetectionThread(QThread):
    finished = pyqtSignal()

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        detection_manager = DetectionManager(self.video_path)
        detection_manager.detect_people()
        self.finished.emit()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        #Configuración de la ventana de la interfaz y los componentes
        self.setWindowTitle('Sistema de detección peatonal')
        self.resize(800, 600)

        icono = QIcon("icono.png")
        self.setWindowIcon(icono)
        self.video_path = None
        self.filtrar_label = None
        self.velocidad_checkbox = None
        self.centroide_checkbox = None
        self.bounding_boxes_checkbox = None
        self.vbox = QVBoxLayout()
        self.vbox.setSpacing(20)

        titulo_label = QLabel("BIENVENID@")
        font = QFont("Calibri Light", 20, QFont.Bold)
        titulo_label.setFont(font)
        titulo_label.setAlignment(Qt.AlignCenter)
        self.vbox.addWidget(titulo_label)

        hbox = QHBoxLayout()
        self.importar_btn = QPushButton("Importar Video")
        self.importar_btn.clicked.connect(self.importar_video)
        hbox.addWidget(self.importar_btn)

        self.detectar_btn = QPushButton("Detectar Personas")
        self.detectar_btn.clicked.connect(self.detectar_personas)
        self.detectar_btn.setEnabled(False)
        hbox.addWidget(self.detectar_btn)

        self.vbox.addLayout(hbox)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.vbox.addWidget(self.video_label)

        self.video_player = VideoPlayer()
        self.vbox.addWidget(self.video_player)

        self.setLayout(self.vbox)

    def importar_video(self):
        #Abre cuadro de diálogo para importar un video
        file_dialog = QFileDialog()
        video_path, _ = file_dialog.getOpenFileName(None, "Importar Video", "", "Video Files (*.mp4 *.avi *.mkv)")
        if video_path:
            print("Video importado:", video_path)
            self.video_path = video_path
            self.video_player.set_video(video_path)
            self.detectar_btn.setEnabled(True)
            video_name = QUrl.fromLocalFile(video_path).fileName()
            self.video_label.setText(f"Video seleccionado: {video_name}")

            # Eliminar la sección "Filtrar Datos de Salida" si existe
            self.eliminar_seccion_filtrar_datos()

    def detectar_personas(self):
        print("Detectando personas en el video...")

        # Eliminar la sección "Filtrar Datos de Salida" si existe
        self.eliminar_seccion_filtrar_datos()

        # Agregar la sección "Filtrar Datos de Salida"
        self.filtrar_label = QLabel("Filtrar Datos de Salida")
        self.vbox.addWidget(self.filtrar_label)

        # Agregar las opciones de filtrado
        hbox = QHBoxLayout()
        self.velocidad_checkbox = QCheckBox("Velocidad")
        self.centroide_checkbox = QCheckBox("Centroide")
        self.bounding_boxes_checkbox = QCheckBox("Bounding Boxes")

        hbox.addWidget(self.velocidad_checkbox)
        hbox.addWidget(self.centroide_checkbox)
        hbox.addWidget(self.bounding_boxes_checkbox)

        self.vbox.addLayout(hbox)

        # recupera el camino al video que fue seleccionado
        video_path = self.video_path

        # crea e inicia el hilo de detección
        self.detection_thread = DetectionThread(video_path)
        self.detection_thread.finished.connect(self.on_detection_finished)
        self.detection_thread.start()

    def eliminar_seccion_filtrar_datos(self):
        #Elimina la sección de opciones de filtrado de datos, SI SE IMPORTA UN VIDEO NUEVO 
        if self.filtrar_label:
            self.filtrar_label.setParent(None)
            self.velocidad_checkbox.setParent(None)
            self.centroide_checkbox.setParent(None)
            self.bounding_boxes_checkbox.setParent(None)

    def on_detection_finished(self):
        #maneja lo que debes hacer cuando la detección se complete
        print("La detección de personas ha finalizado.")


"""def detect_people(self):
        # recupera el camino al video que fue seleccionado
        video_path = self.get_video_path()

        # crea una instancia de DetectionManager y llama a detect_people
        detection_manager = DetectionManager(video_path)
        detection_manager.detect_people()"""
        