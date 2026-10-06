extends Node
## The library's end-to-end check, run by tools/test-library.sh in an exported launcher (user argument
## "--library-selftest=<step>"):
##   download: checks the channel, downloads every game, then runs each one for a moment
##   reopen:   (a second start, no network) every game is mounted from the last run and runs
##   damaged:  the channel's files are damaged: nothing may be installed
##   selfupdate: the channel has a newer launcher: it replaces this one ($APPIMAGE) and starts it again
##   fetch:    (the web test) downloads every game the channel offers here, then waits for the browser to store them
##   mounted:  (the web test, next visit) every game came back from the browser's storage
##   ui=<id>:  drives the launcher like a player (select, Enter to download and play, back, library, remove, Enter
##             again) and saves a screenshot at each step in $SELFTEST_SHOTS
## Prints "SELFTEST ..." lines and quits with 0 when everything passed.

var step := ""
var _failures := 0
var _t := 0.0


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--library-selftest="):
			step = a.get_slice("=", 1)
	if step.begins_with("ui:"):
		_ui.call_deferred(step.get_slice(":", 1))
		step = "ui"
		return
	printerr("SELFTEST start %s: build %s, core %d, %d installed" % [step, Library.build.get("build", "?"), Library.core(), Library.installed.size()])
	if "--relaunched" in OS.get_cmdline_user_args():
		printerr("SELFTEST relaunched from %s" % OS.get_executable_path())
		_finish()
		return
	match step:
		"download", "damaged", "selfupdate", "fetch":
			Library.check()
		"mounted":
			_check_mounted.call_deferred()
		"reopen":
			_run_games.call_deferred()


func _process(delta: float) -> void:
	if step == "selfupdate":
		_self_update(delta)
		return
	if step not in ["download", "damaged", "fetch"]:
		return
	_t += delta
	if _t > 900.0:
		_fail("timed out (checking %s, %d queued)" % [Library.checking, Library._queue.size()])
		_finish()
		return
	if Library.checking or (Library.manifest.is_empty() and _t < 20.0):
		return
	if Library.manifest.is_empty():
		_fail("no manifest from the channel")
		_finish()
		return
	if not _started:
		_started = true
		var ids := Library.missing()
		printerr("SELFTEST channel: %d games to download, %s" % [ids.size(), LibraryCatalog.size_text(LibraryCatalog.total_size(ids, Library.manifest))])
		if ids.is_empty():
			_fail("nothing to download")
		Library.download_all(ids)
		return
	if Library.busy():
		return
	set_process(false)
	if step == "damaged":
		if not Library.installed.is_empty():
			_fail("%d damaged games were installed" % Library.installed.size())
		var errs := 0
		for g in GameRegistry.GAMES:
			if Library.error(g["id"]) != "":
				errs += 1
		printerr("SELFTEST damaged: %d downloads refused" % errs)
		if errs == 0:
			_fail("no download was refused")
		_finish()
		return
	for g in _games():
		if Library.state(g) != LibraryCatalog.READY:
			_fail("%s is %s after downloading (%s)" % [g["id"], Library.state(g), Library.error(g["id"])])
	if step == "fetch":
		await get_tree().create_timer(5.0).timeout  # the browser stores user:// between frames
		_finish()
		return
	_run_games()


var _started := false


func _self_update(delta: float) -> void:
	_t += delta
	if _started or Library.checking or (Library.manifest.is_empty() and _t < 20.0):
		if _t > 300.0:
			_fail("the launcher update didn't finish")
			_finish()
		return
	_started = true
	if not Library.launcher_newer():
		_fail("the channel's launcher is not newer (core %d)" % Library.core())
	elif not Library.can_self_update():
		_fail("this launcher can't replace itself (APPIMAGE=%s)" % OS.get_environment("APPIMAGE"))
	else:
		printerr("SELFTEST updating the launcher")
		Library.failed.connect(func(id, message): _fail("%s: %s" % [id, message]); _finish())
		Library.update_launcher()  # downloads, replaces, starts the new one and quits
		return
	_finish()


