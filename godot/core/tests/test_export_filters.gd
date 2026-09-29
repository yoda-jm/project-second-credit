extends GdUnitTestSuite
## Every data file a game reads at run time (levels, walls, mazes, packs) is exported. Godot only packs files it
## imports; the rest must match an export preset's include filter, or a release build starts with no levels (Prism
## Breaker crashed on macOS without its walls).

const SKIP := ["gd", "uid", "tscn", "tres", "gdshader", "gdshaderinc", "import", "md", "txt", "mid"]


func test_every_game_data_file_is_exported() -> void:
	var cf := ConfigFile.new()
	assert_int(cf.load("res://export_presets.cfg")).is_equal(OK)
	var presets := 0
	for s in cf.get_sections():
		if not s.ends_with(".options") and cf.has_section_key(s, "include_filter"):
			presets += 1
			var filters: Array[String] = []
			for f in String(cf.get_value(s, "include_filter")).split(",", false):
				filters.append(f.strip_edges())
			for path in _data_files("res://games"):
				var rel := path.trim_prefix("res://")
				assert_bool(filters.any(func(f: String) -> bool: return rel.matchn(f))) \
					.override_failure_message("%s is not exported by preset %s" % [rel, cf.get_value(s, "name")]).is_true()
	assert_int(presets).is_greater(0)


## Files under a folder that Godot doesn't import itself (no .import beside them), tests and tools left out.
func _data_files(dir: String) -> Array[String]:
	var out: Array[String] = []
	for d in DirAccess.get_directories_at(dir):
		if d not in ["tests", "tools"]:
			out.append_array(_data_files(dir.path_join(d)))
	for f in DirAccess.get_files_at(dir):
		if f.get_extension() not in SKIP and not FileAccess.file_exists(dir.path_join(f) + ".import"):
			out.append(dir.path_join(f))
	return out
