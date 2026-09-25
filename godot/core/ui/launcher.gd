extends Node
## The collection's front door: a 3D backdrop of drifting gems, the title, the game cards and the main menu
## (Play, Settings, Credits, Quit). Keyboard, gamepad and mouse all work. Games return here from their pause
## menu. Pass "--game=<id>" (user argument) to jump straight into a game.

const GOLD := Color(1.0, 0.83, 0.35)
const PANEL := Color(0.05, 0.05, 0.09, 0.72)

var _selected := 0
var _menu_index := 0
var _buttons: Array[Button] = []
var _cards: Array[Control] = []
var _card_box: HBoxContainer
var _ui: Control
var _settings: Control
var _credits: Control
var _fade: ColorRect
var _sfx := {}
var _sfx_player: AudioStreamPlayer
var _music: AudioStreamPlayer
const PROP_COUNT := 90
var _prop_mm := {}  ## mesh path -> MultiMeshInstance3D
var _prop_count := {}
var _previous := 0
var _morph_t := 10.0
var _camera: Camera3D
var _time := 0.0
var _seeds: Array[Vector4] = []
var _launching := false
var _arrows: Array[Button] = []
var _hovered_card := -1
const CARD_ROW_X := 395.0  ## places the selected card in the middle of the card window


func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--game="):
			var g := GameRegistry.find(arg.substr(7))
			if not g.is_empty() and g["scene"] != "":
				LoadingScreen.go.call_deferred(g["scene"], g["title"])
				return
	_build_backdrop()
	_build_ui()
	_load_sounds()
	_select_game(0, false)
	_focus_menu(0, false)
	_fade_from_black()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--select="):  # for captures: change card after a second
			get_tree().create_timer(1.0).timeout.connect(_select_game.bind(int(arg.substr(9))))


# ------------------------------------------------------------------ backdrop

func _build_backdrop() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.01, 0.01, 0.02)
	env.glow_enabled = true
	env.glow_intensity = 1.1
	env.glow_bloom = 0.15
	env.glow_hdr_threshold = 0.8
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.fog_enabled = true
	env.fog_light_color = Color(0.05, 0.04, 0.08)
	env.fog_density = 0.05
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-40, 30, 0)
	light.light_energy = 0.7
	add_child(light)
	var rim := OmniLight3D.new()
	rim.position = Vector3(-4, 2, 3)
	rim.light_color = Color(0.4, 0.8, 1.0)
	rim.light_energy = 3.0
	rim.omni_range = 14.0
	add_child(rim)
	_camera = Camera3D.new()
	_camera.fov = 50
	_camera.position = Vector3(0, 0, 9)
	add_child(_camera)

	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	for i in PROP_COUNT:
		_seeds.append(Vector4(rng.randf_range(-13, 13), rng.randf_range(-7, 7), rng.randf_range(-16, -2), rng.randf()))
	# one multimesh per distinct prop of every game; each floating object picks its shape from the selected game
	for g in GameRegistry.GAMES:
		for prop in g.get("props", []):
			var key: String = prop[0]
			if not _prop_mm.has(key):
				_prop_mm[key] = _multimesh(key, PROP_COUNT, _prop_material(prop[1]))


func _prop_material(kind: String) -> Material:
	if kind == "model":
		return null
	if kind == "stone":
		var st := Pbr.material("stone_bricks", Color(1.0, 0.96, 0.9), 1.4).duplicate() as StandardMaterial3D
		st.uv1_world_triplanar = false  # the texture must travel and spin with each floating brick
		return st
	if kind == "gem":
		var m := ShaderMaterial.new()
		m.shader = load("res://games/glimmerdeep/shaders/gem.gdshader")
		return m
	var s := StandardMaterial3D.new()
	match kind:
		"rock":
			s.albedo_color = Color(0.3, 0.29, 0.28)
			s.roughness = 0.8
		"iron":
			s.albedo_color = Color(0.3, 0.3, 0.32)
			s.metallic = 0.8
			s.roughness = 0.35
			s.emission_enabled = true
			s.emission = Color(1.0, 0.35, 0.05)
			s.emission_energy_multiplier = 0.9
		"stone":
			s.albedo_color = Color(0.62, 0.58, 0.5)
			s.roughness = 0.9
		"cone":
			s.albedo_color = Color(1.0, 0.45, 0.05)
			s.emission_enabled = true
			s.emission = Color(1.0, 0.35, 0.0)
			s.emission_energy_multiplier = 0.6
		"steel":
			s.albedo_color = Color(0.6, 0.65, 0.72)
			s.metallic = 1.0
			s.roughness = 0.3
	return s


