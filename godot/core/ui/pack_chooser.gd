class_name PackChooser
extends CanvasLayer
## Picks a campaign when a game has more than one pack: the packs side by side as cards (name, missions, author,
## description), Left and Right (or the mouse) to choose, Enter or a click to start. Shared by every game.

signal chosen(pack: Pack)

var packs: Array[Pack] = []
var accent := Color(1.0, 0.83, 0.35)
var count_label := "LEVELS"
var level_count: Callable  ## Pack -> int, the game's own count of levels in a pack
var _i := 0
var _t := 0.0
var _root: Control
var _move: AudioStream
var _select: AudioStream
var _player: AudioStreamPlayer


func _ready() -> void:
	layer = 45
	process_mode = Node.PROCESS_MODE_ALWAYS
	_move = load("res://core/audio/ui_move.wav")
	_select = load("res://core/audio/ui_select.wav")
	_player = AudioStreamPlayer.new()
	_player.bus = "UI"
	add_child(_player)
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.draw.connect(_draw_cards)
	_root.gui_input.connect(_mouse)
	add_child(_root)


func _process(delta: float) -> void:
	_t += delta
	_root.queue_redraw()


func _beep(s: AudioStream) -> void:
	_player.stream = s
	_player.play()


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_left"):
		_i = (_i - 1 + packs.size()) % packs.size()
		_beep(_move)
	elif event.is_action_pressed("ui_right"):
		_i = (_i + 1) % packs.size()
		_beep(_move)
	elif event.is_action_pressed("ui_accept"):
		_pick()
	else:
		return
	get_viewport().set_input_as_handled()


func _mouse(event: InputEvent) -> void:
	if event is InputEventMouseMotion or (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT):
		for k in packs.size():
			if _card_rect(k).has_point(event.position):
				if k != _i:
					_i = k
					_beep(_move)
				if event is InputEventMouseButton:
					_pick()


func _pick() -> void:
	_beep(_select)
	chosen.emit(packs[_i])
	set_process_input(false)
	var tw := create_tween()
	tw.tween_interval(0.15)
	tw.tween_callback(queue_free)


func _card_rect(k: int) -> Rect2:
	var vp := _root.get_viewport_rect().size
	var w := minf(460.0, (vp.x - 120.0) / packs.size() - 30.0)
	var total := packs.size() * w + (packs.size() - 1) * 30.0
	return Rect2((vp.x - total) * 0.5 + k * (w + 30.0), vp.y * 0.5 - 170.0, w, 380.0)


func _draw_cards() -> void:
	var vp := _root.get_viewport_rect().size
	var a := clampf(_t * 3.0, 0.0, 1.0)
	_root.draw_rect(Rect2(Vector2.ZERO, vp), Color(0.01, 0.01, 0.03, 0.78 * a))
	HudKit.text(_root, Vector2(vp.x * 0.5, vp.y * 0.5 - 230), "CHOOSE A CAMPAIGN", 44, Color(accent, a), HudKit.font(true), HudKit.CENTER)
	for k in packs.size():
		var p := packs[k]
		var r := _card_rect(k)
		var on := k == _i
		if on:
			r = r.grow(6.0 + 2.0 * sin(_t * 4.0))
		HudKit.panel(_root, r, accent if on else Color(HudKit.MUTED, 0.5), 16, a)
		HudKit.text(_root, Vector2(r.get_center().x, r.position.y + 62), p.name.to_upper(), 28, Color(accent if on else HudKit.INK, a), HudKit.font(true), HudKit.CENTER)
		var n: int = level_count.call(p) if level_count.is_valid() else p.levels.size()
		HudKit.text(_root, Vector2(r.get_center().x, r.position.y + 100), "%d %s  -  %s" % [n, count_label, p.author.to_upper()], 15, Color(HudKit.MUTED, a), HudKit.label_font(), HudKit.CENTER)
		var y := r.position.y + 150.0
		for line in _wrap(p.description, 19, r.size.x - 50.0):
			HudKit.text(_root, Vector2(r.position.x + 25, y), line, 19, Color(HudKit.INK, a * (1.0 if on else 0.7)), HudKit.label_font())
			y += 30.0
	HudKit.hints(_root, Vector2(vp.x * 0.5, vp.y * 0.5 + 260), [["LEFT / RIGHT", "choose"], ["ENTER", "start"]], a)


func _wrap(s: String, size: int, width: float) -> PackedStringArray:
	var out := PackedStringArray()
	var line := ""
	for word in s.split(" ", false):
		var t := word if line == "" else line + " " + word
		if HudKit.width(t, size, HudKit.label_font()) > width and line != "":
			out.append(line)
			line = word
		else:
			line = t
	if line != "":
		out.append(line)
	return out
