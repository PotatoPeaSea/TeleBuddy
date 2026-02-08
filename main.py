from ursina import *
from reciever import SerialController


# Initialize the Ursina app
app = Ursina()

# Window Setup
window.title = 'Soldering Simulation'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

# Serial Setup
# Try to auto-connect to the first available port or prompt in console
print("Initializing Serial Controller...")
controller = SerialController()
# Note: This might block for user input in the console if multiple ports are found
# and auto-selection isn't bypassed.
controller.start()

# Scene Setup
ground = Entity(model='plane', scale=(10, 1, 10), color=color.gray.tint(-.2), texture='white_cube', texture_scale=(10,10), collider='box')

# Camera Control
# EditorCamera allows orbiting with Right Mouse Button, Panning with Middle Mouse, and Zooming with Scroll Wheel.
# To use Left Mouse Button for rotation (better for trackpads), we can set specific keys or use a custom script,
# but EditorCamera is the quickest standard way.
editor_camera = EditorCamera()
editor_camera.position = (0, 7, 0) # Start high
editor_camera.rotation = (90, 0, 0) # Look down


# Soldering Iron Representation
# Pivot point for rotation
iron_pivot = Entity(y=1, z=-2)

iron = Entity(parent=iron_pivot, model='cube', scale=(0.2, 0.2, 1.5), color=color.orange, origin_z=-0.5)
iron_tip = Entity(parent=iron, model='cone', scale=0.8, z=0.8, color=color.gray, rotation_x=90)
hot_zone = Entity(parent=iron_tip, model='sphere', scale=0.2, z=0.5, color=color.red, alpha=0.5)

# Solder Target
pcb = Entity(model='plane', scale=(4, 1, 4), color=color.black, texture='white_cube', y=0.01)

# 4x4 Grid of Holes
holes = []
grid_size = 4
spacing = 0.5
start_x = -(grid_size - 1) * spacing / 2
start_z = -(grid_size - 1) * spacing / 2

for r in range(grid_size):
    row_holes = []
    for c in range(grid_size):
        x = start_x + c * spacing
        z = start_z + r * spacing
        # Create hole entity
        hole = Entity(
            parent=pcb,
            model='circle',
            scale=0.15,
            color=color.red, # Initial color
            y=0.02,
            x=x,
            z=z,
            collider='box'
        )
        # Store metadata on the entity itself for easy access
        hole.grid_pos = (r, c)
        hole.is_soldered = False
        row_holes.append(hole)
    holes.append(row_holes)

# Game State
class GameState:
    heat_timer = 0.0

state = GameState()

# Text for debugging
status_text = Text(text='Waiting for Serial...', position=(-0.85, 0.45), scale=1.5)

def update():
    # Get orientation from serial controller
    data = controller.values 
    
    # Check if we have valid serial data (simplified check)
    has_serial = any(data.get(k, 0) != 0 for k in ['pitch', 'roll', 'yaw'])

    # Apply Rotation
    p = data.get('pitch', 0)
    r = data.get('roll', 0)
    y = data.get('yaw', 0)
    
    if has_serial:
        iron_pivot.rotation_x = p
        iron_pivot.rotation_z = r
        iron_pivot.rotation_y = y
    
    # Keyboard fallback / WASD Control for testing
    speed = 50 * time.dt
    if held_keys['w']: iron_pivot.rotation_x += speed
    if held_keys['s']: iron_pivot.rotation_x -= speed
    if held_keys['a']: iron_pivot.rotation_z += speed
    if held_keys['d']: iron_pivot.rotation_z -= speed
    if held_keys['q']: iron_pivot.rotation_y -= speed
    if held_keys['e']: iron_pivot.rotation_y += speed

    # Simulation Logic
    # Check distance between iron tip hot zone and holes
    tip_pos = hot_zone.world_position
    
    # Reset heat timer by default, will accumulate if touching *any* unsoldered hole
    touching_any = False

    for r in range(grid_size):
        for c in range(grid_size):
            hole = holes[r][c]
            if hole.is_soldered:
                continue

            pad_pos = hole.world_position
            distance = distance_2d(tip_pos, pad_pos) # planar distance
            height_diff = abs(tip_pos.y - pad_pos.y)

            # Check collision
            if distance < 0.15 and height_diff < 0.2:
                touching_any = True
                iron_tip.color = color.red
                
                # Instant soldering on contact as per request ("change color... on initial contact")
                # Or we can keep the heat timer. The prompt said "on initial contact change the color".
                # Let's start with instant for responsiveness, or a very short timer.
                # User asked: "when the soldering iron tip comes in xyz contact to the holes change the color to the holes from red to green on initial contact"
                
                hole.color = color.green
                hole.is_soldered = True
                print(f"Contact with hole [{r}, {c}]")
                
                # Optional: Add a solder blob visual if needed, but color change was specific request.
                
    if not touching_any:
        iron_tip.color = color.gray
        state.heat_timer = 0.0

    # Update Status Text
    status_text.text = f"Pitch: {iron_pivot.rotation_x:.1f}\nRoll: {iron_pivot.rotation_z:.1f}\nYaw: {iron_pivot.rotation_y:.1f}"

def distance_2d(p1, p2):
    return ((p1.x - p2.x)**2 + (p1.z - p2.z)**2)**0.5

def input(key):
    if key == 'escape':
        controller.stop()
        app.quit()

# Run
app.run()
