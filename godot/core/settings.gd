extends Node
## Global settings shared by every game (autoload "Settings"): audio volumes per bus, display options and
## accessibility. Saved in user://settings.cfg and applied at start.

signal changed

const PATH := "user://settings.cfg"
const BUSES := ["Master", "Music", "SFX", "UI"]

var volume := {"Master": 0.85, "Music": 0.6, "SFX": 0.9, "UI": 0.7}
var fullscreen := false
var vsync := true
var camera_shake := true  ## explosions shake the camera (turn off to reduce motion)
var show_fps := false

var _fps_label: Label


func _ready() -> void:
	for bus in BUSES:
		if AudioServer.get_bus_index(bus) < 0:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, bus)
			AudioServer.set_bus_send(i, "Master")
	load_settings()
	apply()
	var layer := CanvasLayer.new()
	layer.layer = 100
	add_child(layer)
	_fps_label = Label.new()
	_fps_label.position = Vector2(12, 1040)
	layer.add_child(_fps_label)


func _process(_delta: float) -> void:
	_fps_label.visible = show_fps
	if show_fps:
		_fps_label.text = "%d fps" % Engine.get_frames_per_second()


func apply() -> void:
	for bus in BUSES:
		var i := AudioServer.get_bus_index(bus)
		var v: float = volume[bus]
		AudioServer.set_bus_volume_db(i, linear_to_db(maxf(v, 0.0001)))
		AudioServer.set_bus_mute(i, v <= 0.001)
	if not Engine.is_embedded_in_editor() and DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
	changed.emit()


func save_settings() -> void:
	var cf := ConfigFile.new()
	for bus in BUSES:
		cf.set_value("audio", bus, volume[bus])
	cf.set_value("display", "fullscreen", fullscreen)
	cf.set_value("display", "vsync", vsync)
	cf.set_value("display", "show_fps", show_fps)
	cf.set_value("comfort", "camera_shake", camera_shake)
	cf.save(PATH)


func load_settings() -> void:
	var cf := ConfigFile.new()
	if cf.load(PATH) != OK:
		return
	for bus in BUSES:
		volume[bus] = cf.get_value("audio", bus, volume[bus])
	fullscreen = cf.get_value("display", "fullscreen", fullscreen)
	vsync = cf.get_value("display", "vsync", vsync)
	show_fps = cf.get_value("display", "show_fps", show_fps)
	camera_shake = cf.get_value("comfort", "camera_shake", camera_shake)
