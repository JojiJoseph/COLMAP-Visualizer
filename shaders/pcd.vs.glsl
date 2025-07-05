#version 330
in vec3 in_vert;
in vec3 in_color;
uniform mat4 projection;
out vec3 color;
void main() {
    gl_Position = projection * vec4(in_vert, 1.0);
    color = in_color;
}
