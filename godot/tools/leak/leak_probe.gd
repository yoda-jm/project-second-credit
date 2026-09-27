extends Node
## Leak probe: runs one game scene in demo mode and prints object, node and resource counts and static memory at a
## few moments, so a steady climb shows. Usage (user arguments): --scene=res://... --frames=N [other game arguments].

var _scene := ""
var _frames := 3600
var _f := 0
var _marks: Array[int] = []
var _every := 0


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--scene="): _scene = a.substr(8)
		elif a.begins_with("--frames="): _frames = int(a.substr(9))
		elif a.begins_with("--every="): _every = int(a.substr(8))
	_marks = [1, _frames / 6, _frames / 2, _frames]
	print("LEAK before f=0 static_mb=%.1f" % (Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0))
	add_child((load(_scene) as PackedScene).instantiate())


func _process(_d: float) -> void:
	_f += 1
	if _f in _marks or (_every > 0 and _f % _every == 0):
		print("LEAK %s f=%d objects=%d nodes=%d resources=%d orphans=%d static_mb=%.1f" % [_scene.get_file(), _f,
			Performance.get_monitor(Performance.OBJECT_COUNT), Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
			Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT), Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT),
			Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0])
	if _f >= _frames:
		get_tree().quit()
