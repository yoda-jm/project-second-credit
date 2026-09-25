class_name PauseMenu
extends CanvasLayer
## Shared in-game pause menu (Esc or the gamepad Start button): Resume, Restart, volume and Back to menu.
## A game adds one and connects `restart_requested`; the menu pauses the whole tree while open.

signal restart_requested

const GOLD := Color(1.0, 0.83, 0.35)
const LAUNCHER := "res://core/ui/launcher.tscn"

var _root: Control
var _buttons: Array[Button] = []
var _move: AudioStream
var _select: AudioStream
var _player: AudioStreamPlayer


func _ready() -> void:
	layer = 50
	process_mode = Node.PROCESS_MODE_ALWAYS
	_move = load("res://core/audio/ui_move.wav")
	_select = load("res://core/audio/ui_select.wav")
	_player = AudioStreamPlayer.new()
	_player.bus = "UI"
	add_child(_player)
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.visible = false
	add_child(_root)
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.6)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(dim)
	var panel := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.05, 0.09, 0.9)
	sb.border_color = GOLD
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(18)
	sb.set_content_margin_all(30)
	panel.add_theme_stylebox_override("panel", sb)
	panel.custom_minimum_size = Vector2(400, 0)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.add_child(panel)
	_root.add_child(center)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	panel.add_child(v)
	var title := Label.new()
	title.text = "PAUSED"
	title.add_theme_font_override("font", load("res://core/fonts/kenney_future.ttf"))
	title.add_theme_font_size_override("font_size", 52)
	title.add_theme_color_override("font_color", GOLD)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(title)
	for entry in [["RESUME", _resume], ["RESTART", _restart], ["BACK TO MENU", _quit]]:
		var b := Button.new()
		b.text = entry[0]
		b.custom_minimum_size = Vector2(340, 60)
		b.add_theme_font_override("font", load("res://core/fonts/kenney_future_narrow.ttf"))
		b.add_theme_font_size_override("font_size", 32)
		b.add_theme_color_override("font_focus_color", GOLD)
		b.pressed.connect(entry[1])
		b.focus_entered.connect(func(): _sound(_move))
		v.add_child(b)
		_buttons.append(b)
	var vol := HSlider.new()
	vol.min_value = 0.0
	vol.max_value = 1.0
	vol.step = 0.05
	vol.value = Settings.volume["Master"]
	vol.custom_minimum_size = Vector2(340, 36)
	vol.value_changed.connect(func(x): Settings.volume["Master"] = x; Settings.apply())
	var vl := Label.new()
	vl.text = "Volume"
	vl.add_theme_font_override("font", load("res://core/fonts/kenney_future_narrow.ttf"))
	vl.add_theme_font_size_override("font_size", 24)
	v.add_child(vl)
	v.add_child(vol)


func _unhandled_input(event: InputEvent) -> void:
	var toggle: bool = event.is_action_pressed("ui_cancel") \
		or (event is InputEventJoypadButton and event.pressed and event.button_index == JOY_BUTTON_START)
	if toggle:
		if _root.visible:
			_resume()
		else:
			_open()
		get_viewport().set_input_as_handled()


func _open() -> void:
	_root.visible = true
	get_tree().paused = true
	_sound(_select)
	_buttons[0].grab_focus()


func _resume() -> void:
	_root.visible = false
	get_tree().paused = false
	Settings.save_settings()


func _restart() -> void:
	_resume()
	restart_requested.emit()


func _quit() -> void:
	_resume()
	get_tree().change_scene_to_file(LAUNCHER)


func _sound(s: AudioStream) -> void:
	_player.stream = s
	_player.play()
