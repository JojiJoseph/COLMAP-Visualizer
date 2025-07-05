#version 330
in vec2 texcoord;
flat in int out_texture_id;
out vec4 fragColor;

uniform sampler2DArray texture_array;

void main() {
    fragColor = vec4(texture(texture_array, vec3(texcoord, out_texture_id)).rgb,1.0);
}