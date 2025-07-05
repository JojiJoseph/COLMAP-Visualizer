import numpy as np
import cv2
import plyfile
import tyro
import moderngl
import scipy.spatial.transform as scipy_transform


class PCDRenderer:
    def __init__(self, width: int = 800, height: int = 800):
        self.width = width
        self.height = height
        self.ctx = moderngl.create_standalone_context()
        self.fbo = self.ctx.simple_framebuffer((width, height), components=3)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.vao = None

    def load(self, vertices: np.ndarray, colors: np.ndarray, camera_to_world: np.ndarray = None, intrinsics: np.ndarray = None, textures: np.ndarray = None):
        """Load new point cloud data. vertices and colors: (N, 3) np.float32"""
        assert vertices.shape == colors.shape and vertices.shape[1] == 3
        data = np.hstack([vertices, colors]).astype('f4')
        vbo = self.ctx.buffer(data.tobytes())
        self.prog = self.ctx.program(
            vertex_shader=open("./shaders/pcd.vs.glsl", "r").read(),
            fragment_shader=open("./shaders/pcd.fs.glsl", "r").read(),
        )
        self.prog_camera_frustum = self.ctx.program(
            vertex_shader=open("./shaders/camera_frustum.vs.glsl", "r").read(),
            geometry_shader=open("./shaders/camera_frustum.gs.glsl", "r").read(),
            fragment_shader=open("./shaders/camera_frustum.fs.glsl", "r").read(),
        )

        self.prog_camera_texture = self.ctx.program(
            vertex_shader=open("./shaders/camera_texture.vs.glsl", "r").read(),
            geometry_shader=open("./shaders/camera_texture.gs.glsl", "r").read(),
            fragment_shader=open("./shaders/camera_texture.fs.glsl", "r").read(),
        )

        self.vao = self.ctx.simple_vertex_array(self.prog, vbo, 'in_vert', 'in_color')
        if camera_to_world is not None:
            data1 = camera_to_world[:,:3,:3].reshape((-1,9)).astype('f4')
            data2 = camera_to_world[:,:3,3].reshape((-1,3)).astype('f4')
            data = np.hstack([data1, data2]).astype('f4')
            vbo_frustum = self.ctx.buffer(data.tobytes())
            self.vao_frustum = self.ctx.simple_vertex_array(self.prog_camera_frustum, vbo_frustum, 'in_row1', 'in_row2', 'in_row3', 'in_vert')
        else:
            self.vao_frustum = None
        if camera_to_world is not None and textures is not None:
            data1 = camera_to_world[:,:3,:3].reshape((-1,9)).astype('f4')
            data2 = camera_to_world[:,:3,3].reshape((-1,3)).astype('f4')
            data3 = np.arange(len(textures)).reshape((-1,1)).astype('f4')  # Texture IDs
            data = np.hstack([data1, data2, data3]).astype('f4')
            vbo_camera_texture = self.ctx.buffer(data.tobytes())
            self.vao_camera_texture = self.ctx.simple_vertex_array(self.prog_camera_texture, vbo_camera_texture, 'in_row1', 'in_row2', 'in_row3', 'in_vert','in_texture_id')
            texture_array = self.ctx.texture_array((128, 128, len(textures)), 3, textures.tobytes())
            texture_array.build_mipmaps()
            texture_array.use()

        
        else:
            self.vao_camera_texture = None

    def render(self, K: np.ndarray, viewmat: np.ndarray, near=0.1, far=100.0) -> np.ndarray:
        fx, fy = K[0, 0], K[1, 1]
        cx, cy = K[0, 2], K[1, 2]
        # Enable shader point size
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        proj = np.array([
            [2*fx/self.width, 0, 2*cx/self.width - 1, 0],
            [0, 2*fy/self.height, 2*cy/self.height - 1, 0],
            [0, 0, -(far + near)/(far - near), -2 * far * near / (far - near)],
            [0, 0, -1, 0]
        ], dtype=np.float32)
        flip_yz = np.diag([1, -1, -1, 1]).astype(np.float32)
        proj = proj @ flip_yz @ viewmat
        self.prog['projection'].write(proj.T.astype('f4').tobytes())
        if self.vao_frustum is not None:
            self.prog_camera_frustum['projection'].write(proj.T.astype('f4').tobytes())

        if self.vao_camera_texture is not None:
            self.prog_camera_texture['projection'].write(proj.T.astype('f4').tobytes())

        self.fbo.use()
        self.fbo.clear()
        self.vao.render(moderngl.POINTS)
        if self.vao_frustum is not None:
            self.ctx.wireframe = True  # Enable wireframe mode for frustum
            self.vao_frustum.render(moderngl.POINTS)
            self.ctx.wireframe = False  # Disable wireframe mode after rendering frustum

        if self.vao_camera_texture is not None:
            self.vao_camera_texture.render(moderngl.POINTS)

        rgb = self.fbo.read(components=3)
        img = np.frombuffer(rgb, dtype='u1').reshape((self.height, self.width, 3))
        return np.flipud(img)  # OpenGL origin correction

