#version 330
in vec3 in_row1;
in vec3 in_row2;
in vec3 in_row3;
in vec3 in_vert;
uniform mat4 projection;
out vec3 row1;
out vec3 row2;
out vec3 row3;
void main() {
    gl_Position = projection * vec4(in_vert, 1.0);
    //gl_PointSize = 5.0; // Size of the frustum points
    row1 = in_row1;
    row2 = in_row2;
    row3 = in_row3;
}
