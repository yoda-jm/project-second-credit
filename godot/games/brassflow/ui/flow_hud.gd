class_name FlowHud
extends Control
## Brassflow HUD: score and best, the level and its chances, the gauge (the countdown to the flow, then the pieces
## filled), a map of the board seen from above (every pipe, the glow as it runs, the boiler, the engine and its inlet,
## blocked cells, the cursor) with the next pieces beside it, points rising where the glow fills a piece (a loop bonus
## for a cross filled both ways), the level card, ENGINE RUNNING with its bonus, LEAK!, GAME OVER. Until the first
## piece is down the keys are shown.

const ACCENT := Color(1.0, 0.7, 0.3)
const GLOW := Color(0.3, 1.0, 0.6)
const BRASS := Color(0.9, 0.68, 0.35)
const CELL := 20.0

@export var game: FlowGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _placed := false
var _turn := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"place":
			_placed = true
		"rotate":
			_turn = 1.0
		"replace":
			var c: Vector2i = d["cell"]
			_pops.append({"text": "-50", "pos": Vector3(c.x + 0.5, 0.6, c.y + 0.5), "t": 0.0, "col": HudKit.BAD, "size": 22})
		"fill":
			var c: Vector2i = d["cell"]
			var twice: bool = d["cross_twice"]
			var pts := (100 if game.engine.fast else 50) + (500 if twice else 0)
			_pops.append({"text": ("LOOP! " if twice else "") + str(pts), "pos": Vector3(c.x + 0.5, 0.6, c.y + 0.5), "t": 0.0,
				"col": HudKit.GOLD if twice else GLOW, "size": 30 if twice else 22})


func _process(delta: float) -> void:
	_t += delta
	_turn = maxf(0.0, _turn - delta * 6.0)
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.1)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "LEVEL %d" % (e.level + 1), "BEST %07d" % maxi(game.high, e.score), HudKit.INK, HudKit.RIGHT, 24)
	for i in e.chances:
		HudKit.gem(self, Vector2(vp.x - 56 - i * 26, 124), 9.0, ACCENT)
	# the gauge: the countdown, then the pieces filled
	var c := Vector2(vp.x * 0.5, 66)
	HudKit.panel(self, Rect2(c.x - 150, 12, 300, 108), ACCENT)
	if not e.flowing:
		var full := maxf(8.0, 18.0 - e.level * 1.2)
		var frac := clampf(e.countdown / full, 0.0, 1.0)
		var low := e.countdown < 4.0 and e.phase == FlowEngine.Phase.PLAY
		var col := HudKit.BAD.lerp(Color.WHITE, 0.4 * (0.5 + 0.5 * sin(_t * 10.0))) if low else HudKit.INK
		HudKit.ring(self, c + Vector2(-90, 0), 34.0, frac, ACCENT, 8.0)
		HudKit.text(self, c + Vector2(-90, 12), "%d" % ceili(e.countdown), 30, col, HudKit.font(true), HudKit.CENTER)
		HudKit.text(self, c + Vector2(40, -10), "GLOW IN", 18, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
		HudKit.text(self, c + Vector2(40, 24), "TO THE ENGINE", 20, HudKit.INK, HudKit.font(true), HudKit.CENTER)
	else:
		HudKit.ring(self, c + Vector2(-90, 0), 34.0, e.progress, GLOW, 8.0)
		HudKit.text(self, c + Vector2(-90, 12), "%d" % e.filled, 30, HudKit.INK, HudKit.font(true), HudKit.CENTER)
		HudKit.text(self, c + Vector2(40, -10), "FAST FLOW" if e.fast else "FLOWING", 18, GLOW, HudKit.label_font(), HudKit.CENTER)
		HudKit.text(self, c + Vector2(40, 24), "%d PIECES" % e.filled, 24, HudKit.INK, HudKit.font(true), HudKit.CENTER)
	_draw_map(e, Vector2(vp.x - 24 - (FlowEngine.COLS * CELL + 120), vp.y - 24 - (FlowEngine.ROWS * CELL + 40)))
	# points over the board
	var cam := get_viewport().get_camera_3d()
	for p in _pops:
		if cam == null or cam.is_position_behind(p["pos"]):
			continue
		var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 60.0)
		var a := clampf(1.1 - p["t"], 0.0, 1.0)
		var col2: Color = p["col"]
		HudKit.text(self, sp, p["text"], p["size"], Color(col2, a), HudKit.font(true), HudKit.CENTER)
	if e.phase == FlowEngine.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.36, "LEVEL %d" % (e.level + 1), "LEAD THE GLOW FROM THE BOILER TO THE ENGINE", ACCENT,
			clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == FlowEngine.Phase.DONE and e.passed():
		HudKit.banner(self, vp, vp.y * 0.36, "ENGINE RUNNING!", "%d PIECES  -  BONUS %d" % [e.filled, FlowEngine.EXIT_BONUS + maxi(0, e.filled - e.length) * 50],
			HudKit.GOLD, clampf((3.0 - e.phase_t) * 3.0, 0.0, 1.0))
	elif e.phase == FlowEngine.Phase.DONE:
		HudKit.banner(self, vp, vp.y * 0.36, "LEAK!", "THE GLOW NEVER REACHED THE ENGINE  -  TRY AGAIN", HudKit.BAD,
			clampf((3.0 - e.phase_t) * 3.0, 0.0, 1.0))
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.42, "GAME OVER", "PRESS ENTER" if not game.demo else "", HudKit.BAD, 1.0)
	elif not _placed and not game.demo and e.phase == FlowEngine.Phase.PLAY:
		HudKit.hints(self, Vector2(vp.x * 0.42, vp.y - 50), [["ARROWS", "MOVE"], ["SPACE", "LAY"], ["R", "TURN"], ["F", "FAST FLOW"]])
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.42, vp.y - 30), "DEMO  -  PRESS ANY KEY TO PLAY", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)