## The prop mesh (key) that floating object i uses for game g: shares follow the game's "share" values.
func _prop_for(g: int, i: int) -> String:
	var props: Array = GameRegistry.GAMES[g].get("props", [])
	var x := float((i * 7919) % 100) / 100.0
	var acc := 0.0
	for prop in props:
		acc += prop[2]
		if x < acc:
			return prop[0]
	return props.back()[0]


func _multimesh(path: String, count: int, mat: Material) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	if path.ends_with(".glb"):  # a game model: its first mesh, with the materials made in Blender
		var root := (load(path) as PackedScene).instantiate()
		for n in root.find_children("*", "MeshInstance3D", true, false):
			mm.mesh = (n as MeshInstance3D).mesh
			break
		root.free()
	else:
		mm.mesh = load(path)
	mm.instance_count = count
	var inst := MultiMeshInstance3D.new()
	inst.multimesh = mm
	if mat:
		inst.material_override = mat
	add_child(inst)
	return inst


func _process(delta: float) -> void:
	_time += delta
	for key in _prop_mm:
		_prop_count[key] = 0
	_morph_t += delta
	for i in _seeds.size():
		var s := _seeds[i]
		# rise through a band taller than the view; shrink away near its ends so nothing pops in or out
		var rise := fmod(s.y + 8.0 + _time * (0.15 + s.w * 0.2) + s.w * 20.0, 18.0) - 9.0
		var p := Vector3(s.x + sin(_time * 0.2 + s.w * 9.0) * 0.6, rise, s.z)
		var edge := smoothstep(0.0, 2.5, 9.0 - absf(rise))
		# morph: each object shrinks, swaps shape and pops back, with a small stagger between objects
		var k := clampf((_morph_t - s.w * 0.45) / 0.35, 0.0, 1.0)
		var key := _prop_for(_selected, i) if k >= 0.5 else _prop_for(_previous, i)
		var grow := absf(k * 2.0 - 1.0)
		grow = 1.0 - pow(1.0 - grow, 3.0)
		var spin := _time * (0.3 + s.w) + k * TAU
		var b := Basis(Vector3(s.w, 1.0, 0.3).normalized(), spin).scaled(Vector3.ONE * (0.6 + s.w * 0.8) * maxf(grow * edge, 0.001))
		var mm: MultiMesh = _prop_mm[key].multimesh
		mm.set_instance_transform(_prop_count[key], Transform3D(b, p))
		_prop_count[key] += 1
	for key in _prop_mm:
		_prop_mm[key].multimesh.visible_instance_count = _prop_count[key]
	_camera.position = Vector3(sin(_time * 0.07) * 1.2, cos(_time * 0.05) * 0.5, 9.0)
	_camera.look_at(Vector3(0, 0, -3))
	for i in _cards.size():
		var target := 1.08 if i == _selected else (0.98 if i == _hovered_card else 0.92)
		var c := _cards[i]
		c.scale = c.scale.lerp(Vector2.ONE * target, 1.0 - exp(-delta * 10.0))
		c.modulate.a = lerpf(c.modulate.a, 1.0 if i == _selected else (0.8 if i == _hovered_card else 0.55),
			1.0 - exp(-delta * 8.0))


# ------------------------------------------------------------------ UI

func _font(narrow: bool = true) -> Font:
	return load("res://core/fonts/kenney_future_narrow.ttf" if narrow else "res://core/fonts/kenney_future.ttf")


func _label(text: String, size: int, color: Color, narrow: bool = true) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", _font(narrow))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_constant_override("outline_size", maxi(4, size / 10))
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	return l


