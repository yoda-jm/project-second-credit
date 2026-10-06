extends Node
## The collection's front door: a 3D backdrop of drifting gems, the title, the game cards and the main menu
## (Play, Library, Settings, Credits, Quit). Games not downloaded yet show it on their card (floppy disks and clouds
## float behind them) and download on Enter; the library (LibraryUI, U) updates them (docs/updater.md). Keyboard, gamepad and mouse all work. Games return here from their pause
## menu. Pass "--game=<id>" (user argument) to jump straight into a game.

const GOLD := Color(1.0, 0.83, 0.35)
const MENU := ["PLAY", "LIBRARY", "SETTINGS", "CREDITS", "QUIT"]
const PANEL := Color(0.05, 0.05, 0.09, 0.72)

var _selected := 0
var _menu_index := 0
var _buttons: Array[Button] = []
var _cards: Array[Control] = []
var _chip_hint: Label
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
var _prop_norm := {}  ## mesh path -> scale that brings the prop to a common size
var _prop_count := {}
var _previous := 0
var _morph_t := 10.0
var _camera: Camera3D
var _time := 0.0
var _seeds: Array[Vector4] = []
var _launching := false
var _arrows: Array[Button] = []
var _style := ""  ## "" shows every game; otherwise only the games of that style
var _chips: Array[Button] = []
var _hovered_card := -1
const CARD_ROW_X := 395.0  ## places the selected card in the middle of the card window
const WINDOW_W := 1170.0
var _center_tween: Tween
static var _deep_linked := false  ## "--game=<id>" (on the web ?game=<id>) has been followed
var _card_status: Array[Label] = []
var _card_chip: Array[Label] = []
var _card_bar: Array[ProgressBar] = []
var _card_veil: Array[Control] = []
var _library: LibraryUI
var _play_when_ready := ""  ## the game to start as soon as its download is done
var _from_keys: Array[String] = []  ## the prop each floating object showed before the current morph
## what floats behind a game that isn't on this computer yet
const DOWNLOAD_PROPS := [["res://core/art/props/floppy_teal.glb", "model", 0.28], ["res://core/art/props/floppy_pink.glb", "model", 0.28],
	["res://core/art/props/cloud.glb", "model", 0.3], ["res://core/art/props/download_arrow.glb", "model", 0.2]]


func _ready() -> void:
	var deep_link := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--game=") and not _deep_linked:  # once per run: the launcher comes back after the game
			_deep_linked = true
			var g := GameRegistry.find(arg.substr(7))
			if not g.is_empty() and g["scene"] != "":
				if Library.state(g) == LibraryCatalog.READY:
					LoadingScreen.go.call_deferred(g["scene"], g["title"])
					return
				deep_link = g["id"]  # to download first (the web build): the launcher shows its card meanwhile
	_build_backdrop()
	_build_ui()
	_load_sounds()
	var start := 0
	for gi in GameRegistry.GAMES.size():
		if GameRegistry.GAMES[gi]["id"] == Settings.last_game:
			start = gi
	_selected = start
	_previous = start
	_card_box.position.x = CARD_ROW_X - start * 414.0  # back on the game played last, without sliding
	# exact once the row has been laid out (only then do the cards know their widths)
	_card_box.sort_children.connect(func():
		if _center_tween:
			_center_tween.kill()
		_card_box.position.x = _row_x(_selected), CONNECT_ONE_SHOT | CONNECT_DEFERRED)
	if deep_link != "":
		start = GameRegistry.GAMES.find(GameRegistry.find(deep_link))
		_card_box.position.x = CARD_ROW_X - start * 414.0
	_select_game(start, false)
	_focus_menu(0, false)
	if deep_link != "":
		_follow_link(deep_link)
	if OS.has_feature("web") and deep_link == "":
		Library.changed.connect(_web_pick)
		_web_pick()
	_fade_from_black()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--select="):  # for captures: change card after a second
			get_tree().create_timer(1.0).timeout.connect(_select_game.bind(int(arg.substr(9))))
		if arg == "--open-library":  # for captures: the library panel after two seconds
			get_tree().create_timer(2.0).timeout.connect(_library.open_panel)


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
		_seeds.append(Vector4(rng.randf_range(-13, 13), rng.randf_range(-7, 7), rng.randf_range(-17, -4), rng.randf()))
	# one multimesh per distinct prop of every game; each floating object picks its shape from the selected game
	_add_props(DOWNLOAD_PROPS)
	for g in GameRegistry.GAMES:
		_add_props(g.get("props", []))
	_from_keys.resize(PROP_COUNT)


