class_name SelfUpdate
extends Node
## Puts a newer launcher in place of the running one, then Library.restart() starts it. Per platform:
## - Linux AppImage: the new file is written beside $APPIMAGE and renamed over it (the running copy stays mapped).
## - Windows: the running .exe is renamed to .old (Windows allows that), the new one takes its name; .old goes at
##   the next start.
## - macOS: the new .app is unzipped beside the running one (ditto keeps permissions and the signature), the
##   running one becomes .old, the new one takes its name. Not from a translocated (never moved) app.
## Anywhere else (a plain binary, a read-only folder) the launcher only points at the download page.

signal progress(bytes: int, total: int)
signal done(ok: bool, message: String)

const PART := "user://library/launcher.part"

var _http: HTTPRequest
var _entry := {}


static func platform() -> String:
	if OS.has_feature("web"):
		return "web"
	match OS.get_name():
		"Windows":
			return "windows"
		"macOS":
			return "macos"
		"Linux", "FreeBSD":
			return "linux"
	return OS.get_name().to_lower()


## What gets replaced: the AppImage, the .exe or the .app ("" when this launcher can't replace itself).
static func target() -> String:
	if not OS.has_feature("template"):
		return ""
	match platform():
		"linux":
			return OS.get_environment("APPIMAGE")
		"windows":
			return OS.get_executable_path()
		"macos":
			var exe := OS.get_executable_path()  # .../Second Credit.app/Contents/MacOS/Second Credit
			var app := exe.get_base_dir().get_base_dir().get_base_dir()
			if not app.ends_with(".app") or app.contains("/AppTranslocation/"):
				return ""
			return app
	return ""


static func supported() -> bool:
	var t := target()
	if t == "":
		return false
	# the folder must be writable: try a file beside it
	var probe := t.get_base_dir().path_join(".second-credit-write-test")
	var f := FileAccess.open(probe, FileAccess.WRITE)
	if f == null:
		return false
	f.close()
	DirAccess.remove_absolute(probe)
	return true


## Removes what an update left behind (the previous .exe or .app).
static func tidy() -> void:
	var t := target()
	if t == "":
		return
	if platform() == "windows" and FileAccess.file_exists(t + ".old"):
		DirAccess.remove_absolute(t + ".old")
	elif platform() == "macos" and DirAccess.dir_exists_absolute(t + ".old"):
		OS.execute("rm", ["-rf", t + ".old"])


## Starts this launcher again (the new file, once replaced) with the same arguments, and quits.
static func relaunch() -> void:
	var user := Array(OS.get_cmdline_user_args())
	if "--relaunched" not in user:
		user.append("--relaunched")
	var engine := Array(OS.get_cmdline_args())
	if DisplayServer.get_name() == "headless" and "--headless" not in engine:
		engine.append("--headless")  # not among the arguments Godot hands back
	var args := engine + ["--"] + user
	var t := target()
	match platform():
		"macos":
			if t != "":
				OS.create_process("open", ["-n", t, "--args"] + args)
			else:
				OS.create_process(OS.get_executable_path(), args)
		"linux":
			OS.create_process(t if t != "" else OS.get_executable_path(), args)
		_:
			OS.create_process(OS.get_executable_path(), args)
	(Engine.get_main_loop() as SceneTree).quit()


func start(url: String, entry: Dictionary) -> void:
	_entry = entry
	_http = HTTPRequest.new()
	_http.use_threads = true
	_http.max_redirects = 8
	_http.download_chunk_size = 1 << 22
	_http.download_file = PART
	_http.body_size_limit = int(entry.get("size", 0)) + 1_000_000
	add_child(_http)
	_http.request_completed.connect(_on_done)
	if _http.request(url) != OK:
		done.emit(false, "could not start the download")


func _process(_delta: float) -> void:
	if _http:
		progress.emit(_http.get_downloaded_bytes(), maxi(_http.get_body_size(), int(_entry.get("size", 0))))


func _on_done(result: int, code: int, _h: PackedStringArray, _b: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		DirAccess.remove_absolute(PART)
		done.emit(false, "the download failed")
		return
	if not Library._file_ok(PART, _entry):
		DirAccess.remove_absolute(PART)
		done.emit(false, "the download was damaged")
		return
	var err := _apply(ProjectSettings.globalize_path(PART))
	DirAccess.remove_absolute(PART)
	done.emit(err == "", err)


## Puts the downloaded file in place; returns "" or what went wrong.
func _apply(part: String) -> String:
	var t := target()
	match platform():
		"linux":
			var tmp := t + ".new"
			if DirAccess.copy_absolute(part, tmp) != OK:
				return "could not write beside the launcher"
			OS.execute("chmod", ["+x", tmp])
			if DirAccess.rename_absolute(tmp, t) != OK:
				DirAccess.remove_absolute(tmp)
				return "could not replace the launcher"
			return ""
		"windows":
			var zip := ZIPReader.new()
			if zip.open(part) != OK:
				return "the download is not a zip"
			var name := ""
			for f in zip.get_files():
				if f.get_extension().to_lower() == "exe":
					name = f
			if name == "":
				return "no program in the download"
			var bytes := zip.read_file(name)
			zip.close()
			var tmp := t + ".new"
			var out := FileAccess.open(tmp, FileAccess.WRITE)
			if out == null:
				return "could not write beside the launcher"
			out.store_buffer(bytes)
			out.close()
			DirAccess.remove_absolute(t + ".old")
			if DirAccess.rename_absolute(t, t + ".old") != OK:
				DirAccess.remove_absolute(tmp)
				return "could not move the running launcher aside"
			if DirAccess.rename_absolute(tmp, t) != OK:
				DirAccess.rename_absolute(t + ".old", t)
				return "could not replace the launcher"
			return ""
		"macos":
			var dir := t.get_base_dir().path_join(".second-credit-update")
			OS.execute("rm", ["-rf", dir])
			if OS.execute("ditto", ["-x", "-k", part, dir]) != 0:
				return "could not unpack the download"
			var app := ""
			for d in DirAccess.get_directories_at(dir):
				if d.ends_with(".app"):
					app = dir.path_join(d)
			if app == "":
				OS.execute("rm", ["-rf", dir])
				return "no app in the download"
			OS.execute("xattr", ["-dr", "com.apple.quarantine", app])
			OS.execute("rm", ["-rf", t + ".old"])
			if DirAccess.rename_absolute(t, t + ".old") != OK:
				OS.execute("rm", ["-rf", dir])
				return "could not move the running app aside"
			if DirAccess.rename_absolute(app, t) != OK:
				DirAccess.rename_absolute(t + ".old", t)
				OS.execute("rm", ["-rf", dir])
				return "could not replace the app"
			OS.execute("rm", ["-rf", dir])
			return ""
	return "this launcher can't update itself here"
