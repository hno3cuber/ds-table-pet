def scaled_size(orig_w: int, orig_h: int, scale: float) -> tuple[int, int]:
    return (max(1, round(orig_w * scale)), max(1, round(orig_h * scale)))


def scale_from_drag(orig_w: int, drag_dx: int, current_scale: float, min_scale: float = 0.3) -> float:
    return max(min_scale, current_scale + drag_dx / orig_w)