func _add_props(props: Array) -> void:
	for prop in props:
		var key: String = prop[0]
		if not ResourceLoader.exists(key):
			continue   # a model not made yet, or a game not downloaded: it floats other props
		if not _prop_mm.has(key):
			var mmi := _multimesh(key, PROP_COUNT, _prop_material(prop[1]))
			if mmi:
				_prop_mm[key] = mmi


func _prop_material(kind: String) -> Material:
	if kind == "model":
		return null
	if kind == "stone":
		var st := Pbr.material("stone_bricks", Color(1.0, 0.96, 0.9), 1.4).duplicate() as StandardMaterial3D
		st.uv1_world_triplanar = false  # the texture must travel and spin with each floating brick
		return st
	if kind == "gem":
		var m := ShaderMaterial.new()
		m.shader = load("res://core/art/shaders/gem.gdshader")  # a copy of Glimmerdeep's: the launcher ships without the games
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
	if not _has_props(g):
		props = DOWNLOAD_PROPS
	var x := float((i * 7919) % 100) / 100.0
	var acc := 0.0
	for prop in props:
		acc += prop[2]
		if x < acc:
			return prop[0]
	return props.back()[0]


## Whether game g is on this computer with its models loaded (otherwise the download props float behind it).
func _has_props(g: int) -> bool:
	var props: Array = GameRegistry.GAMES[g].get("props", [])
	if props.is_empty() or not Library.state(GameRegistry.GAMES[g]) in [LibraryCatalog.READY, LibraryCatalog.UPDATE, LibraryCatalog.IN_DEVELOPMENT]:
		return false
	return props.any(func(p): return _prop_mm.has(p[0]))


## The floating objects change shape from what they show now to what the selected game shows.
func _begin_morph() -> void:
	for i in PROP_COUNT:
		_from_keys[i] = _prop_for(_selected, i)
	_morph_t = 0.0


func _multimesh(path: String, count: int, mat: Material) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	if path.ends_with(".glb"):  # a game model: its first mesh, with the materials made in Blender
		var ps := load(path) as PackedScene
		if ps == null:
			return null   # there but not imported yet
		var root := ps.instantiate()
		for n in root.find_children("*", "MeshInstance3D", true, false):
			mm.mesh = (n as MeshInstance3D).mesh
			break
		root.free()
	else:
		mm.mesh = load(path)
	mm.instance_count = count
	# every prop floats at about the same size, whatever its size in its own game (a gem, a podium, a tank)
	_prop_norm[path] = 1.7 / maxf(0.05, mm.mesh.get_aabb().get_longest_axis_size()) if mm.mesh else 1.0
	var inst := MultiMeshInstance3D.new()
	inst.multimesh = mm
	if mat:
		inst.material_override = mat
	add_child(inst)
	return inst


