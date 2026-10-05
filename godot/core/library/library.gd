extends Node
## The game library (autoload "Library"): which games are on this machine, what the update channel offers, and the
## downloads. Each game is its own .pck (only its own folder) kept in user://library/ and mounted at start; the
## launcher download holds core/ only. Nothing is ever installed without the player asking: a check at start
## finds new versions, the launcher says so, the player picks what to download. Spec: docs/updater.md
##
## Development runs (the editor, tools/test.sh, tools/capture.sh) have every game in res:// and never touch the
## network. "--library-preview" fakes a channel for a look at the launcher's states without one.

signal changed  ## a game's state or the channel changed (cards and the library panel redraw)
signal news(updates: Array, launcher: bool)  ## a check found something new since the last one
signal failed(id: String, message: String)  ## a download didn't work ("" id: the check itself)
signal finished(id: String)  ## a game is downloaded, checked and mounted

const DIR := "user://library/"
const INSTALLED := DIR + "installed.json"
const CACHED := DIR + "manifest.json"
const REPO := "https://github.com/yoda-jm/project-second-credit/releases/"
const CHANNELS := {"latest": REPO + "download/latest/manifest.json", "stable": REPO + "latest/download/manifest.json"}
const STALL_SECONDS := 30.0

var build := {}  ## core/library/build.json of an exported build: build, commit, core, godot, games (bundled versions)
var manifest := {}  ## the channel's manifest (the last one fetched; cached for offline starts)
var installed := {}  ## id -> {version, file, sha256, size, date, fresh}
var dev := true  ## a development run: every game is in res://, no network
var web := false
var checking := false
var launcher_ready := false  ## the new launcher is downloaded and in place: a restart runs it
var _queue: Array[String] = []  ## ids waiting to download, the first one downloading
var _http: HTTPRequest
var _check_http: HTTPRequest
var _progress := {}  ## id -> [bytes, total]
var _stall := 0.0
var _last_bytes := 0
var _errors := {}  ## id -> message of the last failure
var _played := {}  ## ids played this session (their scripts stay loaded: an update needs a restart)
var _restart_needed := false
var _preview := false
var _url := ""
var _bundled := {}  ## ids whose game is inside the launcher download itself (an "all games" build)


func _ready() -> void:
	web = OS.has_feature("web")
	dev = not OS.has_feature("template")
	var args := OS.get_cmdline_user_args()
	_preview = "--library-preview" in args
	for a in args:
		if a.begins_with("--channel-url="):  # tests: a local channel
			_url = a.get_slice("=", 1)
	if dev and not _preview:
		return
	if not _preview:
		var bj = JSON.parse_string(FileAccess.get_file_as_string("res://core/library/build.json"))
		build = bj if bj is Dictionary else {}
	for g in GameRegistry.GAMES:  # before any pack is mounted
		if g["scene"] != "" and ResourceLoader.exists(g["scene"]) and not _preview:
			_bundled[g["id"]] = String(build.get("games", {}).get(g["id"], "bundled"))
	DirAccess.make_dir_recursive_absolute(DIR)
	_load_installed()
	_tidy()
	for id in installed.keys():
		_mount(id)
	var cached = JSON.parse_string(FileAccess.get_file_as_string(CACHED)) if FileAccess.file_exists(CACHED) else null
	if LibraryCatalog.valid_manifest(cached):
		manifest = cached
	if _preview:
		_fake_channel()
		return
	_http = _request(not web)
	_http.request_completed.connect(_on_pack_done)
	_check_http = _request(not web)
	_check_http.timeout = 15.0
	_check_http.request_completed.connect(_on_check_done)
	SelfUpdate.tidy()
	var quiet := "--no-update" in args or "--demo" in args
	if Settings.update_check and not quiet:
		get_tree().create_timer(1.0).timeout.connect(check)


func _request(threads: bool) -> HTTPRequest:
	var r := HTTPRequest.new()
	r.use_threads = threads
	r.max_redirects = 8
	add_child(r)
	return r


# ------------------------------------------------------------------ what the launcher asks

## Where this game stands (LibraryCatalog states).
func state(g: Dictionary) -> String:
	if dev and not _preview:
		return LibraryCatalog.READY if g.get("scene", "") != "" else LibraryCatalog.IN_DEVELOPMENT
	return LibraryCatalog.state(g, _ctx())


