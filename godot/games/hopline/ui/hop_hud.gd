class_name HopHud
extends Control
## Hopline HUD: the score rolling up (it bumps on every gain), the stage and its time of day, frogs left as little
## frog heads, the five bays (filled, the fly, the crocodile), the quick-crossing streak, the time bar (it pulses
## when short), points popping where frogs reach home, drivers' honks, READY, ALL HOME, GAME OVER.

const ACCENT := Color(0.45, 0.9, 0.45)
const FROG := Color(0.35, 0.8, 0.2)
const STREAK := [Color(1.0, 0.85, 0.35), Color(1.0, 0.6, 0.25), Color(1.0, 0.4, 0.3), Color(1.0, 0.35, 0.7)]

@export var game: HopGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _shown := 0.0          ## the score as displayed, rolling towards the real one
var _score_pop := 0.0
var _streak_pop := 0.0
var _bay_pop := [0.0, 0.0, 0.0, 0.0, 0.0]
var _clear_t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.stage_started.connect(func(e):
		e.event.connect(_on_event)
		_clear_t = 0.0
		if e.score == 0:
			_shown = 0.0)
	game.fx.connect(_on_fx)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"home":
			var at := HopView3D.cell(HopEngine.BAYS[d["bay"]], 0, 0.8)
			_pop("+%d" % (50 + d["time_bonus"]), at, HudKit.GOLD, 30)
			_bay_pop[d["bay"]] = 1.0
			if game.streak >= 1:
				_pop("QUICK  %.1fs" % game.last_crossing, at + Vector3(0, 0.9, 0), STREAK[mini(game.streak - 1, 3)], 22, 0.15)
				_streak_pop = 1.0
		"fly":
			_pop("FLY +200", HopView3D.cell(e.x, 0, 1.3), Color(0.7, 1.0, 0.5), 28, 0.1)
		"lady":
			_pop("LADY!", HopView3D.cell(e.x, e.row, 1.0), Color(1.0, 0.6, 0.8), 24)
		"lady_home":
			_pop("LADY +200", HopView3D.cell(e.x, 0, 1.8), Color(1.0, 0.6, 0.8), 28, 0.2)
		"extra_life":
			_pop("EXTRA FROG", HopView3D.cell(7.0, 6, 1.0), HudKit.GOOD, 34)
		"all_home":
			_clear_t = 0.0


func _on_fx(kind: String, d: Dictionary) -> void:
	if kind == "honk" and d.get("near", false):
		_pop("HONK!", d["pos"] + Vector3(0, 0.4, 0), Color(1.0, 0.9, 0.35), 24)


func _pop(text: String, pos: Vector3, col: Color, size: int, delay := 0.0) -> void:
	_pops.append({"text": text, "pos": pos, "t": -delay, "col": col, "size": size})


func _process(delta: float) -> void:
	_t += delta
	_clear_t += delta
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.4)
	var e := game.engine
	if e:
		if e.score > _shown + 0.5:
			_shown = minf(float(e.score), _shown + maxf(40.0, (e.score - _shown) * 6.0) * delta)
			_score_pop = 1.0
		else:
			_shown = float(e.score)
	_score_pop = maxf(0.0, _score_pop - delta * 4.0)
	_streak_pop = maxf(0.0, _streak_pop - delta * 2.0)
	for i in 5:
		_bay_pop[i] = maxf(0.0, _bay_pop[i] - delta * 2.0)
	queue_redraw()