func _process(delta: float) -> void:
	_time += delta
	if Library.busy() and Engine.get_process_frames() % 12 == 0:
		_refresh_cards()  # the progress bar
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
		var key := _prop_for(_selected, i) if k >= 0.5 or _from_keys[i] == "" else _from_keys[i]
		var grow := absf(k * 2.0 - 1.0)
		grow = 1.0 - pow(1.0 - grow, 3.0)
		var spin := _time * (0.3 + s.w) + k * TAU
		var b := Basis(Vector3(s.w, 1.0, 0.3).normalized(), spin).scaled(Vector3.ONE * (0.6 + s.w * 0.8) * _prop_norm.get(key, 1.0) * maxf(grow * edge, 0.001))
		if not _prop_mm.has(key):
			continue
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
	for i in (MENU.size() - 1 if OS.has_feature("web") else MENU.size()):  # in a browser there is nowhere to quit to
		var name: String = MENU[i]
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
			if not _settings.visible and not _credits.visible and not _library.is_open():
				_focus_menu(i))
		menu.add_child(b)
		_buttons.append(b)

	var hint := _label("arrows or gamepad to choose    tab or q / e to filter    u for the library    enter to confirm", 22,
		Color(0.6, 0.65, 0.75))
	hint.position = Vector2(116, 1010)
	_ui.add_child(hint)

	# style chips: browse the collection by kind of game
	var chip_row := HBoxContainer.new()
	chip_row.position = Vector2(620, 488)
	chip_row.add_theme_constant_override("separation", 12)
	_ui.add_child(chip_row)
	for st in [""] + GameRegistry.styles():
		var chip := Button.new()
		chip.text = "ALL GAMES" if st == "" else st.to_upper()
		chip.focus_mode = Control.FOCUS_NONE
		chip.add_theme_font_override("font", _font())
		chip.add_theme_font_size_override("font_size", 20)
		chip.pressed.connect(_set_style.bind(st))
		chip.set_meta("style", st)
		chip_row.add_child(chip)
		_chips.append(chip)
	_style_chips()
	var filter_hint := _label("TAB  or  Q / E", 18, Color(0.6, 0.65, 0.75))  # how to change the filter, after the chips
	filter_hint.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	chip_row.add_child(filter_hint)
	_chip_hint = filter_hint

	# the cards slide inside a clipped window between the two arrows
	var window := Control.new()
	window.clip_contents = true
	window.position = Vector2(610, 520)
	window.size = Vector2(WINDOW_W, 530)
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
			_step(side)
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
	_library = LibraryUI.new(self)
	_ui.add_child(_library)
	_library.play_requested.connect(_play_game)
	Library.changed.connect(_refresh_cards)
	Library.finished.connect(_on_downloaded)
	_refresh_cards()

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
	if g.get("card", "") != "":
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
	var chip := _label("", 18, Color.WHITE)
	var chip_box := PanelContainer.new()
	var csb := StyleBoxFlat.new()
	csb.bg_color = Color(0.03, 0.03, 0.06, 0.85)
	csb.set_corner_radius_all(14)
	csb.set_border_width_all(2)
	csb.content_margin_left = 12
	csb.content_margin_right = 12
	csb.content_margin_top = 3
	csb.content_margin_bottom = 3
	chip_box.add_theme_stylebox_override("panel", csb)
	chip_box.position = Vector2(10, 10)
	chip_box.add_child(chip)
	# over the picture: what stands between the player and the game (download, new version, progress)
	var veil := Control.new()
	veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	veil.mouse_filter = Control.MOUSE_FILTER_IGNORE
	veil.draw.connect(_draw_veil.bind(veil, index))
	pic.add_child(veil)
	_card_veil.append(veil)
	pic.add_child(chip_box)
	_card_chip.append(chip)
	v.add_child(_label(g["title"].to_upper(), 38, accent if playable else Color(0.75, 0.75, 0.8), false))
	var tag := _label(g["tagline"], 22, Color(0.85, 0.87, 0.92))
	tag.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tag.custom_minimum_size = Vector2(336, 0)
	v.add_child(tag)
	v.add_child(_label("inspired by " + g["inspired_by"], 18, Color(0.6, 0.63, 0.72)))
	var status := _label("PRESS ENTER TO PLAY" if playable else "IN DEVELOPMENT", 20,
		GOLD if playable else Color(0.55, 0.55, 0.62))
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.custom_minimum_size = Vector2(336, 0)
	v.add_child(status)
	_card_status.append(status)
	var bar := ProgressBar.new()
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(336, 10)
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(1, 1, 1, 0.1)
	bg.set_corner_radius_all(5)
	var fill := StyleBoxFlat.new()
	fill.bg_color = LibraryUI.TEAL
	fill.set_corner_radius_all(5)
	bar.add_theme_stylebox_override("background", bg)
	bar.add_theme_stylebox_override("fill", fill)
	bar.visible = false
	v.add_child(bar)
	_card_bar.append(bar)
	return card


