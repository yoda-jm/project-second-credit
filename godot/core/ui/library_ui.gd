class_name LibraryUI
extends Control
## The launcher's library screens (docs/updater.md): the LIBRARY panel (every game with its state, size and what's
## new, download / update / remove, UPDATE ALL, DOWNLOAD ALL, the launcher's own update), the small question
## asked when a game with a newer version is picked (update first, or play this one), the notice that slides in
## when the check at start finds something, and the status pill in the corner. Nothing downloads unless asked.

signal play_requested(id: String)  ## the player chose to play now (the version on this machine)
signal closed

const GOLD := Color(1.0, 0.83, 0.35)
const TEAL := Color(0.31, 0.84, 0.91)
const LEAF := Color(0.55, 1.0, 0.4)
const AMBER := Color(1.0, 0.64, 0.23)
const RED := Color(1.0, 0.42, 0.42)
const MUTED := Color(0.62, 0.65, 0.76)

var launcher: Node  ## the launcher: its fonts, panels and sounds
var panel: PanelContainer  ## LIBRARY
var prompt: PanelContainer  ## "a new version of X"
var _rows: VBoxContainer
var _head: Label
var _launcher_row: HBoxContainer
var _launcher_text: Label
var _launcher_button: Button
var _bulk: HBoxContainer
var _update_all: Button
var _download_all: Button
var _check_now: Button
var _back: Button
var _row_of := {}  ## id -> {status, button, remove, changes}
var _toast: PanelContainer
var _toast_text: Label
var _toast_tween: Tween
var _pill: Label
var _prompt_id := ""
var _prompt_title: Label
var _prompt_text: Label
var _prompt_update: Button
var _prompt_play: Button
var _prompt_restart := false
var _refresh_left := 0.0


func _init(l: Node) -> void:
	launcher = l
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	_build_pill()
	_build_toast()
	_build_panel()
	_build_prompt()
	Library.changed.connect(_on_changed)
	Library.news.connect(_on_news)
	Library.failed.connect(_on_failed)
	Library.finished.connect(_on_finished)
	_on_changed()


func is_open() -> bool:
	return panel.visible or prompt.visible


# ------------------------------------------------------------------ pill and notice

func _build_pill() -> void:
	_pill = launcher._label("", 20, MUTED)
	_pill.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_pill.position = Vector2(1180, 40)
	_pill.size = Vector2(680, 30)
	add_child(_pill)


func _pill_text() -> Array:
	if Library.dev:
		return ["", MUTED]
	var ups := Library.updates().size() + (1 if Library.launcher_newer() else 0)
	var channel := ("WEB" if Library.web else Settings.channel.to_upper())
	if Library.busy():
		return ["%s  ·  DOWNLOADING" % channel, TEAL]
	if Library.checking:
		return ["%s  ·  CHECKING FOR UPDATES" % channel, MUTED]
	if ups > 0:
		return ["%s  ·  %d UPDATE%s  ·  PRESS U" % [channel, ups, "" if ups == 1 else "S"], GOLD]
	if Library.manifest.is_empty():
		return ["%s  ·  OFFLINE" % channel if Settings.update_check or Library.web else "%s  ·  UPDATE CHECK OFF" % channel, MUTED]
	return ["%s  ·  UP TO DATE" % channel, MUTED]


func _build_toast() -> void:
	_toast = PanelContainer.new()
	var sb: StyleBoxFlat = launcher._panel_style(GOLD, 14)
	sb.bg_color = Color(0.07, 0.06, 0.12, 0.92)
	_toast.add_theme_stylebox_override("panel", sb)
	_toast.position = Vector2(1220, 84)
	_toast.custom_minimum_size = Vector2(640, 0)
	_toast.modulate.a = 0.0
	_toast.mouse_filter = Control.MOUSE_FILTER_STOP
	_toast.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed:
			open_panel())
	_toast_text = launcher._label("", 24, Color(0.92, 0.93, 0.98))
	_toast_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_toast.add_child(_toast_text)
	add_child(_toast)


