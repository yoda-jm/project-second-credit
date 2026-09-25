class_name HudKit
extends RefCounted
## Shared drawing helpers for the in-game HUDs, so every game has the same polished look: frosted panels,
## small spaced labels over big values, glowing progress rings, key-cap hints and banners.
## All functions draw on the given CanvasItem from its _draw().

const INK := Color(0.94, 0.95, 1.0)
const MUTED := Color(0.62, 0.66, 0.8)
const GOLD := Color(1.0, 0.83, 0.35)
const GOOD := Color(0.45, 1.0, 0.6)
const BAD := Color(1.0, 0.38, 0.3)
const PANEL := Color(0.04, 0.05, 0.1, 0.72)

enum { LEFT, CENTER, RIGHT }

static var _fonts := {}
static var _boxes := {}


static func font(big := false) -> Font:
	var key := "big" if big else "narrow"
	if not _fonts.has(key):
		_fonts[key] = load("res://core/fonts/kenney_future.ttf" if big else "res://core/fonts/kenney_future_narrow.ttf")
	return _fonts[key]


## Narrow font with extra letter spacing, for the small labels above values.
static func label_font() -> Font:
	if not _fonts.has("label"):
		var f := FontVariation.new()
		f.base_font = font()
		f.spacing_glyph = 3
		_fonts["label"] = f
	return _fonts["label"]


static func width(s: String, size: int, f: Font = null) -> float:
	return (f if f else font()).get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x


