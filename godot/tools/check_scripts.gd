extends SceneTree
## Loads every script under the given folders (default: res://games) and reports parse errors.
## Run: godot --headless --path godot -s res://tools/check_scripts.gd [-- res://folder ...]


var _done := false


func _process(_delta: float) -> bool:
	# run on the first frame: autoload singletons (like Settings) are registered by then
	if not _done:
		_done = true
		_check()
	return false


func _check() -> void:
	var roots := OS.get_cmdline_user_args()
	if roots.is_empty():
		roots = PackedStringArray(["res://games", "res://boot", "res://tools"])
	var failed := 0
	var count := 0
	for r in roots:
		for path in _scripts(r):
			if path == (get_script() as Script).resource_path:
				continue  # reloading the running script would crash
			count += 1
			var s = ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_IGNORE)
			if s == null or not (s as Script).can_instantiate():
				failed += 1
				print("FAILED: ", path)
	print("checked %d scripts, %d failed" % [count, failed])
	quit(1 if failed > 0 else 0)


func _scripts(dir: String) -> PackedStringArray:
	var out := PackedStringArray()
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".gd"):
			out.append(dir.path_join(f))
	for d in DirAccess.get_directories_at(dir):
		out.append_array(_scripts(dir.path_join(d)))
	return out