## Slides a notice in at the top right for a few seconds.
func toast(text: String, color: Color = GOLD, seconds: float = 7.0) -> void:
	_toast_text.text = text
	(_toast.get_theme_stylebox("panel") as StyleBoxFlat).border_color = color
	if _toast_tween:
		_toast_tween.kill()
	_toast.position.x = 1300
	_toast_tween = create_tween()
	_toast_tween.tween_property(_toast, "modulate:a", 1.0, 0.25)
	_toast_tween.parallel().tween_property(_toast, "position:x", 1220.0, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_toast_tween.tween_interval(seconds)
	_toast_tween.tween_property(_toast, "modulate:a", 0.0, 0.5)


func _on_news(ups: Array, launcher_new: bool) -> void:
	var parts: Array[String] = []
	if launcher_new:
		parts.append("a new launcher")
	if not ups.is_empty():
		var names := ups.slice(0, 3).map(func(id): return GameRegistry.find(id)["title"])
		parts.append(("a new version of %s" % names[0]) if ups.size() == 1 else
			("new versions of %s%s" % [", ".join(names), " and %d more" % (ups.size() - 3) if ups.size() > 3 else ""]))
	toast("NEW:  %s.\nPress U to see what changed and update." % " and ".join(parts))
	launcher._play("ui_select")


func _on_failed(id: String, message: String) -> void:
	if id == "":
		return  # a failed check stays quiet: the pill says OFFLINE
	var title: String = "The new launcher" if id == "launcher" else GameRegistry.find(id).get("title", id)
	toast("%s didn't download: %s. Try again from the library (U)." % [title, message], RED)


func _on_finished(id: String) -> void:
	var g := GameRegistry.find(id)
	if Library.restart_needed() and Library._played.has(id):
		toast("%s is updated. Restart the launcher to play the new version." % g["title"], LEAF)
	elif id != launcher._play_when_ready:
		toast("%s is ready to play." % g["title"], LEAF, 4.0)


# ------------------------------------------------------------------ the LIBRARY panel

func _button(text: String, size: int = 24) -> Button:
	var b := Button.new()
	b.text = text
	b.add_theme_font_override("font", launcher._font())
	b.add_theme_font_size_override("font_size", size)
	b.add_theme_color_override("font_focus_color", GOLD)
	b.add_theme_color_override("font_hover_color", GOLD)
	b.pressed.connect(func(): launcher._play("ui_select"))
	return b


func _build_panel() -> void:
	panel = PanelContainer.new()
	var psb: StyleBoxFlat = launcher._panel_style(GOLD)
	psb.bg_color = Color(0.04, 0.04, 0.08, 0.95)
	panel.add_theme_stylebox_override("panel", psb)
	panel.position = Vector2(620, 110)
	panel.custom_minimum_size = Vector2(1180, 900)
	panel.visible = false
	add_child(panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	panel.add_child(v)
	v.add_child(launcher._label("LIBRARY", 48, GOLD, false))
	_head = launcher._label("", 22, MUTED)
	v.add_child(_head)

	_launcher_row = HBoxContainer.new()
	_launcher_row.add_theme_constant_override("separation", 20)
	_launcher_text = launcher._label("", 24, GOLD)
	_launcher_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_launcher_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_launcher_row.add_child(_launcher_text)
	_launcher_button = _button("UPDATE AND RESTART")
	_launcher_button.pressed.connect(Library.update_launcher)
	_launcher_row.add_child(_launcher_button)
	v.add_child(_launcher_row)

	_bulk = HBoxContainer.new()
	_bulk.add_theme_constant_override("separation", 16)
	_update_all = _button("UPDATE ALL")
	_update_all.pressed.connect(func(): Library.download_all(Library.updates()))
	_download_all = _button("DOWNLOAD ALL")
	_download_all.pressed.connect(func(): Library.download_all(Library.missing()))
	_check_now = _button("CHECK NOW")
	_check_now.pressed.connect(Library.check)
	for b in [_update_all, _download_all, _check_now]:
		_bulk.add_child(b)
	v.add_child(_bulk)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(1130, 560)
	scroll.follow_focus = true
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(scroll)
	_rows = VBoxContainer.new()
	_rows.add_theme_constant_override("separation", 6)
	_rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_rows)
	for g in GameRegistry.GAMES:
		_add_row(g)

	_back = _button("BACK", 30)
	_back.add_theme_font_override("font", launcher._font(false))
	_back.pressed.connect(close)
	v.add_child(_back)


func _add_row(g: Dictionary) -> void:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 0)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	var title: Label = launcher._label(String(g["title"]).to_upper(), 26, g["accent"], false)
	title.custom_minimum_size = Vector2(360, 0)
	row.add_child(title)
	var status: Label = launcher._label("", 22, MUTED)
	status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(status)
	var remove := _button("REMOVE", 20)
	remove.pressed.connect(func(): Library.remove(g["id"]))
	row.add_child(remove)
	var act := _button("", 22)
	act.custom_minimum_size = Vector2(220, 0)
	act.pressed.connect(_row_action.bind(g["id"]))
	row.add_child(act)
	box.add_child(row)
	var changes: Label = launcher._label("", 18, Color(0.75, 0.78, 0.86))
	changes.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	changes.custom_minimum_size = Vector2(1080, 0)
	box.add_child(changes)
	_rows.add_child(box)
	_row_of[g["id"]] = {"status": status, "button": act, "remove": remove, "changes": changes}


