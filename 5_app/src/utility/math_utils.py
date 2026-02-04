import pymel.core as pm


def get_distance(point_a: pm.dt.Vector, point_b: pm.dt.Vector) -> float:
    vec_a = pm.datatypes.Vector(point_a)
    vec_b = pm.datatypes.Vector(point_b)
    return (vec_b - vec_a).length()

def get_distance_between_transforms(transform_a: pm.nt.Transform, transform_b: pm.nt.Transform) -> float:
    pos_a = pm.xform(transform_a, q=True, ws=True, t=True)
    pos_b = pm.xform(transform_b, q=True, ws=True, t=True)
    return get_distance(pos_a, pos_b)

def get_midpoint(point_a: pm.dt.Vector, point_b: pm.dt.Vector) -> pm.datatypes.Vector:
    vec_a = pm.datatypes.Vector(point_a)
    vec_b = pm.datatypes.Vector(point_b)
    midpoint = (vec_a + vec_b) / 2
    return midpoint

def get_midpoint_between_transforms(transform_a: pm.nt.Transform, transform_b: pm.nt.Transform) -> pm.datatypes.Vector:
    pos_a = pm.xform(transform_a, q=True, ws=True, t=True)
    pos_b = pm.xform(transform_b, q=True, ws=True, t=True)
    return get_midpoint(pos_a, pos_b)

"""def calculate_pole_vector(start_pos: pm.dt.Vector, end_pos: pm.dt.Vector, mid_pos: pm.dt.Vector, scale=1.0) -> pm.datatypes.Vector:
    start_vec = pm.datatypes.Vector(start_pos)
    end_vec = pm.datatypes.Vector(end_pos)
    mid_vec = pm.datatypes.Vector(mid_pos)

    start_to_end = end_vec - start_vec
    start_to_mid = mid_vec - start_vec

    projection_length = start_to_mid * start_to_end.normal()
    projection_vec = start_to_end.normal() * projection_length

    perpendicular_vec = start_to_mid - projection_vec
    pole_vector = perpendicular_vec.normal() * scale

    return pole_vector + mid_vec"""