func _panel_style(border: Color, radius: int = 18) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = PANEL
	sb.border_color = border
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(radius)
	sb.shadow_color = Color(0, 0, 0, 0.5)
	sb.shadow_size = 16
	sb.content_margin_left = 22
	sb.content_margin_right = 22
	sb.content_margin_top = 16
	sb.content_margin_bottom = 16
	return sb


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_ui = Control.new()
	_ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_ui)

	var vignette := ColorRect.new()
	vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var vs := ShaderMaterial.new()
	vs.shader = Shader.new()
	vs.shader.code = """shader_type canvas_item;
void fragment() { vec2 d = UV - 0.5; COLOR = vec4(0.0, 0.0, 0.0, smoothstep(0.35, 0.85, length(d * vec2(1.2, 1.0))) * 0.85); }"""
	vignette.material = vs
	_ui.add_child(vignette)

	var title := _label("SECOND CREDIT", 104, GOLD, false)
	title.position = Vector2(110, 90)
	_ui.add_child(title)
	var sub := _label("free remakes of games that deserve another go", 30, Color(0.8, 0.85, 0.95))
	sub.position = Vector2(116, 225)
	_ui.add_child(sub)

	var menu := VBoxContainer.new()
	menu.position = Vector2(116, 350)
	menu.add_theme_constant_override("separation", 14)
	_ui.add_child(menu)
	for i in 4:
		var name: String = ["PLAY", "SETTINGS", "CREDITS", "QUIT"][i]
		var b := Button.new()
		b.text = name
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(380, 70)
		b.add_theme_font_override("font", _font(false))
		b.add_theme_font_size_override("font_size", 40)
		b.add_theme_color_override("font_color", Color(0.85, 0.87, 0.95))
		b.add_theme_color_override("font_hover_color", GOLD)
		b.add_theme_color_override("font_focus_color", GOLD)
		var normal := StyleBoxFlat.new()
		normal.bg_color = Color(0, 0, 0, 0)
		normal.content_margin_left = 24
		var focus := _panel_style(GOLD, 12)
		focus.bg_color = Color(1.0, 0.83, 0.35, 0.12)
		for state in ["normal", "pressed", "disabled"]:
			b.add_theme_stylebox_override(state, normal)
		b.add_theme_stylebox_override("hover", focus)
		b.add_theme_stylebox_override("focus", focus)
		b.pressed.connect(_on_menu.bind(i))
		b.mouse_entered.connect(func():
			if not _settings.visible and not _credits.visible:
				_focus_menu(i))
		menu.add_child(b)
		_buttons.append(b)

	var hint := _label("arrows or gamepad to choose    enter to confirm    esc to go back", 22, Color(0.6, 0.65, 0.75))
	hint.position = Vector2(116, 1010)
	_ui.add_child(hint)

	# the cards slide inside a clipped window between the two arrows
	var window := Control.new()
	window.clip_contents = true
	window.position = Vector2(610, 520)
	window.size = Vector2(1170, 530)
	window.mouse_filter = Control.MOUSE_FILTER_PASS
	_ui.add_child(window)
	_card_box = HBoxContainer.new()
	_card_box.position = Vector2(CARD_ROW_X, 40)
	_card_box.add_theme_constant_override("separation", 34)
	window.add_child(_card_box)
	for i in GameRegistry.GAMES.size():
		var card := _make_card(GameRegistry.GAMES[i], i)
		_card_box.add_child(card)
		_cards.append(card)

	for side in [-1, 1]:
		var arrow := Button.new()
		arrow.flat = true
		arrow.focus_mode = Control.FOCUS_NONE
		arrow.custom_minimum_size = Vector2(120, 120)
		arrow.size = Vector2(120, 120)
		arrow.pivot_offset = Vector2(60, 60)
		arrow.position = Vector2(480 if side < 0 else 1790, 725)
		arrow.draw.connect(_draw_arrow.bind(arrow, side))
		arrow.mouse_entered.connect(func(): arrow.queue_redraw(); _play("ui_move"))
		arrow.mouse_exited.connect(arrow.queue_redraw)
		arrow.pressed.connect(func():
			_select_game(_selected + side)
			var tw := create_tween()
			tw.tween_property(arrow, "scale", Vector2.ONE * 0.85, 0.06)
			tw.tween_property(arrow, "scale", Vector2.ONE, 0.12).set_trans(Tween.TRANS_BACK))
		_ui.add_child(arrow)
		_arrows.append(arrow)

	_settings = _build_settings()
	_settings.visible = false
	_ui.add_child(_settings)
	_credits = _build_credits()
	_credits.visible = false
	_ui.add_child(_credits)

	_fade = ColorRect.new()
	_fade.color = Color.BLACK
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.add_child(_fade)