func _row_action(id: String) -> void:
	match Library.state_of(id):
		LibraryCatalog.MISSING, LibraryCatalog.UPDATE:
			Library.download(id)
		LibraryCatalog.DOWNLOADING:
			Library.cancel(id)
		LibraryCatalog.READY:
			close()
			play_requested.emit(id)
		LibraryCatalog.NEEDS_LAUNCHER:
			Library.update_launcher()


func open_panel() -> void:
	if panel.visible:
		return
	prompt.visible = false
	if _toast_tween:
		_toast_tween.kill()
	_toast.modulate.a = 0.0
	launcher._open_panel(panel)
	_refresh()
	# focus the first thing worth doing
	for b in [_launcher_button, _update_all, _download_all, _check_now]:
		if b.is_visible_in_tree() and not b.disabled:
			b.grab_focus()
			return
	_back.grab_focus()


func close() -> void:
	if prompt.visible:
		prompt.visible = false
		launcher._cards_focus_back()
		closed.emit()
		return
	if panel.visible:
		launcher._close_panels()
		closed.emit()


func _on_changed() -> void:
	var p := _pill_text()
	_pill.text = p[0]
	_pill.add_theme_color_override("font_color", p[1])
	if panel.visible:
		_refresh()


func _process(delta: float) -> void:
	_refresh_left -= delta
	if _refresh_left <= 0.0 and (Library.busy() or not Library.launcher_progress().is_empty()):
		_refresh_left = 0.2
		_on_changed()
		if panel.visible:
			_refresh()