## The board from above, and the dispenser's next pieces at its left.
func _draw_map(e: FlowEngine, at: Vector2) -> void:
	var w := FlowEngine.COLS * CELL
	var h := FlowEngine.ROWS * CELL
	HudKit.panel(self, Rect2(at, Vector2(w + 120, h + 40)), ACCENT)
	var o := at + Vector2(100, 20)
	draw_rect(Rect2(o, Vector2(w, h)), Color(0.05, 0.09, 0.07, 0.9))
	for x in FlowEngine.COLS + 1:
		draw_line(o + Vector2(x * CELL, 0), o + Vector2(x * CELL, h), Color(1, 1, 1, 0.07), 1.0)
	for y in FlowEngine.ROWS + 1:
		draw_line(o + Vector2(0, y * CELL), o + Vector2(w, y * CELL), Color(1, 1, 1, 0.07), 1.0)
	for b in e.blocked:
		var r := Rect2(o + Vector2(b.x, b.y) * CELL + Vector2(3, 3), Vector2(CELL - 6, CELL - 6))
		draw_rect(r, Color(0.3, 0.3, 0.32))
		draw_line(r.position, r.end, Color(0.15, 0.15, 0.16), 2.0)
		draw_line(Vector2(r.position.x, r.end.y), Vector2(r.end.x, r.position.y), Color(0.15, 0.15, 0.16), 2.0)
	# pipes, the glow along the parts it has filled
	for cell in e.grid:
		var g: Dictionary = e.grid[cell]
		var mid := o + (Vector2(cell.x, cell.y) + Vector2(0.5, 0.5)) * CELL
		_piece(mid, g["piece"], CELL, BRASS, 5.0)
		for enter in g["filled"]:
			var f := e.progress if e.flowing and cell == e.head and enter == e.head_from and e.phase == FlowEngine.Phase.PLAY else 1.0
			_flow(mid, enter, FlowEngine.exit_of(g["piece"], enter), f, CELL)
	# the boiler and its outlet; the engine and its inlet
	var sm := o + (Vector2(e.source.x, e.source.y) + Vector2(0.5, 0.5)) * CELL
	var sd: Vector2i = FlowEngine.DIRS[e.source_dir]
	draw_line(sm, sm + Vector2(sd.x, sd.y) * CELL * 0.5, GLOW, 5.0)
	draw_circle(sm, CELL * 0.36, GLOW.darkened(0.3))
	draw_circle(sm, CELL * 0.24, GLOW)
	var xm := o + (Vector2(e.exit_cell.x, e.exit_cell.y) + Vector2(0.5, 0.5)) * CELL
	var xd: Vector2i = FlowEngine.DIRS[e.exit_dir]
	var pulse := 0.5 + 0.5 * sin(_t * 5.0)
	draw_line(xm, xm + Vector2(xd.x, xd.y) * CELL * 0.5, HudKit.GOLD, 5.0)
	draw_rect(Rect2(xm - Vector2(CELL, CELL) * 0.36, Vector2(CELL, CELL) * 0.72), Color(0.95, 0.45, 0.2).lerp(HudKit.GOLD, pulse * 0.5))
	# an arrow into the inlet
	var tip := xm + Vector2(xd.x, xd.y) * CELL * 0.62
	var back := xm + Vector2(xd.x, xd.y) * CELL * (1.0 + 0.1 * pulse)
	var side := Vector2(-xd.y, xd.x) * CELL * 0.18
	draw_colored_polygon(PackedVector2Array([tip, back + side, back - side]), Color(HudKit.GOLD, 0.6 + 0.4 * pulse))
	# the cursor
	var cr := Rect2(o + Vector2(e.cursor.x, e.cursor.y) * CELL, Vector2(CELL, CELL))
	draw_rect(cr, Color(1, 1, 1, 0.9) if e.can_place(e.cursor) else HudKit.BAD, false, 2.0)
	HudKit.text(self, o + Vector2(0, -5), "THE BOARD", 13, HudKit.MUTED, HudKit.label_font(), HudKit.LEFT)
	# the next pieces: the front one large (turning when turned), two more small
	HudKit.text(self, at + Vector2(48, 30), "NEXT", 15, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
	var fc := at + Vector2(48, 66)
	draw_rect(Rect2(fc - Vector2(28, 28), Vector2(56, 56)), Color(0.12, 0.1, 0.08, 0.9))
	draw_set_transform(fc, -_turn * PI * 0.5, Vector2.ONE)
	_piece(Vector2.ZERO, e.queue[0], 50.0, HudKit.GOLD, 8.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	for i in range(1, mini(3, e.queue.size())):
		var pc := at + Vector2(48, 92 + i * 34)
		draw_rect(Rect2(pc - Vector2(14, 14), Vector2(28, 28)), Color(0.12, 0.1, 0.08, 0.7))
		_piece(pc, e.queue[i], 26.0, BRASS, 4.0)


## A piece drawn from above: a line from the middle to each opening (a cross is two straight lines).
func _piece(mid: Vector2, piece: String, s: float, col: Color, w: float) -> void:
	for d in FlowEngine.PIECES[piece]:
		var v: Vector2i = FlowEngine.DIRS[d]
		draw_line(mid, mid + Vector2(v.x, v.y) * s * 0.5, col, w)
	if piece != "x":
		draw_circle(mid, w * 0.5, col)


## The glow through a piece, entering by one side and leaving by another, filled to f.
func _flow(mid: Vector2, enter: int, out: int, f: float, s: float) -> void:
	var a: Vector2i = FlowEngine.DIRS[enter]
	var b: Vector2i = FlowEngine.DIRS[out]
	var p0 := mid + Vector2(a.x, a.y) * s * 0.5
	var p1 := mid + Vector2(b.x, b.y) * s * 0.5
	if f <= 0.5:
		draw_line(p0, p0.lerp(mid, f * 2.0), GLOW, 3.5)
	else:
		draw_line(p0, mid, GLOW, 3.5)
		draw_line(mid, mid.lerp(p1, (f - 0.5) * 2.0), GLOW, 3.5)
