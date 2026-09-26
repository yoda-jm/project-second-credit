extends Node
## Glimmerdeep two-player race: the screen split in two, the same cave with the same seed on each side (same rocks,
## same creatures), each player seeing the other as a ghost. A bar across the top keeps the live scores; the first
## out of the exit wins, else the better score when both are out. Enter: next cave; R: the same cave again.
## Player 1: arrow keys, Ctrl or Enter to grab, first gamepad. Player 2: W A S D (by key position), Shift or Space
## to grab, second gamepad. "--demo" lets the bot race itself on both sides (for captures).

const P1_COL := Color(1.0, 0.72, 0.2)
const P2_COL := Color(0.4, 0.8, 1.0)

var games: Array[CaveGame] = []
var views: Array = []
var caves: Array[CaveStored] = []
var cave_no := 0
var result := ""
var _t := 0.0
var _hud: Control
var _seed := 1


func _ready() -> void:
	var pack := Pack.find("glimmerdeep", "second-credit")
	for f in pack.levels:
		caves.append_array(BdcffLoader.load_file(f).caves)
	var demo := OS.get_cmdline_user_args().has("--demo")
	var split := HBoxContainer.new()
	split.set_anchors_preset(Control.PRESET_FULL_RECT)
	split.add_theme_constant_override("separation", 4)
	add_child(split)
	for p in [1, 2]:
		var box := SubViewportContainer.new()
		box.stretch = true
		box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		split.add_child(box)
		var vp := SubViewport.new()
		vp.own_world_3d = true
		vp.audio_listener_enable_3d = p == 1
		box.add_child(vp)
		var g := CaveGame.new()
		g.player = p
		g.auto_restart = false
		g.autopilot = demo
		vp.add_child(g)
		var v := CaveView3D.new()
		v.game = g
		v.ghost_color = P2_COL if p == 1 else P1_COL
		vp.add_child(v)
		var layer := CanvasLayer.new()
		vp.add_child(layer)
		var hud := CaveHud.new()
		hud.game = g
		layer.add_child(hud)
		var audio := CaveAudio.new()
		audio.game = g
		audio.with_music = p == 1
		vp.add_child(audio)
		games.append(g)
		views.append(v)
		g.cave_finished.connect(func(_e, _ok): _check_end())
	views[0].ghost = games[1]
	views[1].ghost = games[0]
	var top := CanvasLayer.new()
	top.layer = 20
	add_child(top)
	_hud = Control.new()
	_hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.draw.connect(_draw_race)
	top.add_child(_hud)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(_start)
	_start()


func _start() -> void:
	result = ""
	_seed = randi() & 0x7fffffff
	for g in games:
		g.race_seed = _seed
		g.cave = caves[cave_no]
		g.demo = null
		g.restart()


func _process(delta: float) -> void:
	_t += delta
	_hud.queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if result == "" or not event.is_pressed() or event.is_echo():
		return
	if event.is_action_pressed("ui_accept"):
		cave_no = (cave_no + 1) % caves.size()
		_start()
	elif event is InputEventKey and event.physical_keycode == KEY_R:
		_start()


func _done(g: CaveGame) -> bool:
	return g.finished


func _check_end() -> void:
	var a := games[0]
	var b := games[1]
	var ea := a.engine.player_state == CaveRendered.PlayerState.EXITED
	var eb := b.engine.player_state == CaveRendered.PlayerState.EXITED
	if result != "":
		return
	if ea != eb and (ea or eb):  # the first one out wins, even while the other still plays
		result = "PLAYER 1 WINS" if ea else "PLAYER 2 WINS"
	elif a.finished and b.finished:
		result = "DRAW" if a.score == b.score else ("PLAYER 1 WINS" if a.score > b.score else "PLAYER 2 WINS")
	if result != "" and OS.get_cmdline_user_args().has("--demo"):
		get_tree().create_timer(5.0).timeout.connect(func():
			cave_no = (cave_no + 1) % caves.size()
			_start())


func _draw_race() -> void:
	var vp := _hud.get_viewport_rect().size
	var cx := vp.x * 0.5
	# the live scores, one panel over the seam
	HudKit.panel(_hud, Rect2(cx - 290, vp.y - 118, 580, 96), HudKit.GOLD, 16, 0.92)
	HudKit.text(_hud, Vector2(cx, vp.y - 88), caves[cave_no].name.to_upper(), 16, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
	for i in 2:
		var g := games[i]
		if g.engine == null:
			continue
		var col := P1_COL if i == 0 else P2_COL
		var x := cx - 150 if i == 0 else cx + 150
		var e := g.engine
		var state := ""
		match e.player_state:
			CaveRendered.PlayerState.EXITED: state = "OUT!"
			CaveRendered.PlayerState.DIED: state = "CRUSHED"
			CaveRendered.PlayerState.TIMEOUT: state = "TIME UP"
		HudKit.text(_hud, Vector2(x, vp.y - 60), "P%d  %06d" % [i + 1, g.score], 26, col, HudKit.font(true), HudKit.CENTER)
		HudKit.text(_hud, Vector2(x, vp.y - 34), state if state != "" else "GEMS %d / %d" % [e.diamonds_collected, e.diamonds_needed],
			16, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	# who leads right now
	if result == "" and games[0].engine and games[1].engine:
		var lead := signi(games[0].score - games[1].score)
		if lead != 0:
			var lx := cx - 40 if lead > 0 else cx + 40
			HudKit.gem(_hud, Vector2(lx, vp.y - 66), 9.0, P1_COL if lead > 0 else P2_COL)
	if result != "":
		var a := clampf(_t, 0.0, 1.0)
		var col := HudKit.GOLD if result == "DRAW" else (P1_COL if result.begins_with("PLAYER 1") else P2_COL)
		HudKit.banner(_hud, vp, vp.y * 0.42, result, "ENTER  NEXT CAVE     R  AGAIN", col, a)