func state_of(id: String) -> String:
	return state(GameRegistry.find(id))


func _ctx() -> Dictionary:
	var local := _bundled.duplicate()
	for id in installed:
		local[id] = installed[id]["version"]
	return {"manifest": manifest, "local": local, "core": core(), "web": web, "downloading": _queue}


## This launcher's core serial (0 in development).
func core() -> int:
	return int(build.get("core", 0))


## Bytes to download for a game ("" when unknown).
func size_text(id: String) -> String:
	var n := int(manifest.get("games", {}).get(id, {}).get("size", 0))
	return LibraryCatalog.size_text(n) if n > 0 else ""


## The new version's changes (commit subjects), newest first.
func changes(id: String) -> Array:
	return manifest.get("games", {}).get(id, {}).get("changes", [])


## [bytes, total] of a download in progress.
func progress(id: String) -> Array:
	return _progress.get(id, [0, int(manifest.get("games", {}).get(id, {}).get("size", 0))])


func error(id: String) -> String:
	return _errors.get(id, "")


## Updated since it was last played (the card says so until then).
func fresh(id: String) -> bool:
	return installed.get(id, {}).get("fresh", false)


func updates() -> Array[String]:
	return [] if dev and not _preview else LibraryCatalog.updates(GameRegistry.GAMES, _ctx())


func missing() -> Array[String]:
	return [] if dev and not _preview else LibraryCatalog.missing(GameRegistry.GAMES, _ctx())


func launcher_newer() -> bool:
	return not manifest.is_empty() and LibraryCatalog.launcher_newer(manifest, core()) and (web or not launcher_file().is_empty())


func launcher_file() -> Dictionary:
	return LibraryCatalog.launcher_file(manifest, SelfUpdate.platform())


## Whether this launcher can replace itself here (an AppImage, a writable Windows folder, a moved macOS app).
func can_self_update() -> bool:
	return web or SelfUpdate.supported()


func restart_needed() -> bool:
	return _restart_needed or launcher_ready


## The game was started this session.
func played(id: String) -> void:
	_played[id] = true
	if installed.get(id, {}).get("fresh", false):
		installed[id]["fresh"] = false
		_save_installed()


# ------------------------------------------------------------------ check

## Fetches the channel's manifest (in the background; the launcher never waits for it).
func check() -> void:
	if dev or _preview or checking:
		return
	checking = true
	changed.emit()
	var err := _check_http.request(_manifest_url(), ["Cache-Control: no-cache"])
	if err != OK:
		checking = false
		failed.emit("", "could not reach the update channel")
		changed.emit()


func _manifest_url() -> String:
	if _url != "":
		return _url
	if web:
		var here := str(JavaScriptBridge.eval("location.href.split('?')[0].split('#')[0]"))
		return here.substr(0, here.rfind("/") + 1) + "packs/manifest.json"
	return CHANNELS.get(Settings.channel, CHANNELS["latest"])


func _on_check_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	checking = false
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		failed.emit("", "no connection to the update channel" if result != HTTPRequest.RESULT_SUCCESS else "the update channel answered %d" % code)
		changed.emit()
		return
	var m = JSON.parse_string(body.get_string_from_utf8())
	if not LibraryCatalog.valid_manifest(m):
		failed.emit("", "the update channel sent something unreadable")
		changed.emit()
		return
	manifest = m
	var f := FileAccess.open(CACHED, FileAccess.WRITE)
	if f:
		f.store_string(body.get_string_from_utf8())
		f.close()
	changed.emit()
	# tell about what wasn't told yet this session (the first check: everything pending)
	var now := updates()
	var unseen := now.filter(func(id): return not _told.has(id))
	var launcher := launcher_newer() and not _told.has("launcher")
	if not unseen.is_empty() or launcher:
		for id in now:
			_told[id] = true
		if launcher_newer():
			_told["launcher"] = true
		news.emit(now, launcher_newer())


var _told := {}  ## ids (and "launcher") already announced this session


# ------------------------------------------------------------------ downloads

## Queues a game's download (its first install or its update).
func download(id: String) -> void:
	if id in _queue or manifest.get("games", {}).get(id, {}).is_empty():
		return
	if not LibraryCatalog.can_install(manifest["games"][id], _ctx()):
		return
	_errors.erase(id)
	_queue.append(id)
	_progress[id] = [0, int(manifest["games"][id]["size"])]
	changed.emit()
	if _queue.size() == 1:
		_start_next()