## Each card says where its game stands: here, new version, to download (and how big), downloading...
func _refresh_cards() -> void:
	for i in _cards.size():
		var g: Dictionary = GameRegistry.GAMES[i]
		var id: String = g["id"]
		var st := Library.state(g)
		var words := LibraryUI.status_text(id)
		var text: String = words[0]
		var color: Color = words[1]
		var chip := ""
		var chip_color := Color.WHITE
		match st:
			LibraryCatalog.READY:
				text = "PRESS ENTER TO PLAY"
				color = GOLD
				if Library.fresh(id):
					chip = "UPDATED"
					chip_color = LibraryUI.LEAF
			LibraryCatalog.UPDATE:
				text = "PRESS ENTER TO PLAY  ·  NEW VERSION OUT"
				color = GOLD
				chip = "NEW VERSION"
				chip_color = GOLD
			LibraryCatalog.MISSING:
				text = ("DIDN'T DOWNLOAD (%s): ENTER TO RETRY" % Library.error(id)).to_upper() if Library.error(id) != "" \
					else "PRESS ENTER TO DOWNLOAD AND PLAY"
				color = LibraryUI.TEAL if Library.error(id) == "" else LibraryUI.RED
			LibraryCatalog.NEEDS_LAUNCHER:
				text = "UPDATE THE LAUNCHER TO GET IT (U)"
		_card_status[i].text = text
		_card_status[i].add_theme_color_override("font_color", color)
		_card_chip[i].text = chip
		_card_chip[i].add_theme_color_override("font_color", chip_color)
		var box := _card_chip[i].get_parent() as PanelContainer
		box.visible = chip != ""
		(box.get_theme_stylebox("panel") as StyleBoxFlat).border_color = chip_color
		_card_bar[i].visible = st == LibraryCatalog.DOWNLOADING and Library._queue.find(id) == 0
		if _card_bar[i].visible:
			var p := Library.progress(id)
			_card_bar[i].value = 100.0 * p[0] / maxf(1.0, p[1])
		_card_veil[i].queue_redraw()