## Status words per state (shared with the cards).
static func status_text(id: String) -> Array:
	var st := Library.state_of(id)
	var size := Library.size_text(id)
	var err := Library.error(id)
	match st:
		LibraryCatalog.READY:
			return ["UPDATED: NEW SINCE YOU LAST PLAYED" if Library.fresh(id) else "ON THIS COMPUTER" if not Library.dev else "READY", LEAF if Library.fresh(id) else MUTED]
		LibraryCatalog.UPDATE:
			return ["NEW VERSION  ·  %s" % size, GOLD]
		LibraryCatalog.MISSING:
			if err != "":
				return ["DIDN'T DOWNLOAD: %s" % err.to_upper(), RED]
			return ["NOT DOWNLOADED  ·  %s" % size, TEAL]
		LibraryCatalog.DOWNLOADING:
			var p := Library.progress(id)
			if Library._queue.find(id) > 0:
				return ["WAITING TO DOWNLOAD", TEAL]
			return ["DOWNLOADING  %s / %s" % [LibraryCatalog.size_text(p[0]), LibraryCatalog.size_text(p[1])], TEAL]
		LibraryCatalog.NEEDS_LAUNCHER:
			return ["NEEDS THE NEW LAUNCHER", AMBER]
		LibraryCatalog.OFFLINE:
			return ["CONNECT TO THE INTERNET TO DOWNLOAD IT", MUTED]
		LibraryCatalog.UNAVAILABLE:
			return ["DOESN'T WORK IN BROWSERS: ONLY ON DESKTOP" if Library.web else "NOT IN THIS CHANNEL", MUTED]
	return ["IN DEVELOPMENT", MUTED]


func _refresh() -> void:
	var ups := Library.updates()
	var miss := Library.missing()
	if Library.dev:
		_head.text = "development build: every game is in the project, nothing to download"
	else:
		var build := String(Library.build.get("build", "?"))
		_head.text = ("in your browser" if Library.web else "%s channel  ·  launcher %s" % [Settings.channel, build]) + \
			("  ·  checking..." if Library.checking else ("  ·  offline" if Library.manifest.is_empty() else ""))
	# the launcher itself
	var lp := Library.launcher_progress()
	_launcher_row.visible = Library.launcher_newer() or Library.launcher_ready
	if Library.web:
		_launcher_text.text = "A newer version of this page is out."
		_launcher_button.text = "RELOAD THE PAGE"
	elif Library.launcher_ready:
		_launcher_text.text = "The new launcher is in place."
		_launcher_button.text = "RESTART NOW"
	elif not lp.is_empty():
		_launcher_text.text = "Downloading the new launcher: %s / %s" % [LibraryCatalog.size_text(lp[0]), LibraryCatalog.size_text(maxi(1, lp[1]))]
		_launcher_button.text = "PLEASE WAIT"
	elif Library.can_self_update():
		_launcher_text.text = "A new launcher is out (%s). It replaces this one and restarts; your games and saves stay." % \
			LibraryCatalog.size_text(int(Library.launcher_file().get("size", 0)))
		_launcher_button.text = "UPDATE AND RESTART"
	else:
		_launcher_text.text = "A new launcher is out. This copy can't replace itself here: get it from the download page."
		_launcher_button.text = "OPEN THE DOWNLOAD PAGE"
	_launcher_button.disabled = not lp.is_empty() and not Library.launcher_ready
	_update_all.text = "UPDATE ALL  ·  %d  ·  %s" % [ups.size(), LibraryCatalog.size_text(LibraryCatalog.total_size(ups, Library.manifest))] if not ups.is_empty() else "EVERYTHING UP TO DATE"
	_update_all.disabled = ups.is_empty()
	_download_all.text = "DOWNLOAD ALL  ·  %d  ·  %s" % [miss.size(), LibraryCatalog.size_text(LibraryCatalog.total_size(miss, Library.manifest))] if not miss.is_empty() else "ALL GAMES DOWNLOADED"
	_download_all.disabled = miss.is_empty()
	_check_now.disabled = Library.checking or Library.dev
	_bulk.visible = not Library.dev
	for id in _row_of:
		var r: Dictionary = _row_of[id]
		var st := Library.state_of(id)
		var s := status_text(id)
		(r["status"] as Label).text = s[0]
		(r["status"] as Label).add_theme_color_override("font_color", s[1])
		var b: Button = r["button"]
		b.visible = true
		b.disabled = false
		match st:
			LibraryCatalog.READY:
				b.text = "PLAY"
			LibraryCatalog.UPDATE:
				b.text = "UPDATE"
			LibraryCatalog.MISSING:
				b.text = "RETRY" if Library.error(id) != "" else "DOWNLOAD"
			LibraryCatalog.DOWNLOADING:
				b.text = "CANCEL"
			LibraryCatalog.NEEDS_LAUNCHER:
				b.text = "GET LAUNCHER"
			_:
				b.visible = false
		(r["remove"] as Button).visible = Library.installed.has(id) and st in [LibraryCatalog.READY, LibraryCatalog.UPDATE] and not Library.web
		var ch: Array = Library.changes(id) if st == LibraryCatalog.UPDATE or (st == LibraryCatalog.READY and Library.fresh(id)) else []
		(r["changes"] as Label).text = "\n".join(ch.slice(0, 3).map(func(c): return "  •  " + _short(c)))
		(r["changes"] as Label).visible = not ch.is_empty()


