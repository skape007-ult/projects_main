# CPU-Based ASCII 3D Rasterization Pipeline

![ASCII Rotating Cube](./assets/perfect_cube_loop.gif)

## Overview
This project reconstructs a standard 3D graphics pipeline entirely in software, operating not on pixels but on a grid of ASCII characters. It relies on pure Python with no 3D graphics APIs, GPU acceleration, or external matrix libraries. 

The goal of this experiment is to map the theoretical mathematics of linear transformations and projection directly into functional, interactive code.

### The Rendering Pipeline
The system implements the core stages of modern rendering from scratch:
* **Surface Parameterization:** Mapping 2D coordinate pairs $(u, v)$ to 3D object space.
* **Euler Rotation Matrices:** Sequential rotations $(R_z R_y R_x)$ applied to vertex streams.
* **Back-Face Culling:** Dot-product visibility testing against the camera normal.
* **Perspective Projection:** Foreshortening via mathematical division by depth $(z)$.
* **Z-Buffering:** Resolving occlusion and depth ordering natively.

