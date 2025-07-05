#version 330
layout(points) in;
layout(triangle_strip, max_vertices = 10) out;
uniform float rect_size = 0.1; // Rectangle half-size
uniform mat4 projection;

in vec3 row1[];
in vec3 row2[];
in vec3 row3[];
flat in int texture_id[];

out vec2 texcoord;
flat out int out_texture_id;

mat4 getExtrinsicMatrix() {
    return mat4(
        row1[0].x, row2[0].x, row3[0].x, 0.0,
        row1[0].y, row2[0].y, row3[0].y, 0.0,
        row1[0].z, row2[0].z, row3[0].z, 0.0,
        0.0,    0.0,    0.0, 1.0
    );
}

void main() {
    vec4 center = gl_in[0].gl_Position;
    float s = rect_size;

    // Four corners of the rectangle in NDC (screen-aligned)
    vec4 offsets[4] = vec4[](
        projection * getExtrinsicMatrix() * vec4(-s, -s, rect_size, 0),
        projection * getExtrinsicMatrix() * vec4( s, -s, rect_size, 0),
        projection * getExtrinsicMatrix() * vec4(-s,  s, rect_size, 0),
        projection * getExtrinsicMatrix() * vec4( s,  s, rect_size, 0)
    );

    for (int i = 0; i < 4; ++i) {
        gl_Position = center + offsets[i];
        out_texture_id = texture_id[0];
        texcoord = vec2((i % 2), (i / 2));
        EmitVertex();
    }

    EndPrimitive();

}