## A commit subject without the game's name in front, cut to one line.
static func _short(subject: String) -> String:
	var s := subject
	var colon := s.find(": ")
	if colon > 0 and colon < 30:
		s = s.substr(colon + 2)
	if s.length() > 110:
		s = s.substr(0, 107).rstrip(" ,;") + "..."
	return s


# ------------------------------------------------------------------ the question when a game has a new version

func _build_prompt() -> void:
	prompt = PanelContainer.new()
	var qsb: StyleBoxFlat = launcher._panel_style(GOLD)
	qsb.bg_color = Color(0.04, 0.04, 0.08, 0.95)
	prompt.add_theme_stylebox_override("panel", qsb)
	prompt.position = Vector2(760, 330)
	prompt.custom_minimum_size = Vector2(900, 0)
	prompt.visible = false
	add_child(prompt)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 16)
	prompt.add_child(v)
	_prompt_title = launcher._label("", 40, GOLD, false)
	v.add_child(_prompt_title)
	_prompt_text = launcher._label("", 22, Color(0.85, 0.87, 0.94))
	_prompt_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_prompt_text.custom_minimum_size = Vector2(850, 0)
	v.add_child(_prompt_text)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 20)
	_prompt_update = _button("UPDATE", 26)
	_prompt_update.pressed.connect(_prompt_main)
	_prompt_play = _button("PLAY THIS VERSION", 26)
	_prompt_play.pressed.connect(func():
		prompt.visible = false
		play_requested.emit(_prompt_id))
	row.add_child(_prompt_update)
	row.add_child(_prompt_play)
	v.add_child(row)
	v.add_child(launcher._label("esc to go back", 18, MUTED))


## Asks before playing a game that has a newer version: update first, or play the one on this machine.
func ask_update(id: String) -> void:
	var g := GameRegistry.find(id)
	_prompt_id = id
	_prompt_restart = false
	_prompt_update.text = "UPDATE"
	_prompt_play.text = "PLAY THIS VERSION"
	_prompt_title.text = "NEW: %s" % String(g["title"]).to_upper()
	var ch: Array = Library.changes(id)
	_prompt_text.text = "A new version is out (%s to download).%s" % [Library.size_text(id),
		("\n" + "\n".join(ch.slice(0, 4).map(func(c): return "  •  " + _short(c)))) if not ch.is_empty() else ""]
	prompt.visible = true
	prompt.modulate.a = 0.0
	create_tween().tween_property(prompt, "modulate:a", 1.0, 0.15)
	_prompt_update.grab_focus()


## Says the launcher must restart to run a game's new version (its old scripts are still loaded).
func ask_restart(id: String) -> void:
	var g := GameRegistry.find(id)
	_prompt_id = id
	_prompt_title.text = "%s IS UPDATED" % String(g["title"]).to_upper()
	_prompt_text.text = "You played it earlier in this session: the new version starts after the launcher restarts."
	_prompt_restart = true
	_prompt_update.text = "RESTART NOW"
	_prompt_play.text = "PLAY THE OLD ONE"
	prompt.visible = true
	_prompt_update.grab_focus()


func _prompt_main() -> void:
	prompt.visible = false
	if _prompt_restart:
		Library.restart()
	else:
		launcher._download(_prompt_id)