## A frog's head seen from the front: the lives counter.
func _frog_head(c: Vector2, r: float, col: Color) -> void:
	draw_circle(c + Vector2(0, 2), r * 1.05, Color(0, 0, 0, 0.35 * col.a), true, -1.0, true)
	draw_circle(c, r, col, true, -1.0, true)
	for s in [-1.0, 1.0]:
		var ec := c + Vector2(s * r * 0.55, -r * 0.62)
		draw_circle(ec, r * 0.42, col, true, -1.0, true)
		draw_circle(ec, r * 0.3, Color(1, 1, 1, col.a), true, -1.0, true)
		draw_circle(ec + Vector2(0, r * 0.03), r * 0.16, Color(0.05, 0.05, 0.08, col.a), true, -1.0, true)
	draw_arc(c + Vector2(0, r * 0.05), r * 0.55, 0.35, PI - 0.35, 12, Color(0.1, 0.25, 0.05, col.a), 2.0, true)


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	# score, with a bump on every gain
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	var sp := 1.0 + 0.18 * _score_pop
	HudKit.text(self, Vector2(48, 38), "SCORE", 15, HudKit.MUTED, HudKit.label_font())
	HudKit.text(self, Vector2(48, 84 + 4 * _score_pop), "%07d" % int(_shown), int(36 * sp), HudKit.GOLD.lerp(Color.WHITE, _score_pop * 0.6),
		HudKit.font(true))
	# frogs left
	for i in mini(e.lives, 8):
		_frog_head(Vector2(50 + i * 34, 126), 11.0, FROG)
	# the streak of quick crossings
	if game.streak >= 1:
		var col: Color = STREAK[mini(game.streak - 1, 3)]
		var s := 1.0 + 0.35 * _streak_pop
		var label := "STREAK x%d" % game.streak
		var w := HudKit.width(label, int(24 * s), HudKit.font(true)) + 36.0
		var r := Rect2(24, 150, w, 42 * s)
		HudKit.panel(self, r, col, 12)
		draw_rect(Rect2(r.position + Vector2(12, r.size.y - 6), Vector2((r.size.x - 24) * (0.5 + 0.5 * sin(_t * 6.0)), 2)),
			Color(col, 0.5))
		HudKit.text(self, Vector2(42, 150 + 30 * s), label, int(24 * s), col.lerp(Color.WHITE, _streak_pop * 0.5), HudKit.font(true))
	# stage, time of day, best
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	var mood: String = HopView3D.MOODS[game.stage % HopView3D.MOODS.size()]["name"]
	HudKit.text(self, Vector2(vp.x - 48, 38), "STAGE %d  -  %s" % [game.stage + 1, mood], 15, HudKit.MUTED, HudKit.label_font(),
		HudKit.RIGHT)
	HudKit.text(self, Vector2(vp.x - 48, 80), "BEST %07d" % maxi(game.high, e.score), 24, HudKit.INK, HudKit.font(true), HudKit.RIGHT)
	# the five bays
	var bw := 5 * 40.0 + 24.0
	var br := Rect2(vp.x * 0.5 - bw * 0.5, 16, bw, 46)
	HudKit.panel(self, br, Color(0, 0, 0, 0), 14, 0.8)
	for i in 5:
		var c := Vector2(br.position.x + 32 + i * 40, br.position.y + 23)
		var pop: float = _bay_pop[i]
		draw_circle(c, 13.0, Color(0.1, 0.3, 0.15, 0.9), true, -1.0, true)
		draw_arc(c, 13.0, 0, TAU, 24, Color(0.4, 0.8, 0.4, 0.5), 1.5, true)
		if e.filled[i]:
			_frog_head(c + Vector2(0, 2), 9.0 * (1.0 + 0.5 * pop), FROG.lerp(Color.WHITE, pop * 0.5))
		elif i == e.fly_bay:
			var g := 0.6 + 0.4 * sin(_t * 10.0)
			draw_circle(c, 6.0 + g * 2.0, Color(0.85, 1.0, 0.4, 0.35), true, -1.0, true)
			draw_circle(c, 3.5, Color(1.0, 1.0, 0.7), true, -1.0, true)
		elif i == e.croc_bay:
			draw_line(c + Vector2(-7, -3), c + Vector2(7, 3), HudKit.BAD, 3.0, true)
			draw_line(c + Vector2(-7, 3), c + Vector2(7, -3), HudKit.BAD, 3.0, true)
	# the time bar: glows, and pulses when short
	var w2 := minf(vp.x * 0.36, 520.0)
	var tr := Rect2(vp.x * 0.5 - w2 * 0.5, vp.y - 40, w2, 14)
	var f := clampf(e.life_t / HopEngine.LIFE_TIME, 0.0, 1.0)
	var col2 := HudKit.GOOD if f > 0.33 else (HudKit.GOLD if f > 0.15 else HudKit.BAD)
	var pulse := 0.0
	if f < 0.27 and e.phase == HopEngine.Phase.PLAY:
		pulse = 0.5 + 0.5 * sin(_t * 14.0)
	var fill := Rect2(tr.position, Vector2(tr.size.x * f, tr.size.y))
	draw_rect(tr.grow(3), Color(0, 0, 0, 0.55))
	draw_rect(fill.grow(4 + pulse * 3), Color(col2, 0.12 + 0.15 * pulse))
	draw_rect(fill.grow(2), Color(col2, 0.25))
	draw_rect(fill, col2.lerp(Color.WHITE, pulse * 0.35))
	draw_rect(Rect2(fill.position, Vector2(fill.size.x, 4)), Color(1, 1, 1, 0.3))
	HudKit.text(self, Vector2(tr.position.x - 12, tr.end.y), "TIME", 16, HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
	HudKit.text(self, Vector2(tr.end.x + 12, tr.end.y + 1), "%d" % ceili(e.life_t), 20, col2.lerp(Color.WHITE, pulse * 0.5),
		HudKit.font(true))
	# pops over the scene, springing in
	var cam: Camera3D = get_viewport().get_camera_3d()
	for p in _pops:
		var t: float = p["t"]
		if cam and t >= 0.0 and not cam.is_position_behind(p["pos"]):
			var at := cam.unproject_position(p["pos"]) + Vector2(0, -40.0 * t)
			var c: Color = p["col"]
			var grow: float = 1.0 + 0.6 * exp(-t * 14.0) * cos(t * 30.0) if t < 0.4 else 1.0
			HudKit.text(self, at, p["text"], int(p["size"] * grow), Color(c, clampf((1.4 - t) / 0.5, 0.0, 1.0)), HudKit.font(true),
				HudKit.CENTER)
	if e.phase == HopEngine.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.42, "READY", "STAGE %d  -  %s" % [game.stage + 1, mood] if e.time < 2.0 else "", ACCENT, 1.0,
			1.0 + 0.08 * sin(_t * 8.0))
	elif e.phase == HopEngine.Phase.CLEARED:
		var k := minf(1.0, _clear_t / 0.35)
		var bounce := 1.0 + 0.35 * (1.0 - k) * sin(k * PI * 2.5)
		HudKit.banner(self, vp, vp.y * 0.34, "ALL HOME", "+1000", HudKit.GOOD, k, bounce)
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.5, "GAME OVER", "SCORE %d" % e.score, HudKit.BAD, 1.0)
		if not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.5 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 110, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 80), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