func download_all(ids: Array) -> void:
	for id in ids:
		download(id)


func cancel(id: String) -> void:
	if id not in _queue:
		return
	if _queue[0] == id and _http:
		_http.cancel_request()
		DirAccess.remove_absolute(DIR + _part(id))
		_queue.pop_front()
		_progress.erase(id)
		changed.emit()
		_start_next()
	else:
		_queue.erase(id)
		_progress.erase(id)
		changed.emit()


func busy() -> bool:
	return not _queue.is_empty()


func _part(id: String) -> String:
	return String(manifest["games"][id]["file"]) + ".part"


func _start_next() -> void:
	if _queue.is_empty():
		return
	var id := _queue[0]
	if _preview:
		return  # the preview's progress is driven by _process
	var g: Dictionary = manifest["games"][id]
	_http.download_file = DIR + _part(id)
	_http.body_size_limit = int(g["size"]) + 1_000_000
	_stall = 0.0
	_last_bytes = 0
	var err := _http.request(LibraryCatalog.url_beside(_manifest_url(), g["file"]))
	if err != OK:
		_fail(id, "could not start the download")


func _process(delta: float) -> void:
	if _queue.is_empty():
		return
	var id := _queue[0]
	if _preview:
		var p: Array = _progress[id]
		p[0] = mini(p[1], p[0] + int(delta * 6_000_000))
		if p[0] >= p[1]:
			_queue.pop_front()
			installed[id] = {"version": manifest["games"][id]["version"], "fresh": true}
			changed.emit()
			finished.emit(id)
			_start_next()
		return
	var bytes := _http.get_downloaded_bytes()
	_progress[id] = [bytes, maxi(_http.get_body_size(), int(manifest["games"][id]["size"]))]
	if bytes != _last_bytes:
		_last_bytes = bytes
		_stall = 0.0
	else:
		_stall += delta
		if _stall > STALL_SECONDS:
			_http.cancel_request()
			_fail(id, "the download stalled")


func _on_pack_done(result: int, code: int, _headers: PackedStringArray, _body: PackedByteArray) -> void:
	if _queue.is_empty():
		return
	var id := _queue[0]
	var g: Dictionary = manifest["games"][id]
	var part := DIR + _part(id)
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		_fail(id, "no connection" if result in [HTTPRequest.RESULT_CANT_CONNECT, HTTPRequest.RESULT_CANT_RESOLVE] \
			else "the download failed (%s)" % (str(code) if result == HTTPRequest.RESULT_SUCCESS else "error %d" % result))
		return
	if not _file_ok(part, g):
		_fail(id, "the download was damaged")
		return
	var dest := DIR + String(g["file"])
	DirAccess.remove_absolute(dest)
	if DirAccess.rename_absolute(part, dest) != OK:
		_fail(id, "could not save the game")
		return
	var was_update: bool = installed.has(id) or _bundled.has(id)
	# an older file of the game stays until the next start (_tidy): it is still mounted now
	installed[id] = {"version": g["version"], "file": g["file"], "sha256": g["sha256"], "size": g["size"],
		"date": Time.get_datetime_string_from_system(true), "fresh": was_update}
	_save_installed()
	if _played.has(id):
		_restart_needed = true  # its old scripts are still loaded: the new version runs after a restart
	elif not ProjectSettings.load_resource_pack(dest, true):
		_fail(id, "could not open the downloaded game")
		return
	_queue.pop_front()
	_progress.erase(id)
	changed.emit()
	finished.emit(id)
	_start_next()


func _fail(id: String, message: String) -> void:
	DirAccess.remove_absolute(DIR + _part(id))
	_errors[id] = message
	_queue.erase(id)
	_progress.erase(id)
	changed.emit()
	failed.emit(id, message)
	_start_next()


## Size and SHA-256 as the manifest says.
static func _file_ok(path: String, entry: Dictionary) -> bool:
	if not FileAccess.file_exists(path):
		return false
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null or f.get_length() != int(entry["size"]):
		return false
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	while f.get_position() < f.get_length():
		h.update(f.get_buffer(1 << 20))
	return h.finish().hex_encode() == String(entry["sha256"]).to_lower()


