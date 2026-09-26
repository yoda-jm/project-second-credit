class_name MossHud
extends Control
## Mossfolk HUD: out, home and needed, the clock; the skill bar (release rate, eight skills with what is left, pause,
## pop-all) with a map of the whole level; a bracket round the mossling under the cursor; the level card at the start
## and the result at the end. Clicks on the bar pick; clicks in the cave give the picked skill.

const ACCENT := Color(0.55, 0.85, 0.4)
const LABELS := {"climb": "CLIMB", "glide": "GLIDE", "pop": "POP", "block": "BLOCK", "build": "BUILD", "bash": "BASH",
	"mine": "MINE", "dig": "DIG"}
const BAR := 0.18   ## the bar's share of the screen height

@export var game: MossGame

var _t := 0.0
var _map: ImageTexture
var _map_img: Image
var _map_dirty := true
var _buttons: Array = []   ## [rect, action]
var _passed := false
var _map_t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e):
		_map_dirty = true
		e.event.connect(func(k, _d): if k in ["stroke", "brick", "pop"]: _map_dirty = true))
	game.level_done.connect(func(_e, passed): _passed = passed)


func _view() -> MossView3D:
	return get_node_or_null("../../View") as MossView3D


func _process(delta: float) -> void:
	_t += delta
	var e := game.engine
	var v := _view()
	if e and v and not game.demo:
		var mp := get_viewport().get_mouse_position()
		game.hover = -1
		if mp.y < size.y * (1.0 - BAR):
			game.hover = e.pick(v.pixel_at(mp), 9.0)
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if game.demo or game.engine == null:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		for b in _buttons:
			if (b[0] as Rect2).has_point(event.position):
				_press(b[1])
				get_viewport().set_input_as_handled()
				return
		if event.position.y >= size.y * (1.0 - BAR):
			# the map: jump there
			var mr := _map_rect()
			if mr.has_point(event.position):
				_view().cam_x = (event.position.x - mr.position.x) / mr.size.x * game.engine.level.w
			return
		if game.give(game.hover):
			get_viewport().set_input_as_handled()


func _press(action: String) -> void:
	var e := game.engine
	match action:
		"rate-": e.rate = maxi(e.level.rate, e.rate - 5)
		"rate+": e.rate = mini(99, e.rate + 5)
		"pause": e.paused = not e.paused
		"nuke": e.nuke()
		_: game.pick_skill(action)


func _map_rect() -> Rect2:
	var bar_h := size.y * BAR
	var mw := minf(size.x * 0.26, 360.0)
	var e := game.engine
	var mh := minf(bar_h - 24.0, mw * e.level.h / e.level.w)
	mw = mh * e.level.w / e.level.h
	return Rect2(size.x - mw - 20.0, size.y - bar_h + (bar_h - mh) * 0.5, mw, mh)


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	var lv := e.level
	# top: out, home, needed, time
	HudKit.panel(self, Rect2(24, 16, 520, 64), ACCENT)
	var home := int(round(100.0 * e.saved / lv.count))
	var need := int(round(100.0 * lv.save / lv.count))
	var mins := maxi(0, int(e.time_left)) / 60
	var secs := maxi(0, int(e.time_left)) % 60
	var stats := [["OUT", str(e.alive())], ["HOME", "%d%%" % home], ["NEED", "%d%%" % need], ["TIME", "%d:%02d" % [mins, secs]]]
	for i in stats.size():
		var col := HudKit.GOOD if stats[i][0] == "HOME" and home >= need else (HudKit.BAD if stats[i][0] == "TIME" and e.time_left < 30 else HudKit.INK)
		HudKit.text(self, Vector2(48 + i * 128, 40), stats[i][0], 14, Color(HudKit.INK, 0.6), HudKit.label_font())
		HudKit.text(self, Vector2(48 + i * 128, 68), stats[i][1], 28, col, HudKit.font(true))
	HudKit.panel(self, Rect2(vp.x - 344, 16, 320, 64), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "LEVEL %d" % (game.index + 1), lv.name.to_upper(), HudKit.INK, HudKit.RIGHT, 22)
	# the cursor bracket
	var v := _view()
	if game.hover >= 0 and v:
		var c: Dictionary = e.folk[game.hover]
		var sp := v.screen_of(c)
		var r := 26.0
		var col := Color(1, 1, 1, 0.9)
		for s in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
			var corner: Vector2 = sp + s * r
			draw_line(corner, corner - Vector2(s.x * 9, 0), col, 3.0)
			draw_line(corner, corner - Vector2(0, s.y * 9), col, 3.0)
		HudKit.text(self, sp + Vector2(0, -r - 10), _state_name(c), 16, col, HudKit.label_font(), HudKit.CENTER)
	_draw_bar(e)
	# cards
	if e.frame < 40 and not e.over:
		HudKit.banner(self, vp, vp.y * 0.4, lv.name.to_upper(), "SAVE %d OF %d" % [lv.save, lv.count], ACCENT, clampf((40 - e.frame) / 10.0, 0.0, 1.0))
	if e.paused:
		HudKit.banner(self, vp, vp.y * 0.4, "PAUSED", "", HudKit.INK, 1.0)
	if game.result:
		var pct := int(round(100.0 * e.saved / lv.count))
		HudKit.banner(self, vp, vp.y * 0.4, "WELL DONE" if _passed else "NOT ENOUGH", "%d%% HOME, %d%% NEEDED" % [pct, need],
			HudKit.GOOD if _passed else HudKit.BAD, 1.0)
		if not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.4 + 120), [["ENTER", "next level" if _passed else "try again"], ["ESC", "menu"]])
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y * (1.0 - BAR) - 60, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y * (1.0 - BAR) - 30), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)