## Text with a soft drop shadow (and a thin outline so it reads over bright scenes).
static func text(ci: CanvasItem, pos: Vector2, s: String, size: int, col: Color, f: Font = null, align := LEFT) -> void:
	f = f if f else font()
	if align != LEFT:
		pos.x -= width(s, size, f) * (0.5 if align == CENTER else 1.0)
	var shadow := Color(0, 0, 0, col.a * 0.55)
	ci.draw_string(f, pos + Vector2(0, maxf(2.0, size * 0.06)), s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, shadow)
	ci.draw_string_outline(f, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, maxi(2, size / 14), Color(0, 0, 0, col.a * 0.6))
	ci.draw_string(f, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


static func _box(radius: int, alpha: float, border: Color) -> StyleBoxFlat:
	var key := "%d|%s|%s" % [radius, alpha, border]
	if not _boxes.has(key):
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(PANEL, PANEL.a * alpha)
		sb.set_corner_radius_all(radius)
		sb.border_color = border
		sb.set_border_width_all(1)
		sb.shadow_color = Color(0, 0, 0, 0.3 * alpha)
		sb.shadow_size = 14
		sb.anti_aliasing = true
		_boxes[key] = sb
	return _boxes[key]


## A frosted panel with an optional accent bar along its top edge.
static func panel(ci: CanvasItem, rect: Rect2, accent := Color(0, 0, 0, 0), radius := 14, alpha := 1.0) -> void:
	ci.draw_style_box(_box(radius, alpha, Color(1, 1, 1, 0.1 * alpha)), rect)
	if accent.a > 0.0:
		var bar := Rect2(rect.position + Vector2(radius, 0), Vector2(rect.size.x - radius * 2.0, 3))
		ci.draw_rect(bar, accent)
		ci.draw_rect(bar.grow_individual(0, 0, 0, 5), Color(accent, accent.a * 0.18))


## A labelled value: small spaced label on top, the value below. `x` is the left, centre or right edge.
static func stat(ci: CanvasItem, x: float, y: float, label: String, value: String, col: Color, align := LEFT,
		size := 36) -> void:
	text(ci, Vector2(x, y + 18), label, 15, Color(MUTED, col.a), label_font(), align)
	text(ci, Vector2(x, y + 18 + size + 4), value, size, col, font(true), align)


## A progress ring with a glow; `frac` 1 is full. Draws the track, the arc and a bright head.
static func ring(ci: CanvasItem, c: Vector2, r: float, frac: float, col: Color, w := 10.0, track := true) -> void:
	if track:
		ci.draw_arc(c, r, 0, TAU, 96, Color(1, 1, 1, 0.1 * col.a), w, true)
	if frac <= 0.0:
		return
	var a0 := -PI * 0.5
	var a1 := a0 + TAU * clampf(frac, 0.0, 1.0)
	var n := maxi(8, int(96 * frac))
	ci.draw_arc(c, r, a0, a1, n, Color(col, col.a * 0.12), w * 3.2, true)
	ci.draw_arc(c, r, a0, a1, n, Color(col, col.a * 0.25), w * 1.8, true)
	ci.draw_arc(c, r, a0, a1, n, col, w, true)
	var head := c + Vector2(cos(a1), sin(a1)) * r
	ci.draw_circle(head, w * 0.9, Color(1, 1, 1, col.a * 0.9), true, -1.0, true)


## Soft round shade (fake radial gradient), e.g. to calm the scene behind a countdown.
static func shade(ci: CanvasItem, c: Vector2, r: float, alpha: float) -> void:
	for i in 10:
		var k := 1.0 - float(i) / 10.0
		ci.draw_circle(c, r * k, Color(0, 0, 0, alpha * 0.1), true, -1.0, true)


## A horizontal ribbon across the screen that fades at both ends, with a big title and an optional subtitle.
static func banner(ci: CanvasItem, vp: Vector2, y: float, title: String, sub: String, accent: Color, a: float,
		pop := 1.0) -> void:
	var h := 150.0 if sub != "" else 116.0
	var top := y - h * 0.5
	var mid := Color(0.02, 0.03, 0.07, 0.72 * a)
	var edge := Color(mid, 0.0)
	var pts := PackedVector2Array([Vector2(0, top), Vector2(vp.x * 0.5, top), Vector2(vp.x, top),
		Vector2(vp.x, top + h), Vector2(vp.x * 0.5, top + h), Vector2(0, top + h)])
	ci.draw_polygon(pts, PackedColorArray([edge, mid, edge, edge, mid, edge]))
	for yy in [top, top + h]:
		var line := PackedVector2Array([Vector2(vp.x * 0.1, yy), Vector2(vp.x * 0.5, yy), Vector2(vp.x * 0.9, yy)])
		ci.draw_polyline_colors(line, PackedColorArray([Color(accent, 0), Color(accent, a), Color(accent, 0)]), 2.0, true)
	var size := int(84 * pop)
	var ty := y + size * 0.36 - (22.0 if sub != "" else 0.0)
	text(ci, Vector2(vp.x * 0.5, ty), title, size, Color(accent, a), font(true), CENTER)
	if sub != "":
		text(ci, Vector2(vp.x * 0.5, ty + 50), sub, 28, Color(INK, a * 0.9), label_font(), CENTER)


## One key cap ("SPACE") followed by what it does ("fire"); returns the width used.
static func keycap(ci: CanvasItem, pos: Vector2, key: String, action: String, a := 1.0, measure_only := false) -> float:
	var kw := maxf(38.0, width(key, 20) + 22.0)
	var aw := width(action, 22, label_font())
	if not measure_only:
		var r := Rect2(pos + Vector2(0, -28), Vector2(kw, 38))
		ci.draw_style_box(_box(8, a, Color(1, 1, 1, 0.35 * a)), r)
		ci.draw_rect(Rect2(r.position + Vector2(6, r.size.y - 4), Vector2(kw - 12, 2)), Color(1, 1, 1, 0.12 * a))
		text(ci, pos + Vector2(kw * 0.5, -2), key, 20, Color(INK, a), font(), CENTER)
		text(ci, pos + Vector2(kw + 10, -1), action, 22, Color(MUTED, a), label_font())
	return kw + 10.0 + aw


## A centred row of key caps: pairs is [[key, action], ...].
static func hints(ci: CanvasItem, center: Vector2, pairs: Array, a := 1.0) -> void:
	var gap := 36.0
	var total := -gap
	for p in pairs:
		total += keycap(ci, Vector2.ZERO, p[0], p[1], a, true) + gap
	var x := center.x - total * 0.5
	for p in pairs:
		x += keycap(ci, Vector2(x, center.y), p[0], p[1], a) + gap


## A faceted gem icon (for counters).
static func gem(ci: CanvasItem, c: Vector2, r: float, col: Color) -> void:
	var top := c + Vector2(0, -r)
	var bot := c + Vector2(0, r)
	var l := c + Vector2(-r * 0.85, -r * 0.2)
	var rr := c + Vector2(r * 0.85, -r * 0.2)
	ci.draw_colored_polygon(PackedVector2Array([top, rr, c + Vector2(0, -r * 0.2), l]), col.lightened(0.45))
	ci.draw_colored_polygon(PackedVector2Array([l, c + Vector2(0, -r * 0.2), bot]), col)
	ci.draw_colored_polygon(PackedVector2Array([c + Vector2(0, -r * 0.2), rr, bot]), col.darkened(0.3))
