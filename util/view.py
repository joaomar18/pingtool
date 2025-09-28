def scale_value(x: float | int, in_min: float | int, in_max: float | int, out_min: float | int, out_max: float | int):
    return ((x - in_min) * (out_max - out_min)) / ((in_max - in_min)) + out_min
