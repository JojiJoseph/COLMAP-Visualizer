from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QStatusBar, QMenuBar, QWidget, QVBoxLayout
import sys
from PyQt6.QtCore import QTimer
import numpy as np
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QLabel
import tyro
import moderngl
import scipy.spatial.transform as scipy_transform
import pycolmap_scene_manager as pycolmap
from pcd_visualizer import PCDRenderer
from PyQt6.QtWidgets import QSlider, QHBoxLayout
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self, colmap_dir: str):
        super().__init__()
        self.setWindowTitle("PyQt6 Timer Application")
        self.colmap_project = pycolmap.SceneManager(colmap_dir)
        self.colmap_project.load()

        # Menubar
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # Status bar
        statusbar = QStatusBar(self)
        self.setStatusBar(statusbar)
        statusbar.showMessage("Ready")

        # Central widget with timer label and image
        central_widget = QWidget(self)
        layout = QVBoxLayout()

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.renderer = PCDRenderer(width=800, height=600)
        self.renderer.load(self.colmap_project.points3D, self.colmap_project.point3D_colors / 255.0,)

        # Sliders for x, y, z
        self.slider_x = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_x.setRange(-1000, 1000)
        self.slider_x.setValue(0)
        self.slider_x.setTickInterval(100)
        self.slider_x.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_x.setToolTip("View X (cm)")

        self.slider_y = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_y.setRange(-1000, 1000)
        self.slider_y.setValue(0)
        self.slider_y.setTickInterval(100)
        self.slider_y.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_y.setToolTip("View Y (cm)")

        self.slider_z = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_z.setRange(-1000, 1000)
        self.slider_z.setValue(0)
        self.slider_z.setTickInterval(100)
        self.slider_z.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_z.setToolTip("View Z (cm)")

        # Sliders for roll, pitch, yaw
        self.slider_roll = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_roll.setRange(-180, 180)
        self.slider_roll.setValue(0)
        self.slider_roll.setTickInterval(30)
        self.slider_roll.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_roll.setToolTip("Roll (deg)")

        self.slider_pitch = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_pitch.setRange(-180, 180)
        self.slider_pitch.setValue(0)
        self.slider_pitch.setTickInterval(30)
        self.slider_pitch.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_pitch.setToolTip("Pitch (deg)")

        self.slider_yaw = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_yaw.setRange(-180, 180)
        self.slider_yaw.setValue(0)
        self.slider_yaw.setTickInterval(30)
        self.slider_yaw.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_yaw.setToolTip("Yaw (deg)")

        rot_slider_layout = QHBoxLayout()
        rot_slider_layout.addWidget(QLabel("Roll:"))
        rot_slider_layout.addWidget(self.slider_roll)
        rot_slider_layout.addWidget(QLabel("Pitch:"))
        rot_slider_layout.addWidget(self.slider_pitch)
        rot_slider_layout.addWidget(QLabel("Yaw:"))
        rot_slider_layout.addWidget(self.slider_yaw)
        layout.addLayout(rot_slider_layout)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("X:"))
        slider_layout.addWidget(self.slider_x)
        slider_layout.addWidget(QLabel("Y:"))
        slider_layout.addWidget(self.slider_y)
        slider_layout.addWidget(QLabel("Z:"))
        slider_layout.addWidget(self.slider_z)
        layout.addLayout(slider_layout)

        # Timer setup
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(10)  # 100 ms interval
    def update_timer(self):
        self.render_point_cloud()

    def render_point_cloud(self):
        K = np.array([[1000, 0, 320],
                          [0, 1000, 240],
                          [0, 0, 1]], dtype=np.float32)
        # Create a random 2D numpy array (grayscale image)
        viewmat = np.eye(4, dtype=np.float32)
        viewmat[0, 3] = self.slider_x.value() / 100.0  # Convert cm to m
        viewmat[1, 3] = self.slider_y.value() / 100.0
        viewmat[2, 3] = self.slider_z.value() / 100.0

        roll = np.radians(self.slider_roll.value())
        pitch = np.radians(self.slider_pitch.value())
        yaw = np.radians(self.slider_yaw.value())
        rotation = scipy_transform.Rotation.from_euler('xyz', [roll, pitch, yaw], degrees=False)
        viewmat[:3, :3] = rotation.as_matrix()

        arr = self.renderer.render(K, viewmat=viewmat, near=0.1, far=100.0).copy()
        # Convert to QImage
        qimg = QImage(arr.data, arr.shape[1], arr.shape[0], arr.strides[0], QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        scaled_pixmap = pixmap.scaled(
        self.image_label.size(),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
)

        self.image_label.setPixmap(scaled_pixmap)

def main(colmap_dir: str):
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            background-color: #202124;
            color: #E8EAED;
            font-family: 'Segoe UI', sans-serif;
            font-size: 11pt;
        }
        QSlider::handle:horizontal {
            background: #1a73e8;
        }
        QLabel {
            font-weight: bold;
        }
    """)
    
    window = MainWindow(colmap_dir)
    window.show()
    sys.exit(app.exec())



if __name__ == "__main__":
    tyro.cli(main)