func _state_name(c: Dictionary) -> String:
	var s: String = c["state"]
	var extra := ""
	if c["climber"]: extra += " C"
	if c["glider"]: extra += " G"
	return {"walk": "WALKER", "fall": "FALLER", "glide": "GLIDER", "climb": "CLIMBER", "block": "BLOCKER", "build": "BUILDER",
		"bash": "BASHER", "mine": "MINER", "dig": "DIGGER", "shrug": "SHRUGGING", "panic": "UH-OH"}.get(s, s.to_upper()) + extra


func _draw_bar(e: MossEngine) -> void:
	var vp := size
	var bar_h := vp.y * BAR
	var top := vp.y - bar_h
	draw_rect(Rect2(0, top, vp.x, bar_h), Color(0.03, 0.035, 0.03, 0.88))
	draw_line(Vector2(0, top), Vector2(vp.x, top), Color(ACCENT, 0.6), 2.0)
	_buttons.clear()
	var slots: Array = [["rate-", "RATE", str(e.level.rate)], ["rate+", "RATE", str(e.rate)]]
	for s in MossEngine.SKILLS:
		slots.append([s, LABELS[s], str(e.skills[s])])
	slots.append(["pause", "PAUSE", "II"])
	slots.append(["nuke", "POP ALL", "!"])
	var mr := _map_rect()
	var bw := minf((mr.position.x - 40.0) / slots.size() - 6.0, 110.0)
	var bh := bar_h - 24.0
	for i in slots.size():
		var r := Rect2(20.0 + i * (bw + 6.0), top + 12.0, bw, bh)
		var act: String = slots[i][0]
		var on := act == game.skill
		var empty: bool = act in MossEngine.SKILLS and e.skills[act] <= 0
		draw_rect(r, Color(1, 1, 1, 0.16) if on else Color(1, 1, 1, 0.05))
		if on:
			draw_rect(r, ACCENT, false, 3.0)
		var a := 0.35 if empty else 1.0
		HudKit.text(self, Vector2(r.get_center().x, r.position.y + bh * 0.42), slots[i][2], int(bh * 0.3), Color(HudKit.GOLD if on else HudKit.INK, a), HudKit.font(true), HudKit.CENTER)
		HudKit.text(self, Vector2(r.get_center().x, r.end.y - bh * 0.14), ("%d  " % (i - 1) if act in MossEngine.SKILLS else "") + slots[i][1], int(clampf(bh * 0.14, 11, 16)),
			Color(HudKit.INK, 0.7 * a), HudKit.label_font(), HudKit.CENTER)
		_buttons.append([r, act])
	# the map
	if (_map_dirty and _t - _map_t > 0.5) or _map == null:
		_map_dirty = false
		_map_t = _t
		_map_img = Image.create(e.w, e.h, false, Image.FORMAT_RGBA8)
		for y in e.h:
			for x in e.w:
				var t := e.terrain[y * e.w + x]
				_map_img.set_pixel(x, y, Color(0, 0, 0, 0) if t == 0 else (Color(0.5, 0.55, 0.6) if t == 2 else Color(0.45, 0.62, 0.3)))
		if _map == null or _map.get_size() != Vector2(e.w, e.h):
			_map = ImageTexture.create_from_image(_map_img)
		else:
			_map.update(_map_img)
	draw_rect(mr, Color(0, 0, 0, 0.5))
	draw_texture_rect(_map, mr, false)
	var k := mr.size.x / e.w
	for c in e.folk:
		if c["state"] != "gone":
			draw_rect(Rect2(mr.position + Vector2(c["x"], c["y"] - 3) * k - Vector2(1, 1), Vector2(2.5, 2.5)), Color(1.0, 0.9, 0.5))
	draw_rect(Rect2(mr.position + Vector2(e.level.exit) * k - Vector2(3, 6), Vector2(6, 6)), Color(1.0, 0.6, 0.2))
	var v := _view()
	if v:
		var vis := v.get_viewport().get_visible_rect().size
		var l := v.pixel_at(Vector2(0, vis.y * 0.3)).x
		var r2 := v.pixel_at(Vector2(vis.x, vis.y * 0.3)).x
		draw_rect(Rect2(mr.position.x + l * k, mr.position.y, (r2 - l) * k, mr.size.y), Color(1, 1, 1, 0.8), false, 2.0)