## Loads and runs every game's scene for a moment.
func _run_games() -> void:
	var games := _games()
	if games.is_empty():
		_fail("no game to run")
	for g in games:
		if not ResourceLoader.exists(g["scene"]):
			_fail("%s: its scene is not there" % g["id"])
			continue
		var ps := load(g["scene"]) as PackedScene
		if ps == null:
			_fail("%s: its scene doesn't load" % g["id"])
			continue
		var n := ps.instantiate()
		get_tree().root.add_child(n)
		for i in 20:
			await get_tree().process_frame
		n.queue_free()
		await get_tree().process_frame
		printerr("SELFTEST ran %s" % g["id"])
	_finish()


func _check_mounted() -> void:
	var n := 0
	for g in GameRegistry.GAMES:
		if Library.manifest.get("games", {}).get(g["id"], {}).get("web", false):
			n += 1
			if not Library.installed.has(g["id"]) or not ResourceLoader.exists(g["scene"]):
				_fail("%s didn't come back from the browser's storage" % g["id"])
	printerr("SELFTEST %d games came back" % n)
	if n == 0:
		_fail("no web game in the cached manifest")
	_finish()


# ------------------------------------------------------------------ ui

var _shot_n := 0


func _ui(id: String) -> void:
	Library.check()
	await _until(func(): return not Library.manifest.is_empty() and not Library.checking, 30.0)
	var gi := GameRegistry.GAMES.find(GameRegistry.find(id))
	var l = get_tree().current_scene
	await _shot("start")
	l._select_game(gi)
	await _frames(40)
	printerr("SELFTEST ui: %s is %s" % [id, Library.state_of(id)])
	await _shot("selected")
	l._launch()
	await _frames(20)
	await _shot("enter")
	await _until(func(): return Library.state_of(id) == LibraryCatalog.READY, 120.0)
	printerr("SELFTEST ui: downloaded, %s" % Library.state_of(id))
	await _until(func(): return get_tree().current_scene == null or get_tree().current_scene.scene_file_path != "res://core/ui/launcher.tscn", 20.0)
	await _seconds(12.0)
	await _shot("playing")
	get_tree().paused = false
	get_tree().change_scene_to_file("res://core/ui/launcher.tscn")
	await _frames(60)
	l = get_tree().current_scene
	await _shot("back")
	l._library.open_panel()
	await _frames(30)
	await _shot("library")
	l._library._row_of[id]["remove"].pressed.emit()
	await _frames(30)
	printerr("SELFTEST ui: after remove %s, installed %s, scene there %s" % [Library.state_of(id), Library.installed.has(id),
		ResourceLoader.exists(GameRegistry.GAMES[gi]["scene"])])
	await _shot("removed")
	l._library.close()
	await _frames(30)
	await _shot("card-after-remove")
	l._launch()
	await _seconds(3.0)
	printerr("SELFTEST ui: Enter after remove, %s" % Library.state_of(id))
	await _shot("enter-after-remove")
	await _seconds(20.0)
	await _shot("after")
	printerr("SELFTEST ui: done, %s" % Library.state_of(id))
	_finish()


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	_shot_n += 1
	var dir := OS.get_environment("SELFTEST_SHOTS")
	if dir != "":
		get_viewport().get_texture().get_image().save_png(dir.path_join("%02d-%s.png" % [_shot_n, name]))


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _seconds(t: float) -> void:
	await get_tree().create_timer(t, true).timeout


func _until(cond: Callable, timeout: float) -> void:
	var t0 := Time.get_ticks_msec()
	while not cond.call() and Time.get_ticks_msec() - t0 < timeout * 1000.0:
		await get_tree().process_frame


## The games this run is about: the channel's (download) or the ones installed (reopen).
func _games() -> Array:
	return GameRegistry.GAMES.filter(func(g): return g["scene"] != "" and \
		(Library.installed.has(g["id"]) if step == "reopen" else Library.state(g) != LibraryCatalog.UNAVAILABLE \
			and Library.manifest.get("games", {}).has(g["id"])))


func _fail(message: String) -> void:
	_failures += 1
	printerr("SELFTEST FAIL ", message)


func _finish() -> void:
	set_process(false)
	printerr("SELFTEST %s: %s" % [step, "PASSED" if _failures == 0 else "%d FAILED" % _failures])
	if not Library.web:
		get_tree().quit(0 if _failures == 0 else 1)