def load_ply(file_path: str) -> tuple[np.ndarray, np.ndarray]:
    """Load a PLY file and return the vertices and colors."""
    with open(file_path, 'rb') as f:
        ply_data = plyfile.PlyData.read(f)

    vertices = np.array([list(vertex) for vertex in ply_data['vertex'].data])
    colors = np.array([list(vertex)[3:] for vertex in ply_data['vertex'].data])
    
    return vertices[:, :3], colors[:, :3] / 255.0  # Normalize colors to [0, 1]

def main(ply_file: str = "path/to/your/file.ply", height: int = 800, width: int = 800, fov: float= 90):
    camera_matrix = np.array([[width / (2 * np.tan(np.radians(fov) / 2)), 0, width / 2],
                             [0, height / (2 * np.tan(np.radians(fov) / 2)), height / 2],
                             [0, 0, 1]], dtype=np.float32)
    vertices, colors = load_ply(ply_file)

    renderer = PCDRenderer(width=width, height=height)
    renderer.load(vertices, colors)

    cv2.namedWindow('OpenGL Rendered Point Cloud', cv2.WINDOW_NORMAL)

    # Create trackbars for camera parameters
    cv2.createTrackbar("Roll", 'OpenGL Rendered Point Cloud', 0, 180, lambda x: None)
    cv2.createTrackbar("Pitch", 'OpenGL Rendered Point Cloud', 0, 180, lambda x: None)
    cv2.createTrackbar("Yaw", 'OpenGL Rendered Point Cloud', 0, 180, lambda x: None)
    cv2.createTrackbar("X", 'OpenGL Rendered Point Cloud', 0, 1000, lambda x: None)
    cv2.createTrackbar("Y", 'OpenGL Rendered Point Cloud', 0, 1000, lambda x: None)
    cv2.createTrackbar("Z", 'OpenGL Rendered Point Cloud', 0, 1000, lambda x: None)

    # Set min
    cv2.setTrackbarMin("Roll", 'OpenGL Rendered Point Cloud', -180)
    cv2.setTrackbarMin("Pitch", 'OpenGL Rendered Point Cloud', -180)
    cv2.setTrackbarMin("Yaw", 'OpenGL Rendered Point Cloud', -180)
    cv2.setTrackbarMin("X", 'OpenGL Rendered Point Cloud', -1000)
    cv2.setTrackbarMin("Y", 'OpenGL Rendered Point Cloud', -1000)
    cv2.setTrackbarMin("Z", 'OpenGL Rendered Point Cloud', -1000)

    while True:
        # print(vertices_concatenated.shape)
        roll = np.radians(cv2.getTrackbarPos("Roll", 'OpenGL Rendered Point Cloud'))
        pitch = np.radians(cv2.getTrackbarPos("Pitch", 'OpenGL Rendered Point Cloud'))
        yaw = np.radians(cv2.getTrackbarPos("Yaw", 'OpenGL Rendered Point Cloud'))
        x = cv2.getTrackbarPos("X", 'OpenGL Rendered Point Cloud') / 100.0 # Convert cm to m
        y = cv2.getTrackbarPos("Y", 'OpenGL Rendered Point Cloud') / 100.0
        z = cv2.getTrackbarPos("Z", 'OpenGL Rendered Point Cloud') / 100.0
        # Create viewmatrix
        viewmat = np.eye(4, dtype=np.float32)
        rotation = scipy_transform.Rotation.from_euler('xyz', [roll, pitch, yaw], degrees=False)
        viewmat[:3, :3] = rotation.as_matrix()
        viewmat[:3, 3] = [x, y, z]
        
        image = renderer.render(camera_matrix, viewmat, near=0.1, far=100.0)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.imshow('OpenGL Rendered Point Cloud', image)
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):
            break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    tyro.cli(main)