func _make_card(g: Dictionary, index: int) -> Control:
	var playable: bool = g["scene"] != ""
	var accent: Color = g["accent"]
	var card := PanelContainer.new()
	card.custom_minimum_size = Vector2(380, 430)
	card.pivot_offset = Vector2(190, 215)
	card.add_theme_stylebox_override("panel", _panel_style(accent if playable else Color(0.4, 0.4, 0.5)))
	card.mouse_entered.connect(func(): _hovered_card = index)
	card.mouse_exited.connect(func(): if _hovered_card == index: _hovered_card = -1)
	card.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			if _selected == index:
				_launch()
			else:
				_select_game(index))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	card.add_child(v)
	var pic := TextureRect.new()
	pic.custom_minimum_size = Vector2(336, 220)
	pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	if g["card"] != "":
		pic.texture = load(g["card"])
	else:
		var ph := GradientTexture2D.new()
		var grad := Gradient.new()
		grad.set_color(0, accent.darkened(0.7))
		grad.set_color(1, Color(0.03, 0.03, 0.05))
		ph.gradient = grad
		ph.fill = GradientTexture2D.FILL_RADIAL
		ph.fill_from = Vector2(0.5, 0.4)
		pic.texture = ph
	v.add_child(pic)
	v.add_child(_label(g["title"].to_upper(), 38, accent if playable else Color(0.75, 0.75, 0.8), false))
	var tag := _label(g["tagline"], 22, Color(0.85, 0.87, 0.92))
	tag.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tag.custom_minimum_size = Vector2(336, 0)
	v.add_child(tag)
	v.add_child(_label("inspired by " + g["inspired_by"], 18, Color(0.6, 0.63, 0.72)))
	v.add_child(_label("PRESS ENTER TO PLAY" if playable else "IN DEVELOPMENT", 20,
		GOLD if playable else Color(0.55, 0.55, 0.62)))
	return card


## A round glass button with a chevron; gold when hovered, dimmed when there is nothing more that way.
func _draw_arrow(b: Button, side: int) -> void:
	var c := b.size * 0.5
	var hover := b.is_hovered()
	var can := (_selected + side) >= 0 and (_selected + side) < _cards.size()
	var ring := GOLD if hover and can else Color(1, 1, 1, 0.55 if can else 0.18)
	b.draw_circle(c, 56.0, Color(0.03, 0.03, 0.06, 0.65))
	b.draw_circle(c, 56.0, Color(ring, 0.18 if hover else 0.08))
	b.draw_arc(c, 56.0, 0.0, TAU, 64, ring, 4.0, true)
	var d := float(side)
	var pts := PackedVector2Array([c + Vector2(-12 * d, -26), c + Vector2(16 * d, 0), c + Vector2(-12 * d, 26)])
	b.draw_polyline(pts, ring, 10.0, true)


func _slider_row(parent: Container, label: String, value: float, on_change: Callable) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 20)
	var l := _label(label, 28, Color(0.9, 0.9, 0.95))
	l.custom_minimum_size = Vector2(240, 0)
	row.add_child(l)
	var s := HSlider.new()
	s.min_value = 0.0
	s.max_value = 1.0
	s.step = 0.05
	s.value = value
	s.custom_minimum_size = Vector2(420, 40)
	s.value_changed.connect(on_change)
	s.value_changed.connect(func(_v): _play("ui_move"))
	row.add_child(s)
	parent.add_child(row)


