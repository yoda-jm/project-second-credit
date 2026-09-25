extends Node
## Runs a scene and saves selected frames as PNG, then quits. Driven by tools/capture.sh:
##   godot --path godot --fixed-fps 60 res://tools/capture/capture.tscn -- --scene=res://x.tscn --frames=60 --every=60 --out=/abs/dir
## Frames are counted from the end: frame N (the last) is always saved, then N-every, N-2*every, ...

var _frames: int = 60
var _every: int = 60
var _out: String = ""
var _frame: int = 0


func _ready() -> void:
	var scene_path: String = ProjectSettings.get_setting("application/run/main_scene")
	for arg in OS.get_cmdline_user_args():
		var kv := arg.trim_prefix("--").split("=", true, 1)
		if kv.size() != 2:
			continue
		match kv[0]:
			"scene": scene_path = kv[1]
			"frames": _frames = maxi(1, kv[1].to_int())
			"every": _every = maxi(1, kv[1].to_int())
			"out": _out = kv[1]
	if _out.is_empty():
		push_error("capture: --out=<dir> is required")
		get_tree().quit(2)
		return
	DirAccess.make_dir_recursive_absolute(_out)
	var packed := load(scene_path) as PackedScene
	if packed == null:
		push_error("capture: cannot load %s" % scene_path)
		get_tree().quit(2)
		return
	# Make the captured scene the current scene, as if it had been run directly.
	var scene := packed.instantiate()
	get_tree().root.add_child.call_deferred(scene)
	(func() -> void: get_tree().current_scene = scene).call_deferred()


func _process(_delta: float) -> void:
	_frame += 1
	if (_frames - _frame) % _every == 0:
		await RenderingServer.frame_post_draw
		var image := get_viewport().get_texture().get_image()
		image.save_png(_out.path_join("frame%05d.png" % _frame))
	if _frame >= _frames:
		get_tree().quit()