## The card picture's veil: dark with a big download badge and the size (not downloaded), lighter with a gold badge
## (a new version), a filling ring (downloading); nothing when the game is ready.
func _draw_veil(c: Control, i: int) -> void:
	var g: Dictionary = GameRegistry.GAMES[i]
	var id: String = g["id"]
	var st := Library.state(g)
	if st in [LibraryCatalog.READY, LibraryCatalog.IN_DEVELOPMENT]:
		return
	var ring := LibraryUI.TEAL
	var dark := 0.62
	var words := ""
	var progress := -1.0
	match st:
		LibraryCatalog.MISSING:
			words = "DOWNLOAD  ·  %s" % Library.size_text(id) if Library.error(id) == "" else "TRY AGAIN"
			if Library.error(id) != "":
				ring = LibraryUI.RED
		LibraryCatalog.UPDATE:
			ring = GOLD
			dark = 0.3
			words = "NEW VERSION  ·  %s" % Library.size_text(id)
		LibraryCatalog.DOWNLOADING:
			var p := Library.progress(id)
			progress = clampf(float(p[0]) / maxf(1.0, p[1]), 0.0, 1.0)
			words = "WAITING" if Library._queue.find(id) > 0 else "%s / %s" % [LibraryCatalog.size_text(p[0]), LibraryCatalog.size_text(p[1])]
		LibraryCatalog.NEEDS_LAUNCHER:
			ring = LibraryUI.AMBER
			words = "NEEDS THE NEW LAUNCHER"
		LibraryCatalog.OFFLINE:
			ring = LibraryUI.MUTED
			dark = 0.72
			words = "OFFLINE"
		LibraryCatalog.UNAVAILABLE:
			ring = LibraryUI.MUTED
			dark = 0.72
			words = "IN THE DESKTOP DOWNLOAD" if OS.has_feature("web") else "NOT IN THIS CHANNEL"
	var sz := c.size
	c.draw_rect(Rect2(Vector2.ZERO, sz), Color(0.01, 0.01, 0.03, dark))
	var center := Vector2(sz.x * 0.5, sz.y * 0.5 - 16.0)
	var r := 44.0
	c.draw_circle(center, r, Color(0.02, 0.02, 0.05, 0.85))
	c.draw_arc(center, r, 0.0, TAU, 64, Color(ring, 0.35), 5.0, true)
	if progress >= 0.0:
		c.draw_arc(center, r, -PI * 0.5, -PI * 0.5 + TAU * progress, 64, ring, 6.0, true)
		var pct := "%d%%" % int(progress * 100.0)
		var f := _font(false)
		var w := f.get_string_size(pct, HORIZONTAL_ALIGNMENT_LEFT, -1, 26).x
		c.draw_string(f, center + Vector2(-w * 0.5, 10.0), pct, HORIZONTAL_ALIGNMENT_LEFT, -1, 26, ring)
	else:
		c.draw_arc(center, r, 0.0, TAU, 64, ring, 4.0, true)
		# the arrow into its tray
		var a := center + Vector2(0, -4)
		c.draw_line(a + Vector2(0, -20), a + Vector2(0, 10), ring, 7.0, true)
		c.draw_colored_polygon(PackedVector2Array([a + Vector2(-14, 4), a + Vector2(14, 4), a + Vector2(0, 19)]), ring)
		c.draw_polyline(PackedVector2Array([a + Vector2(-20, 16), a + Vector2(-20, 24), a + Vector2(20, 24), a + Vector2(20, 16)]), ring, 5.0, true)
	var nf := _font()
	var tw := nf.get_string_size(words, HORIZONTAL_ALIGNMENT_LEFT, -1, 24).x
	var tp := Vector2(sz.x * 0.5 - tw * 0.5, center.y + r + 34.0)
	c.draw_string_outline(nf, tp, words, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, 6, Color(0, 0, 0, 0.9))
	c.draw_string(nf, tp, words, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, ring.lightened(0.15))


## A round glass button with a chevron; gold when hovered, dimmed when there is nothing more that way.
func _draw_arrow(b: Button, side: int) -> void:
	var c := b.size * 0.5
	var hover := b.is_hovered()
	var vis := _visible_games()
	var p := vis.find(_selected)
	var can := p + side >= 0 and p + side < vis.size()
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
	if not OS.has_feature("web"):  # the page is always the latest
		_toggle_row(v, "Look for updates at start", Settings.update_check, func(x): Settings.update_check = x; Settings.save_settings())
		_toggle_row(v, "Stable releases only (not every change)", Settings.channel == "stable", func(x):
			Settings.channel = "stable" if x else "latest"
			Settings.save_settings()
			Library.manifest = {}
			Library.check())
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
		_begin_morph()
	_selected = i
	if Settings.last_game != GameRegistry.GAMES[i]["id"]:
		Settings.last_game = GameRegistry.GAMES[i]["id"]
		Settings.save_settings()
	for a in _arrows:
		a.queue_redraw()
	if _center_tween:
		_center_tween.kill()
	if _cards[i].size.x <= 0.0:
		_card_box.position.x = _row_x(i)  # not laid out yet: the first layout centres it exactly
		return
	_center_tween = create_tween()
	_center_tween.tween_property(_card_box, "position:x", _row_x(i), 0.35).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