func _toggle_row(parent: Container, label: String, value: bool, on_change: Callable) -> void:
	var c := CheckButton.new()
	c.text = label
	c.button_pressed = value
	c.add_theme_font_override("font", _font())
	c.add_theme_font_size_override("font_size", 28)
	c.toggled.connect(on_change)
	c.toggled.connect(func(_v): _play("ui_move"))
	parent.add_child(c)


func _build_settings() -> Control:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _panel_style(GOLD))
	panel.position = Vector2(620, 180)
	panel.custom_minimum_size = Vector2(760, 0)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 16)
	panel.add_child(v)
	v.add_child(_label("SETTINGS", 48, GOLD, false))
	v.add_child(_label("these apply to every game", 22, Color(0.65, 0.68, 0.78)))
	for bus in ["Master", "Music", "SFX", "UI"]:
		var name: String = {"Master": "Volume", "Music": "Music", "SFX": "Effects", "UI": "Menus"}[bus]
		_slider_row(v, name, Settings.volume[bus], func(x): Settings.volume[bus] = x; Settings.apply())
	_toggle_row(v, "Fullscreen", Settings.fullscreen, func(x): Settings.fullscreen = x; Settings.apply())
	_toggle_row(v, "Vertical sync", Settings.vsync, func(x): Settings.vsync = x; Settings.apply())
	_toggle_row(v, "Camera shake", Settings.camera_shake, func(x): Settings.camera_shake = x; Settings.apply())
	_toggle_row(v, "Show frame rate", Settings.show_fps, func(x): Settings.show_fps = x; Settings.apply())
	var back := Button.new()
	back.text = "BACK"
	back.add_theme_font_override("font", _font(false))
	back.add_theme_font_size_override("font_size", 30)
	back.pressed.connect(_close_panels)
	v.add_child(back)
	return panel


func _build_credits() -> Control:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _panel_style(GOLD))
	panel.position = Vector2(620, 150)
	panel.custom_minimum_size = Vector2(1150, 820)
	var v := VBoxContainer.new()
	panel.add_child(v)
	v.add_child(_label("CREDITS", 48, GOLD, false))
	var text := RichTextLabel.new()
	text.bbcode_enabled = true
	text.custom_minimum_size = Vector2(1100, 660)
	text.add_theme_font_override("normal_font", _font())
	text.add_theme_font_override("bold_font", _font(false))
	text.add_theme_font_size_override("normal_font_size", 22)
	text.add_theme_font_size_override("bold_font_size", 26)
	text.text = _credits_bbcode()
	v.add_child(text)
	var back := Button.new()
	back.text = "BACK"
	back.add_theme_font_override("font", _font(false))
	back.add_theme_font_size_override("font_size", 30)
	back.pressed.connect(_close_panels)
	v.add_child(back)
	return panel


func _credits_bbcode() -> String:
	var md := FileAccess.get_file_as_string("res://core/ui/credits.md")
	var out := PackedStringArray()
	for line in md.split("\n"):
		var l := line
		l = RegEx.create_from_string("\\*\\*(.+?)\\*\\*").sub(l, "[b]$1[/b]", true)
		l = RegEx.create_from_string("<(https?://[^>]+)>").sub(l, "$1", true)
		l = RegEx.create_from_string("`([^`]+)`").sub(l, "$1", true)
		l = RegEx.create_from_string("\\*([^*]+)\\*").sub(l, "[i]$1[/i]", true)
		if l.begins_with("# "):
			continue
		if l.begins_with("## "):
			l = "\n[color=#ffd35a][b]" + l.substr(3).to_upper() + "[/b][/color]"
		out.append(l)
	return "\n".join(out)


# ------------------------------------------------------------------ navigation

func _load_sounds() -> void:
	for n in ["ui_move", "ui_select", "ui_back", "ui_start"]:
		_sfx[n] = load("res://core/audio/%s.wav" % n)
	_sfx_player = AudioStreamPlayer.new()
	_sfx_player.bus = "UI"
	_sfx_player.max_polyphony = 4
	add_child(_sfx_player)
	_music = AudioStreamPlayer.new()
	var theme: AudioStreamOggVorbis = load("res://core/audio/menu_theme.ogg")
	theme.loop = true
	_music.stream = theme
	_music.bus = "Music"
	_music.volume_db = -40.0
	add_child(_music)
	_music.play()
	create_tween().tween_property(_music, "volume_db", 0.0, 2.5).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)


