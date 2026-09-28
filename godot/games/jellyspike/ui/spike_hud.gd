class_name SpikeHud
extends Control
## Jelly Spike HUD: a scoreboard with both scores in the blobs' colours (the server's marked), the touches used on each
## side as three dots under its blob, POINT and MATCH POINT cards, the winner, and how to play (and F2 for a second
## player) for new players.

const COLORS := [Color(0.35, 0.8, 1.0), Color(1.0, 0.5, 0.4)]

@export var game: SpikeGame

var _t := 0.0
var _point_t := 0.0
var _point_side := 0
var _hint := 10.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.match_started.connect(func(e):
		e.event.connect(_on_event)
		_hint = 10.0)


func _on_event(kind: String, d: Dictionary) -> void:
	if kind == "point":
		_point_t = 1.4
		_point_side = d["side"]


func _process(delta: float) -> void:
	_t += delta
	_point_t = maxf(0.0, _point_t - delta)
	_hint = maxf(0.0, _hint - delta)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	var names := ["YOU", "CPU"] if not game.versus else ["PLAYER 1", "PLAYER 2"]
	if game.demo:
		names = ["CPU", "CPU"]
	# the scoreboard
	var w := 420.0
	var r := Rect2(vp.x * 0.5 - w * 0.5, 16, w, 96)
	HudKit.panel(self, r, HudKit.GOLD)
	for s in 2:
		var cx := r.position.x + (w * 0.25 if s == 0 else w * 0.75)
		HudKit.text(self, Vector2(cx, r.position.y + 30), names[s], 18, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
		HudKit.text(self, Vector2(cx, r.position.y + 82), str(e.score[s]), 48, COLORS[s], HudKit.font(true), HudKit.CENTER)
		if e.server == s and e.phase != SpikeEngine.Phase.OVER:
			HudKit.gem(self, Vector2(cx + (-70 if s == 0 else 70), r.position.y + 64), 8.0, HudKit.GOLD)
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 72), "-", 36, HudKit.INK, HudKit.font(true), HudKit.CENTER)
	# the power meters, under the scoreboard: full, they pulse and say which key fires the spike
	for s in 2:
		var mw := w * 0.5 - 40.0
		var mx := r.position.x + (20.0 if s == 0 else w * 0.5 + 20.0)
		var mr := Rect2(mx, r.end.y + 8, mw, 10)
		var f: float = e.power[s]
		draw_rect(mr.grow(2), Color(0, 0, 0, 0.5))
		var col: Color = COLORS[s]
		if f >= 1.0:
			col = col.lerp(Color(1.0, 0.85, 0.4), 0.5 + 0.5 * sin(_t * 10.0))
		draw_rect(Rect2(mr.position, Vector2(mr.size.x * f, mr.size.y)), col)
		if f >= 1.0:
			var label := "ARMED!" if e.armed[s] else ("POWER  -  " + _power_key(s) if not game.demo else "POWER")
			HudKit.text(self, Vector2(mr.get_center().x, mr.end.y + 22), label, 16, col, HudKit.label_font(), HudKit.CENTER)
	if game.wins[0] + game.wins[1] > 0:
		HudKit.text(self, Vector2(vp.x * 0.5, r.end.y + 56), "MATCHES  %d - %d" % game.wins, 18, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	# touches used, under each blob
	var cam := get_viewport().get_camera_3d()
	if cam and e.phase == SpikeEngine.Phase.RALLY:
		for s in 2:
			var bp: Vector2 = e.blobs[s]["pos"]
			var sp := cam.unproject_position(Vector3(bp.x, -0.05, 0.6))
			for i in SpikeEngine.TOUCHES:
				var used: bool = i < e.touches[s]
				draw_circle(sp + Vector2((i - 1) * 18.0, 18.0), 6.0, COLORS[s] if used else Color(1, 1, 1, 0.25))
	var mp := e.phase != SpikeEngine.Phase.OVER and maxi(e.score[0], e.score[1]) >= SpikeEngine.TARGET - 1 \
		and absi(e.score[0] - e.score[1]) >= 1
	if _point_t > 0.0 and e.phase != SpikeEngine.Phase.OVER:
		var who: String = names[_point_side]
		HudKit.banner(self, vp, vp.y * 0.36, "MATCH POINT" if mp else "POINT", who, COLORS[_point_side], minf(1.0, _point_t * 2.0))
	if e.phase == SpikeEngine.Phase.OVER:
		var wn: String = names[e.winner]
		HudKit.banner(self, vp, vp.y * 0.38, ("%s WIN" if wn == "YOU" else "%s WINS") % wn, "%d - %d" % e.score, COLORS[e.winner], 1.0)
		if not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.38 + 120), [["ENTER", "rematch"], ["F2", "two players" if not game.versus else "one player"], ["ESC", "menu"]])
	elif _hint > 0.0 and not game.demo:
		var h := [["ARROWS", "move"], ["UP / SPACE", "jump (hold: higher)"], ["DOWN", "power spike"], ["F2", "second player"]] if not game.versus \
			else [["A D  W  S", "left blob"], ["ARROWS  +  UP DOWN", "right blob"], ["F2", "one player"]]
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 50), h)
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 30), "DEMO  -  PRESS ANY KEY TO PLAY", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)


func _power_key(side: int) -> String:
	if game.versus:
		return "S" if side == 0 else "DOWN"
	return "DOWN" if side == 0 else ""
