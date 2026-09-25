class_name GdashReference
extends RefCounted
## Finds the local GDash checkout (.tools/ref/gdash, never committed) used by the reference tests.
## Those files include original caves, so the tests using them skip when the checkout is missing.


static func root() -> String:
	return ProjectSettings.globalize_path("res://").path_join("../.tools/ref/gdash").simplify_path()


static func available() -> bool:
	return DirAccess.dir_exists_absolute(root())


## Every BDCFF file in the checkout.
static func bdcff_files() -> PackedStringArray:
	var out := PackedStringArray()
	_collect(root(), out)
	out.sort()
	return out


static func _collect(dir: String, out: PackedStringArray) -> void:
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".bd"):
			out.append(dir.path_join(f))
	for d in DirAccess.get_directories_at(dir):
		if not d.begins_with("."):
			_collect(dir.path_join(d), out)