# ------------------------------------------------------------------ the launcher's own update

## Downloads the new launcher, puts it in place of this one and restarts (desktop); reloads the page (web).
func update_launcher() -> void:
	if web:
		JavaScriptBridge.eval("location.reload()")
		return
	if launcher_ready:
		restart()
		return
	var f := launcher_file()
	if f.is_empty() or not SelfUpdate.supported():
		OS.shell_open(REPO + ("tag/latest" if Settings.channel == "latest" else "latest"))
		return
	var up := SelfUpdate.new()
	add_child(up)
	up.done.connect(func(ok: bool, message: String):
		up.queue_free()
		if ok:
			launcher_ready = true
			changed.emit()
			restart()
		else:
			failed.emit("launcher", message)
			changed.emit())
	_progress["launcher"] = [0, int(f.get("size", 0))]
	up.progress.connect(func(b: int, t: int): _progress["launcher"] = [b, t])
	up.start(LibraryCatalog.url_beside(_manifest_url(), f["file"]), f)
	changed.emit()


func launcher_progress() -> Array:
	return _progress.get("launcher", [])


## Starts a fresh copy of the launcher (the updated one, if there is one) and quits this one.
func restart() -> void:
	Settings.save_settings()
	if web:
		JavaScriptBridge.eval("location.reload()")
		return
	SelfUpdate.relaunch()


# ------------------------------------------------------------------ files

func _mount(id: String) -> void:
	var e: Dictionary = installed[id]
	var path := DIR + String(e.get("file", ""))
	if _preview:
		return
	if not FileAccess.file_exists(path) or FileAccess.open(path, FileAccess.READ).get_length() != int(e.get("size", -1)) \
			or not ProjectSettings.load_resource_pack(path, true):
		push_warning("library: %s is missing or damaged, it will download again" % id)
		installed.erase(id)
		_save_installed()


## Removes old versions and unfinished downloads (not mounted yet at this point of the start).
func _tidy() -> void:
	var keep := {}
	for id in installed:
		keep[String(installed[id].get("file", ""))] = true
	for f in DirAccess.get_files_at(DIR):
		if (f.ends_with(".pck") or f.ends_with(".part")) and not keep.has(f):
			DirAccess.remove_absolute(DIR + f)


func _load_installed() -> void:
	var j = JSON.parse_string(FileAccess.get_file_as_string(INSTALLED)) if FileAccess.file_exists(INSTALLED) else null
	installed = j if j is Dictionary else {}


func _save_installed() -> void:
	if _preview:
		return
	var f := FileAccess.open(INSTALLED, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(installed, "\t"))
		f.close()


## Removes a downloaded game (it stays listed and can be downloaded again).
func remove(id: String) -> void:
	if not installed.has(id) or _preview:
		return
	installed.erase(id)
	_save_installed()
	_restart_needed = true  # still mounted until the launcher restarts; the file goes at the next start
	changed.emit()


# ------------------------------------------------------------------ preview

## A pretend channel for looking at the launcher's states: most games installed, some to download, a few
## updates and a newer launcher. Nothing is written to disk.
func _fake_channel() -> void:
	dev = false
	build = {"build": "preview", "core": 10, "games": {}}
	var games := {}
	var i := 0
	for g in GameRegistry.GAMES:
		if g["scene"] == "":
			continue
		var id: String = g["id"]
		var v := "v%d" % i
		games[id] = {"version": v, "file": id + ".pck", "sha256": "0".repeat(64), "size": 2_500_000 + (i * 1_700_000) % 24_000_000,
			"min_core": 12 if i % 11 == 7 else 9, "web": i % 3 == 0, "changes": ["%s: a new stage and a faster start" % g["title"],
			"%s: the music loops without a gap" % g["title"]]}
		if i % 4 != 1 and i % 11 != 7:
			installed[id] = {"version": v if i % 5 != 2 else "old", "fresh": i % 9 == 3}
		i += 1
	manifest = {"format": 1, "launcher": {"core": 11, "files": {SelfUpdate.platform(): {"file": "x", "size": 60_000_000}}},
		"games": games}
	get_tree().create_timer(2.0).timeout.connect(func(): news.emit(updates(), launcher_newer()))
