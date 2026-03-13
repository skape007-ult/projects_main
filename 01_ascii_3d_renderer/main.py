import pygame
import math
import sys

pygame.init()
pygame.key.set_repeat(0)

# ---------------- WINDOW ----------------
WIDTH = 1200
HEIGHT = 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Rotating Cube")

clock = pygame.time.Clock()

font_size = 12
font = pygame.font.SysFont("Courier", font_size)
debug_font = pygame.font.SysFont("Courier", 16)

cols = WIDTH // font_size
rows = HEIGHT // font_size

# ---------------- CAMERA ----------------
cam_x, cam_y, cam_z = 0, 0, -150
zoom = 80

# ---------------- ROTATION ----------------
A = B = C = 0
rot_speed_x = 0.02
rot_speed_y = 0.02
rot_speed_z = 0.01

# ---------------- MATH ----------------
def rotate_point(i, j, k):
    # Rotate X
    y = j * math.cos(A) - k * math.sin(A)
    z = j * math.sin(A) + k * math.cos(A)
    j, k = y, z

    # Rotate Y
    x = i * math.cos(B) + k * math.sin(B)
    z = -i * math.sin(B) + k * math.cos(B)
    i, k = x, z

    # Rotate Z
    x = i * math.cos(C) - j * math.sin(C)
    y = i * math.sin(C) + j * math.cos(C)

    return x, y, k


def normalize(v):
    l = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    return (v[0]/l, v[1]/l, v[2]/l)


def dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


# ---------------- DRAW ----------------
def drawCube(size, zBuffer, charBuffer):

    step = 1
    view_dir = (0, 0, -1)

    # One fixed character per face
    faces = [
        ((0, 0, -1), '@', lambda x,y: (x, y, -size)),  # front
        ((1, 0, 0),  '|', lambda x,y: (size, y, x)),   # right
        ((-1, 0, 0), '~', lambda x,y: (-size, y, -x)), # left
        ((0, 0, 1),  '#', lambda x,y: (-x, y, size)),  # back
        ((0, -1, 0), ';', lambda x,y: (x, -size, -y)), # bottom
        ((0, 1, 0),  '+', lambda x,y: (x, size, y)),   # top
    ]

    for normal, char, surface in faces:

        # Rotate normal
        nx, ny, nz = rotate_point(*normal)
        n = normalize((nx, ny, nz))

        # Back-face culling
        if dot(n, view_dir) <= 0:
            continue

        # Compute stable face depth using center
        cx_obj = normal[0] * size
        cy_obj = normal[1] * size
        cz_obj = normal[2] * size

        cx, cy, cz = rotate_point(cx_obj, cy_obj, cz_obj)

        cx -= cam_x
        cy -= cam_y
        cz -= cam_z

        if cz <= 0:
            continue

        face_depth = cz

        for cubeX in range(-size, size, step):
            for cubeY in range(-size, size, step):

                i, j, k = surface(cubeX, cubeY)

                x, y, z = rotate_point(i, j, k)

                x -= cam_x
                y -= cam_y
                z -= cam_z

                if z <= 0:
                    continue

                xp = int(cols/2 + zoom * x / z)
                yp = int(rows/2 - zoom * y / z)

                if 0 <= xp < cols and 0 <= yp < rows:
                    if face_depth < zBuffer[yp][xp] or zBuffer[yp][xp] == 0:
                        zBuffer[yp][xp] = face_depth
                        charBuffer[yp][xp] = char


def draw_debug_info():
    info_lines = [
        f"A: {A:.2f}  B: {B:.2f}  C: {C:.2f}",
        f"Rot Speed X: {rot_speed_x:.4f}",
        f"Rot Speed Y: {rot_speed_y:.4f}",
        f"Rot Speed Z: {rot_speed_z:.4f}",
        f"Cam X: {cam_x}",
        f"Cam Y: {cam_y}",
        f"Cam Z: {cam_z}",
        f"Zoom: {zoom}",
        f"FPS: {int(clock.get_fps())}",
    ]

    y_offset = 10
    for line in info_lines:
        text = debug_font.render(line, True, (0, 255, 0))
        screen.blit(text, (10, y_offset))
        y_offset += 20

# ---------------- MAIN LOOP ----------------

running = True
paused = False
show_debug = True
tab_pressed = False

while running:
    clock.tick(60)
    screen.fill((0, 0, 0))

    keys = pygame.key.get_pressed()

    # -------- ROTATION SPEED CONTROL --------
    if keys[pygame.K_q]:
        rot_speed_x += 0.001
    if keys[pygame.K_a]:
        rot_speed_x -= 0.001

    if keys[pygame.K_w]:
        rot_speed_y += 0.001
    if keys[pygame.K_s]:
        rot_speed_y -= 0.001

    if keys[pygame.K_e]:
        rot_speed_z += 0.001
    if keys[pygame.K_d]:
        rot_speed_z -= 0.001

    # -------- CAMERA MOVEMENT --------
    if keys[pygame.K_LEFT]:
        cam_x += 2
    if keys[pygame.K_RIGHT]:
        cam_x -= 2
    if keys[pygame.K_UP]:
        cam_y -= 2
    if keys[pygame.K_DOWN]:
        cam_y += 2

    if keys[pygame.K_PAGEUP]:
        cam_z += 5
    if keys[pygame.K_PAGEDOWN]:
        cam_z -= 5

    # -------- ZOOM --------
    if keys[pygame.K_z]:
        zoom += 1
    if keys[pygame.K_x]:
        zoom -= 1
        if zoom < 10:
            zoom = 10

    # -------- BUFFERS --------
    zBuffer = [[0 for _ in range(cols)] for _ in range(rows)]
    charBuffer = [[' ' for _ in range(cols)] for _ in range(rows)]

    drawCube(20, zBuffer, charBuffer)

    # -------- RENDER --------
    for y in range(rows):
        for x in range(cols):
            ch = charBuffer[y][x]
            if ch != ' ':
                text = font.render(ch, True, (0, 180, 255))
                screen.blit(text, (x * font_size, y * font_size))

    # -------- UPDATE ROTATION --------
    if not paused:
        A += rot_speed_x
        B += rot_speed_y
        C += rot_speed_z

    # -------- EVENTS --------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused

            if event.key == pygame.K_TAB and not tab_pressed:
                show_debug = not show_debug
                tab_pressed = True

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_TAB:
                tab_pressed = False

    if show_debug:
        draw_debug_info()
    pygame.display.flip()

pygame.quit()
sys.exit()
