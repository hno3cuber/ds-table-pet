def scaled_size(orig_w: int, orig_h: int, scale: float) -> tuple[int, int]:
    return (max(1, round(orig_w * scale)), max(1, round(orig_h * scale)))


def scaled_size_xy(orig_w: int, orig_h: int, scale_x: float, scale_y: float) -> tuple[int, int]:
    """宽高独立缩放：自由宽高比。"""
    return (max(1, round(orig_w * scale_x)), max(1, round(orig_h * scale_y)))


def scale_from_corner_drag(
    start_vec: tuple[int, int],
    cursor_vec: tuple[int, int],
    start_scale: float,
    min_scale: float = 0.1,
) -> float:
    """角点等比缩放（按住 Shift 时用）：光标在「角点→对角锚点」方向上的投影比例决定缩放。

    start_vec  — press 瞬间光标到对角锚点的向量（固定基准）
    cursor_vec — 当前光标到对角锚点的向量
    返回值 = start_scale × (cursor 在 start 方向上的投影 / start 长度²)

    - 不动 → ratio=1（不变）
    - 远离锚点 → ratio>1（放大）
    - 靠近锚点 → 0<ratio<1（缩小）
    - 越过锚点 → ratio<0（钳制到 min_scale）
    """
    denom = start_vec[0] ** 2 + start_vec[1] ** 2
    if denom < 1.0:
        return max(min_scale, start_scale)
    ratio = (cursor_vec[0] * start_vec[0] + cursor_vec[1] * start_vec[1]) / denom
    return max(min_scale, start_scale * ratio)


def corner_resize_size(corner: int, anchor, cursor, min_w: int = 1, min_h: int = 1) -> tuple[int, int]:
    """PPT 式角点自由缩放：对角锚点固定，新窗口宽高由光标独立决定。

    corner 0=左上 1=右上 2=左下 3=右下；anchor 为对角锚点的全局坐标。
    光标越靠近锚点窗口越小，越远离越大；宽高各自跟随光标，不锁比例。
    光标越过锚点时该方向被钳制到最小像素。
    """
    ax, ay = anchor
    cx, cy = cursor
    # 水平：左列角点（0/2）的光标在锚点左侧，右列（1/3）在右侧
    if corner in (0, 2):
        w = ax - cx
    else:
        w = cx - ax
    # 垂直：上行角点（0/1）的光标在锚点上方，下行（2/3）在下方
    if corner in (0, 1):
        h = ay - cy
    else:
        h = cy - ay
    return max(min_w, w), max(min_h, h)


def anchor_and_topleft(corner: int, old_top_left, old_size, new_size):
    """PPT 式角点缩放的对角锚定：返回 (anchor_global, new_top_left)。

    corner 0=左上 1=右上 2=左下 3=右下。
    对角顶点固定不动，新窗口矩形贴着锚点放置。
    """
    ox, oy = old_top_left
    ow, oh = old_size
    nw, nh = new_size
    anchors = {
        0: (ox + ow, oy + oh),   # 锚=右下
        1: (ox, oy + oh),        # 锚=左下
        2: (ox + ow, oy),        # 锚=右上
        3: (ox, oy),             # 锚=左上
    }
    ax, ay = anchors[corner]
    topleft = {
        0: (ax - nw, ay - nh),
        1: (ax, ay - nh),
        2: (ax - nw, ay),
        3: (ax, ay),
    }[corner]
    return (ax, ay), topleft
