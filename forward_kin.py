import numpy as np

def calculate_tip_xy(angles, lengths):
    """
    Calculates the (x, y) coordinate of the robot tip based on 6 joint angles.
    
    Args:
        angles (list): [p0, p1, p2, p3, p4, p5] in degrees.
            where [pitch, pitch, yaw, roll, yaw, yaw]
        lengths (list): [L1, L2, L3, L4, L5, L6] lengths of each arm segment.
        
    Returns:
        tuple: (x, y) coordinate of the tip relative to the base (0,0).
    """
    
    # 1. Convert degrees to radians
    rads = np.radians(angles)
    
    # Unpack angles for clarity
    # Mapping based on your prompt:
    # p0=Pitch, p1=Pitch, p2=Yaw, p3=Roll, p4=Yaw, p5=Yaw
    th = rads # th[0] is p0, th[1] is p1, etc.
    
    # 2. Define Helper Matrices for Rotation (Rot) and Translation (Trans)
    # We use 4x4 Homogeneous Transformation Matrices
    
    def get_tf(angle_rad, axis, length):
        """
        Creates a transformation matrix: Rotate around 'axis', then translate 'length' along X.
        """
        c = np.cos(angle_rad)
        s = np.sin(angle_rad)
        
        # Rotation part
        if axis == 'x': # Roll
            R = np.array([
                [1, 0,  0, 0],
                [0, c, -s, 0],
                [0, s,  c, 0],
                [0, 0,  0, 1]
            ])
        elif axis == 'y': # Pitch
            R = np.array([
                [ c, 0, s, 0],
                [ 0, 1, 0, 0],
                [-s, 0, c, 0],
                [ 0, 0, 0, 1]
            ])
        elif axis == 'z': # Yaw
            R = np.array([
                [c, -s, 0, 0],
                [s,  c, 0, 0],
                [0,  0, 1, 0],
                [0,  0, 0, 1]
            ])
            
        # Translation part (Assuming link extends along local X-axis)
        T_trans = np.array([
            [1, 0, 0, length],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        # Combine: Rotate first, then Translate
        return R @ T_trans

    # 3. Compute Transformations for each joint
    # Your Mapping:
    # p0 (Pitch -> Y), p1 (Pitch -> Y), p2 (Yaw -> Z)
    # p3 (Roll  -> X), p4 (Yaw   -> Z), p5 (Yaw -> Z)
    
    T0 = get_tf(th[0], 'y', lengths[0])
    T1 = get_tf(th[1], 'y', lengths[1])
    T2 = get_tf(th[2], 'z', lengths[2])
    T3 = get_tf(th[3], 'x', lengths[3]) # 'Row' -> Roll
    T4 = get_tf(th[4], 'z', lengths[4])
    T5 = get_tf(th[5], 'z', lengths[5])

    # 4. Chain the transformations (Forward Kinematics)
    # Global Transform = T0 * T1 * T2 * T3 * T4 * T5
    T_total = T0 @ T1 @ T2 @ T3 @ T4 @ T5
    
    # 5. Extract the position
    # The last column of the 4x4 matrix contains the position [x, y, z, 1]
    tip_position = T_total[:3, 3] # Get x, y, z
    
    x = tip_position[0]
    y = tip_position[1]
    z = tip_position[2]
    
    return x, y, z

# --- Example Usage ---

# Define 6 angles (degrees)
# p0=pitch, p1=pitch, p2=yaw, p3=roll, p4=yaw, p5=yaw
my_angles = [0, 45, 0, 0, 0, 0] 

# Define 6 link lengths (e.g., cm)
my_lengths = [10, 10, 10, 5, 5, 2]

x, y, z = calculate_tip_xy(my_angles, my_lengths)

print(f"Tip X Coordinate: {x:.2f}")
print(f"Tip Y Coordinate: {y:.2f}")
print(f"Tip Z Coordinate: {z:.2f}")