## Where the row goes so card i sits in the middle of the window, from the card's real place and width (cards are
## not all the same width: a long title widens one).
func _row_x(i: int) -> float:
	var c := _cards[i]
	if c.size.x <= 0.0:
		return CARD_ROW_X - maxi(0, _visible_games().find(i)) * 414.0  # before the first layout
	return WINDOW_W * 0.5 - (c.position.x + c.size.x * 0.5)


## The games shown under the current style, in collection order.
func _visible_games() -> Array[int]:
	var out: Array[int] = []
	for i in GameRegistry.GAMES.size():
		if _style == "" or GameRegistry.GAMES[i].get("style", "") == _style:
			out.append(i)
	return out


func _step(side: int) -> void:
	var vis := _visible_games()
	var p := vis.find(_selected)
	_select_game(vis[clampi(p + side, 0, vis.size() - 1)])


func _set_style(st: String) -> void:
	if st == _style:
		return
	_play("ui_move")
	_style = st
	var vis := _visible_games()
	for i in _cards.size():
		_cards[i].visible = vis.has(i)
	_style_chips()
	_select_game(_selected if vis.has(_selected) else vis[0], false)
	for a in _arrows:
		a.queue_redraw()


func _cycle_style(side: int) -> void:
	var all: Array = [""] + GameRegistry.styles()
	_set_style(all[posmod(all.find(_style) + side, all.size())])


func _style_chips() -> void:
	for chip in _chips:
		var on: bool = chip.get_meta("style") == _style
		for state in ["normal", "hover", "pressed"]:
			var sb := _panel_style(GOLD if on else Color(1, 1, 1, 0.25), 18)
			sb.bg_color = Color(0.1, 0.08, 0.02, 0.85) if on else Color(0.03, 0.03, 0.06, 0.6)
			sb.content_margin_left = 16
			sb.content_margin_right = 16
			sb.content_margin_top = 6
			sb.content_margin_bottom = 6
			chip.add_theme_stylebox_override(state, sb)
		chip.add_theme_color_override("font_color", GOLD if on else Color(0.8, 0.82, 0.9))
		chip.add_theme_color_override("font_hover_color", GOLD)


func _unhandled_input(event: InputEvent) -> void:
	if _launching or not event.is_pressed():
		return
	if _library.is_open():
		if event.is_action("ui_cancel"):
			_library.close()
			get_viewport().set_input_as_handled()
		return
	if _settings.visible or _credits.visible:
		if event.is_action("ui_cancel"):
			_close_panels()
			get_viewport().set_input_as_handled()
		return
	if event.is_action("ui_left"):
		_step(-1)
	elif event.is_action("ui_right"):
		_step(1)
	elif event is InputEventKey and event.keycode in [KEY_TAB, KEY_E, KEY_PAGEDOWN]:
		_cycle_style(-1 if event.shift_pressed else 1)
	elif event is InputEventKey and event.keycode in [KEY_Q, KEY_PAGEUP]:
		_cycle_style(-1)
	elif event is InputEventKey and event.keycode == KEY_U:
		_library.open_panel()
	elif event.is_action("ui_cancel"):
		_play("ui_back")
		_focus_menu(_buttons.size() - 1)
	else:
		return
	get_viewport().set_input_as_handled()


func _on_menu(i: int) -> void:
	match MENU[i]:
		"PLAY":
			_launch()
		"LIBRARY":
			_library.open_panel()
		"SETTINGS":
			_open_panel(_settings)
		"CREDITS":
			_open_panel(_credits)
		"QUIT":
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
	_library.panel.visible = false
	_show_cards(true)
	for b in _buttons:
		b.focus_mode = Control.FOCUS_ALL
	_focus_menu(_menu_index, false)


func _show_cards(show: bool) -> void:
	var tw := create_tween().set_parallel(true)
	tw.tween_property(_card_box, "modulate:a", 1.0 if show else 0.0, 0.25)
	for a in _arrows:
		a.visible = show
	for c in _chips:
		c.visible = show
	if _chip_hint:
		_chip_hint.visible = show
	_card_box.mouse_filter = Control.MOUSE_FILTER_PASS if show else Control.MOUSE_FILTER_IGNORE
	for c in _cards:
		c.mouse_filter = Control.MOUSE_FILTER_STOP if show else Control.MOUSE_FILTER_IGNORE