func _play(name: String) -> void:
	_sfx_player.stream = _sfx[name]
	_sfx_player.play()


func _focus_menu(i: int, sound: bool = true) -> void:
	if i != _menu_index and sound:
		_play("ui_move")
	_menu_index = i
	_buttons[i].grab_focus()


func _select_game(i: int, sound: bool = true) -> void:
	i = clampi(i, 0, _cards.size() - 1)
	if i != _selected and sound:
		_play("ui_move")
	if i != _selected:
		_previous = _selected
		_morph_t = 0.0
	_selected = i
	for a in _arrows:
		a.queue_redraw()
	var tw := create_tween()
	tw.tween_property(_card_box, "position:x", CARD_ROW_X - i * 414.0, 0.35) \
		.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


func _unhandled_input(event: InputEvent) -> void:
	if _launching or not event.is_pressed():
		return
	if _settings.visible or _credits.visible:
		if event.is_action("ui_cancel"):
			_close_panels()
			get_viewport().set_input_as_handled()
		return
	if event.is_action("ui_left"):
		_select_game(_selected - 1)
	elif event.is_action("ui_right"):
		_select_game(_selected + 1)
	elif event.is_action("ui_cancel"):
		_play("ui_back")
		_focus_menu(3)
	else:
		return
	get_viewport().set_input_as_handled()


func _on_menu(i: int) -> void:
	match i:
		0:
			_launch()
		1:
			_open_panel(_settings)
		2:
			_open_panel(_credits)
		3:
			_play("ui_back")
			Settings.save_settings()
			get_tree().quit()


func _open_panel(panel: Control) -> void:
	_play("ui_select")
	panel.visible = true
	panel.modulate.a = 0.0
	create_tween().tween_property(panel, "modulate:a", 1.0, 0.2)
	_show_cards(false)
	for b in _buttons:
		b.focus_mode = Control.FOCUS_NONE
	# keyboard focus goes to the first control of the panel
	for c in panel.find_children("*", "Control", true, false):
		if (c is Slider or c is BaseButton or c is RichTextLabel) and (c as Control).focus_mode != Control.FOCUS_NONE:
			(c as Control).grab_focus()
			break


func _close_panels() -> void:
	_play("ui_back")
	Settings.save_settings()
	_settings.visible = false
	_credits.visible = false
	_show_cards(true)
	for b in _buttons:
		b.focus_mode = Control.FOCUS_ALL
	_focus_menu(_menu_index, false)


func _show_cards(show: bool) -> void:
	var tw := create_tween().set_parallel(true)
	tw.tween_property(_card_box, "modulate:a", 1.0 if show else 0.0, 0.25)
	for a in _arrows:
		a.visible = show
	_card_box.mouse_filter = Control.MOUSE_FILTER_PASS if show else Control.MOUSE_FILTER_IGNORE
	for c in _cards:
		c.mouse_filter = Control.MOUSE_FILTER_STOP if show else Control.MOUSE_FILTER_IGNORE


func _launch() -> void:
	var g: Dictionary = GameRegistry.GAMES[_selected]
	if g["scene"] == "":
		_play("ui_back")
		var c := _cards[_selected]
		var tw := create_tween()
		tw.tween_property(c, "rotation", 0.05, 0.05)
		tw.tween_property(c, "rotation", -0.05, 0.08)
		tw.tween_property(c, "rotation", 0.0, 0.05)
		return
	_launching = true
	_play("ui_start")
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 1.0, 0.6)
	tw.parallel().tween_property(_music, "volume_db", -40.0, 0.6)
	tw.tween_callback(func(): LoadingScreen.go(g["scene"], g["title"]))


func _fade_from_black() -> void:
	_fade.color.a = 1.0
	create_tween().tween_property(_fade, "color:a", 0.0, 0.8)
