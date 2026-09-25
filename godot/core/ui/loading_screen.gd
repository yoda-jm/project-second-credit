class_name LoadingScreen
extends Node
## Loads a game scene in a background thread with a progress bar, then builds it behind the loading screen
## (paused) until its shaders are compiled and frames come smoothly, then fades in and lets it run. The first
## launch on a machine takes longer (shader cache); the screen says so. Use LoadingScreen.go(scene_path).

const SCENE := "res://core/ui/loading_screen.tscn"
const GOLD := Color(1.0, 0.83, 0.35)

static var target := ""
static var target_title := ""

var _phase := "load"  ## load, warm, fade
var _progress := 0.0
var _time := 0.0
var _smooth_frames := 0
var _warm_frames := 0
var _game: Node
var _layer: CanvasLayer
var _draw: Control
var _alpha := 1.0


static func go(scene_path: String, title: String = "") -> void:
	target = scene_path
	target_title = title
	(Engine.get_main_loop() as SceneTree).change_scene_to_file(SCENE)


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_layer = CanvasLayer.new()
	_layer.layer = 90
	add_child(_layer)
	_draw = Control.new()
	_draw.set_anchors_preset(Control.PRESET_FULL_RECT)
	_draw.draw.connect(_on_draw)
	_layer.add_child(_draw)
	if target == "":
		target = "res://core/ui/launcher.tscn"
	ResourceLoader.load_threaded_request(target, "", true)


func _process(delta: float) -> void:
	_time += delta
	match _phase:
		"load":
			var p := []
			var status := ResourceLoader.load_threaded_get_status(target, p)
			if not p.is_empty():
				_progress = maxf(_progress, p[0] * 0.6)
			if status == ResourceLoader.THREAD_LOAD_LOADED:
				var packed: PackedScene = ResourceLoader.load_threaded_get(target)
				get_tree().paused = true
				_game = packed.instantiate()
				add_child(_game)
				_phase = "warm"
			elif status == ResourceLoader.THREAD_LOAD_FAILED or status == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
				push_error("could not load " + target)
				get_tree().paused = false
				get_tree().change_scene_to_file("res://core/ui/launcher.tscn")
		"warm":
			# the game renders (paused) under the overlay; wait until frames come fast enough
			_warm_frames += 1
			if delta < 0.05:
				_smooth_frames += 1
			else:
				_smooth_frames = 0
			_progress = maxf(_progress, 0.6 + 0.4 * clampf(float(_smooth_frames) / 12.0, 0.0, 1.0))
			if (_warm_frames > 20 and _smooth_frames >= 12) or _warm_frames > 3000:
				_progress = 1.0
				_phase = "fade"
				get_tree().paused = false
		"fade":
			_alpha = maxf(0.0, _alpha - delta * 2.5)
			if _alpha <= 0.0:
				_layer.queue_free()
				set_process(false)
	_draw.queue_redraw()


func _on_draw() -> void:
	var vp := _draw.get_viewport_rect().size
	var font: Font = load("res://core/fonts/kenney_future.ttf")
	var narrow: Font = load("res://core/fonts/kenney_future_narrow.ttf")
	_draw.draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.02, 0.04, _alpha))
	var c := vp * 0.5
	# a spinning gem
	for i in 3:
		var a := _time * 2.2 + i * TAU / 3.0
		var p := c + Vector2(cos(a), sin(a)) * 46.0 - Vector2(0, 90)
		var r := 12.0
		_draw.draw_colored_polygon(PackedVector2Array([p + Vector2(0, -r), p + Vector2(r * 0.8, 0), p + Vector2(0, r),
			p + Vector2(-r * 0.8, 0)]), Color(0.4, 0.9, 1.0, _alpha * (0.5 + 0.5 * sin(_time * 3.0 + i))))
	var title := target_title.to_upper() if target_title != "" else "LOADING"
	var tw := font.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1, 64).x
	_draw.draw_string(font, Vector2(c.x - tw * 0.5, c.y + 20), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 64, Color(GOLD, _alpha))
	var bar := Rect2(c.x - 300, c.y + 60, 600, 12)
	_draw.draw_rect(bar, Color(1, 1, 1, 0.12 * _alpha))
	_draw.draw_rect(Rect2(bar.position, Vector2(bar.size.x * _progress, bar.size.y)), Color(GOLD, _alpha))
	var msg := "loading" if _phase == "load" else "preparing graphics"
	if _phase == "warm" and _time > 3.0:
		msg = "preparing graphics: the first launch takes longer, it is cached afterwards"
	var mw := narrow.get_string_size(msg, HORIZONTAL_ALIGNMENT_LEFT, -1, 26).x
	_draw.draw_string(narrow, Vector2(c.x - mw * 0.5, c.y + 120), msg, HORIZONTAL_ALIGNMENT_LEFT, -1, 26,
		Color(0.8, 0.85, 0.95, _alpha))
