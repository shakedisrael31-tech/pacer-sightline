"""Generate a Dimensions.com-style side-view female runner as SVG paths.

Local coordinates are centimetres, y up, ground at y=0, reference stature 165 cm.
The page flips y with a transform, so everything here stays in body units.
"""
import math

OUT = "#161616"


def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def poly(points):
    return "M" + " L".join(f"{fmt(x)} {fmt(y)}" for x, y in points) + " Z"


def smooth_closed(points, tension=1.0):
    """Catmull-Rom spline through points, returned as a closed cubic Bezier path."""
    n = len(points)
    d = f"M{fmt(points[0][0])} {fmt(points[0][1])}"
    for i in range(n):
        p0, p1, p2, p3 = points[(i - 1) % n], points[i], points[(i + 1) % n], points[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        d += f" C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p2[0])} {fmt(p2[1])}"
    return d + " Z"


def smooth_open(points, tension=1.0):
    n = len(points)
    d = f"M{fmt(points[0][0])} {fmt(points[0][1])}"
    for i in range(n - 1):
        p0 = points[max(i - 1, 0)]
        p1, p2 = points[i], points[i + 1]
        p3 = points[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        d += f" C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p2[0])} {fmt(p2[1])}"
    return d


def capsule(a, ra, b, rb, steps=10):
    """Tapered capsule between joint a (radius ra) and joint b (radius rb)."""
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    base = math.atan2(uy, ux)
    pts = []
    for i in range(steps + 1):  # cap around b
        t = base + math.pi / 2 - math.pi * i / steps
        pts.append((bx + rb * math.cos(t), by + rb * math.sin(t)))
    for i in range(steps + 1):  # cap around a
        t = base - math.pi / 2 - math.pi * i / steps
        pts.append((ax + ra * math.cos(t), ay + ra * math.sin(t)))
    return poly(pts)


def ellipse_on_axis(a, b, t, offset, along, across, steps=24):
    """Muscle bulge: ellipse centred at fraction t along a->b, pushed sideways by offset."""
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    nx, ny = -uy, ux
    cx, cy = ax + ux * L * t + nx * offset, ay + uy * L * t + ny * offset
    pts = []
    for i in range(steps):
        th = 2 * math.pi * i / steps
        pa, pc = along * math.cos(th), across * math.sin(th)
        pts.append((cx + ux * pa + nx * pc, cy + uy * pa + ny * pc))
    return poly(pts)


def cross_line(a, b, t, half):
    """Short line across a limb at fraction t (clothing hem)."""
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    nx, ny = -uy, ux
    cx, cy = ax + ux * L * t, ay + uy * L * t
    return f"M{fmt(cx + nx * half)} {fmt(cy + ny * half)} L{fmt(cx - nx * half)} {fmt(cy - ny * half)}"


def shoe(heel, toe):
    """Running shoe outline in a frame running from heel-bottom to toe-bottom."""
    hx, hy = heel
    tx, ty = toe
    L = math.hypot(tx - hx, ty - hy)
    ux, uy = (tx - hx) / L, (ty - hy) / L
    nx, ny = -uy, ux

    def P(a, b):
        return (hx + ux * a + nx * b, hy + uy * a + ny * b)

    outline = [P(-1.2, 2.2), P(0.5, 0), P(L * 0.5, -0.3), P(L - 2.5, 0.2), P(L + 0.4, 1.8),
               P(L - 0.6, 4.2), P(L * 0.62, 7.6), P(L * 0.36, 10.0), P(L * 0.14, 10.6), P(-0.4, 8.6)]
    sole = smooth_open([P(-0.9, 2.6), P(L * 0.5, 2.4), P(L - 0.4, 2.9)])
    laces = " ".join(cross_line(P(L * 0.38, 9.2), P(L * 0.62, 7.0), t, 0.9) for t in (0.2, 0.55, 0.9))
    return smooth_closed(outline, 0.9), sole, laces


# ---- joints (cm, y up) ------------------------------------------------------
EYE = (12.6, 154.4)                     # 0.936 x 165 cm

near_hip, near_knee, near_ankle = (1.5, 85.0), (32.0, 64.0), (24.0, 27.0)
far_hip, far_knee, far_ankle = (-2.0, 85.0), (-15.0, 50.0), (-36.0, 17.0)
near_sh, near_el, near_wr = (2.5, 133.0), (-19.0, 111.5), (-3.0, 95.0)
far_sh, far_el, far_wr = (4.0, 133.0), (12.0, 103.5), (24.0, 123.5)

# ---- shapes -----------------------------------------------------------------
torso = smooth_closed([
    (-0.6, 143.2), (-2.6, 139.6), (-6.6, 135.0), (-8.6, 127.5), (-8.8, 117), (-7.2, 107), (-8.4, 99),
    (-11.0, 91), (-10.6, 83.5), (-6.5, 78.5), (0.5, 77.0), (6.5, 78.6), (9.4, 84),
    (10.0, 92), (9.4, 100), (10.4, 107.5), (13.6, 114.5), (13.4, 121.5), (11.2, 129.0),
    (8.4, 135.6), (7.4, 139.8), (7.2, 143.6),
])
head = smooth_closed([
    (-0.8, 146.5), (-3.8, 151.5), (-4.2, 157.5), (-1.2, 162.8), (4.6, 165.2), (10.6, 163.0),
    (13.4, 158.8), (14.3, 156.0), (14.0, 154.4), (15.9, 151.6), (14.4, 150.3), (14.8, 148.7),
    (14.2, 147.3), (14.1, 145.6), (12.0, 144.0), (8.4, 144.4), (5.6, 145.2),
], 0.9)
ponytail = smooth_closed([
    (-0.6, 161.6), (-6.0, 160.6), (-11.2, 157.4), (-15.2, 151.2), (-14.6, 146.8),
    (-11.0, 149.6), (-6.6, 153.2), (-3.2, 155.0),
])
hairline = smooth_open([(11.6, 162.4), (8.8, 159.2), (6.2, 156.6), (4.9, 155.2)]) + " " + smooth_open([(2.4, 150.4), (1.2, 148.6), (0.2, 146.8)])
band = "M-3.3 156.8 L-1.4 160.2"
ear = smooth_closed([(2.6, 154.6), (4.4, 154.2), (4.6, 151.6), (3.2, 150.2), (2.2, 151.6)])
top_hem = smooth_open([(-8.5, 112.0), (1.5, 110.2), (11.6, 109.4)])
waistband = smooth_open([(-7.6, 100.4), (1.2, 99.0), (9.5, 98.6)])

near_leg = [capsule(near_hip, 8.2, near_knee, 5.4), capsule(near_knee, 5.4, near_ankle, 3.2),
            ellipse_on_axis(near_knee, near_ankle, 0.32, -1.6, 12.0, 5.0),
            ellipse_on_axis(near_hip, near_knee, 0.45, 1.2, 13.0, 7.6)]
far_leg = [capsule(far_hip, 8.0, far_knee, 5.3), capsule(far_knee, 5.3, far_ankle, 3.1),
           ellipse_on_axis(far_knee, far_ankle, 0.32, -1.6, 12.0, 4.8),
           ellipse_on_axis(far_hip, far_knee, 0.45, 1.2, 12.5, 7.3)]
near_arm = [capsule(near_sh, 4.6, near_el, 3.2), capsule(near_el, 3.2, near_wr, 2.4),
            ellipse_on_axis(near_sh, near_el, 0.22, 0.0, 8.0, 5.0),
            ellipse_on_axis(near_wr, near_el, -0.12, 0.0, 4.6, 3.6)]
far_arm = [capsule(far_sh, 4.4, far_el, 3.1), capsule(far_el, 3.1, far_wr, 2.3),
           ellipse_on_axis(far_sh, far_el, 0.22, 0.0, 7.6, 4.8),
           ellipse_on_axis(far_wr, far_el, -0.12, 0.0, 4.4, 3.4)]

near_shoe, near_sole, near_laces = shoe((19.5, 22.6), (45.0, 22.0))
far_shoe, far_sole, far_laces = shoe((-42.5, 12.0), (-17.5, 0.0))

near_shorts = cross_line(near_hip, near_knee, 0.42, 7.6)
glute_crease = smooth_open([(-9.6, 82.6), (-5.6, 80.2), (-1.0, 80.6)])
far_shorts = cross_line(far_hip, far_knee, 0.42, 7.4)


def layer(shapes, fill, details=()):
    """Unified silhouette: thick dark pass, then fill pass on top, then interior lines."""
    s = '<g>'
    s += ''.join(f'<path d="{d}" fill="{OUT}" stroke="{OUT}" stroke-width="2.3" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>' for d in shapes)
    s += ''.join(f'<path d="{d}" fill="{fill}"/>' for d in shapes)
    s += ''.join(f'<path d="{d}" fill="none" stroke="{OUT}" stroke-width="0.8" stroke-linecap="round" vector-effect="non-scaling-stroke"/>' for d in details)
    return s + '</g>'


FAR, NEAR = "#e7e7e4", "#ffffff"
figure = "".join([
    layer(far_arm, FAR),
    layer(far_leg + [far_shoe], FAR, [far_shorts, far_sole, far_laces]),
    layer([ponytail], NEAR, [band]),
    layer([torso, head] + near_leg + [near_shoe], NEAR,
          [hairline, ear, top_hem, waistband, near_shorts, near_sole, near_laces, glute_crease]),
    layer(near_arm, NEAR),
])

if __name__ == "__main__":
    import json, sys
    json.dump({"figure": figure, "eye": EYE}, sys.stdout)