func _launch() -> void:
	var g: Dictionary = GameRegistry.GAMES[_selected]
	var id: String = g["id"]
	match Library.state(g):
		LibraryCatalog.READY:
			if Library._played.has(id) and Library.restart_needed() and Library.fresh(id):
				_play("ui_select")
				_library.ask_restart(id)
			else:
				_start(g)
		LibraryCatalog.UPDATE:
			_play("ui_select")
			_library.ask_update(id)
		LibraryCatalog.MISSING:
			_download_then_play(id)
		LibraryCatalog.NEEDS_LAUNCHER:
			_library.open_panel()
		_:  # in development, downloading, offline, not offered here: the card shakes
			_play("ui_back")
			var c := _cards[_selected]
			var tw := create_tween()
			tw.tween_property(c, "rotation", 0.05, 0.05)
			tw.tween_property(c, "rotation", -0.05, 0.08)
			tw.tween_property(c, "rotation", 0.0, 0.05)


func _start(g: Dictionary) -> void:
	_launching = true
	_play("ui_start")
	Library.played(g["id"])
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 1.0, 0.6)
	tw.parallel().tween_property(_music, "volume_db", -40.0, 0.6)
	tw.tween_callback(func(): LoadingScreen.go(g["scene"], g["title"]))


## Starts a game from the library panel or the update question (the version on this computer).
func _play_game(id: String) -> void:
	_select_game(GameRegistry.GAMES.find(GameRegistry.find(id)), false)
	if Library.state_of(id) in [LibraryCatalog.READY, LibraryCatalog.UPDATE] and not _launching:
		_start(GameRegistry.find(id))


## Downloads the game (first install or update) and starts it when it's ready, if its card is still selected.
func _download_then_play(id: String) -> void:
	_play("ui_select")
	_play_when_ready = id
	Library.download(id)
	_refresh_cards()


func _on_downloaded(id: String) -> void:
	var gi := GameRegistry.GAMES.find(GameRegistry.find(id))
	_add_props(GameRegistry.GAMES[gi].get("props", []))
	if gi == _selected:
		_begin_morph()  # the floppies and clouds turn into the game's own things
	if id == _play_when_ready:
		_play_when_ready = ""
		if gi == _selected and not _library.is_open() and not _settings.visible and not _credits.visible and not _launching:
			get_tree().create_timer(0.9).timeout.connect(func():
				if _selected == gi and not _launching and not _library.is_open():
					_launch())


## In the browser, start on a game that plays there (the last one played may be in the desktop download only).
func _web_pick() -> void:
	if Library.manifest.is_empty():
		return
	Library.changed.disconnect(_web_pick)
	if Library.state(GameRegistry.GAMES[_selected]) in [LibraryCatalog.UNAVAILABLE, LibraryCatalog.OFFLINE]:
		for i in _visible_games():
			if Library.state(GameRegistry.GAMES[i]) in [LibraryCatalog.READY, LibraryCatalog.MISSING, LibraryCatalog.UPDATE]:
				_select_game(i, false)
				return


## A link to a game not downloaded yet: download it as soon as the channel's list is in, then play it.
func _follow_link(id: String) -> void:
	match Library.state_of(id):
		LibraryCatalog.MISSING, LibraryCatalog.UPDATE:
			_download_then_play(id)
		LibraryCatalog.OFFLINE:
			Library.changed.connect(_follow_link.bind(id), CONNECT_ONE_SHOT)
		LibraryCatalog.READY:
			_launch()


## Back from the update question: keyboard focus returns to the menu.
func _cards_focus_back() -> void:
	_focus_menu(_menu_index, false)


func _fade_from_black() -> void:
	_fade.color.a = 1.0
	create_tween().tween_property(_fade, "color:a", 0.0, 0.8)
