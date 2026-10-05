extends Node
## The library's end-to-end check, run by tools/test-library.sh in an exported launcher (user argument
## "--library-selftest=<step>"):
##   download: checks the channel, downloads every game, then runs each one for a moment
##   reopen:   (a second start, no network) every game is mounted from the last run and runs
##   damaged:  the channel's files are damaged: nothing may be installed
## Prints "SELFTEST ..." lines and quits with 0 when everything passed.

var step := ""
var _failures := 0
var _t := 0.0


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--library-selftest="):
			step = a.get_slice("=", 1)
	print("SELFTEST start %s: build %s, core %d, %d installed" % [step, Library.build.get("build", "?"), Library.core(), Library.installed.size()])
	match step:
		"download", "damaged":
			Library.check()
		"reopen":
			_run_games.call_deferred()


func _process(delta: float) -> void:
	if step not in ["download", "damaged"]:
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
		print("SELFTEST channel: %d games to download, %s" % [ids.size(), LibraryCatalog.size_text(LibraryCatalog.total_size(ids, Library.manifest))])
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
		print("SELFTEST damaged: %d downloads refused" % errs)
		if errs == 0:
			_fail("no download was refused")
		_finish()
		return
	for g in _games():
		if Library.state(g) != LibraryCatalog.READY:
			_fail("%s is %s after downloading (%s)" % [g["id"], Library.state(g), Library.error(g["id"])])
	_run_games()


var _started := false


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
		print("SELFTEST ran %s" % g["id"])
	_finish()


## The games this run is about: the channel's (download) or the ones installed (reopen).
func _games() -> Array:
	return GameRegistry.GAMES.filter(func(g): return g["scene"] != "" and \
		(Library.installed.has(g["id"]) if step == "reopen" else Library.manifest.get("games", {}).has(g["id"])))


func _fail(message: String) -> void:
	_failures += 1
	print("SELFTEST FAIL ", message)


func _finish() -> void:
	print("SELFTEST %s: %s" % [step, "PASSED" if _failures == 0 else "%d FAILED" % _failures])
	get_tree().quit(0 if _failures == 0 else 1)
