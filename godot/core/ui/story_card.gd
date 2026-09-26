class_name StoryCard
extends CanvasLayer
## A campaign's story card between levels: the game dims behind a panel, the title drops in and the text types
## itself out. A key or click finishes the text, a second one closes the card (or it closes by itself after
## `auto` seconds, as in the demo). Shared by every game; the game waits for `closed` before it plays on.

signal closed

const GOLD := Color(1.0, 0.83, 0.35)

var title := ""
var text := ""
var accent := GOLD
var auto := 0.0  ## seconds before it closes by itself (0: wait for the player)
var _t := 0.0
var _shown := 0.0
var _root: Control
var _done := false


static func show_card(parent: Node, card: Dictionary, accent_: Color, auto_ := 0.0) -> StoryCard:
	var c := StoryCard.new()
	c.title = str(card.get("title", ""))
	c.text = str(card.get("text", ""))
	c.accent = accent_
	c.auto = auto_
	parent.add_child(c)
	return c


func _ready() -> void:
	layer = 40
	process_mode = Node.PROCESS_MODE_ALWAYS
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.draw.connect(_draw_card)
	add_child(_root)


func _process(delta: float) -> void:
	_t += delta
	_shown = minf(float(text.length()), _shown + delta * 55.0)  # letters per second
	if auto > 0.0 and _t > auto:
		_close()
	_root.queue_redraw()


func _input(event: InputEvent) -> void:
	if _done or _t < 0.4:
		return
	var press: bool = (event is InputEventKey and event.pressed and not event.echo) or (event is InputEventMouseButton and event.pressed) \
		or (event is InputEventJoypadButton and event.pressed)
	if not press or event.is_action("ui_cancel"):
		return
	get_viewport().set_input_as_handled()
	if _shown < text.length():
		_shown = text.length()
	else:
		_close()


func _close() -> void:
	if _done:
		return
	_done = true
	closed.emit()
	queue_free()


func _draw_card() -> void:
	var vp := _root.get_viewport_rect().size
	var a := clampf(_t * 3.0, 0.0, 1.0)
	_root.draw_rect(Rect2(Vector2.ZERO, vp), Color(0, 0, 0, 0.62 * a))
	var w := minf(1100.0, vp.x - 120.0)
	var lines := _wrap(text, 26, w - 100.0)  # wrapped whole, then revealed letter by letter
	var h := 170.0 + lines.size() * 38.0
	var r := Rect2((vp.x - w) * 0.5, (vp.y - h) * 0.5 + (1.0 - a) * 30.0, w, h)
	HudKit.panel(_root, r, accent, 18, a)
	HudKit.text(_root, Vector2(vp.x * 0.5, r.position.y + 76), title.to_upper(), 40, Color(accent, a), HudKit.font(true), HudKit.CENTER)
	_root.draw_line(Vector2(vp.x * 0.5 - 60, r.position.y + 96), Vector2(vp.x * 0.5 + 60, r.position.y + 96), Color(accent, 0.6 * a), 2.0)
	var left := int(_shown)
	for i in lines.size():
		if left <= 0:
			break
		HudKit.text(_root, Vector2(r.position.x + 50, r.position.y + 146 + i * 38), lines[i].left(left), 26, Color(HudKit.INK, a), HudKit.label_font())
		left -= lines[i].length() + 1
	if _shown >= text.length() and auto <= 0.0:
		var blink := 0.5 + 0.5 * sin(_t * 4.0)
		HudKit.text(_root, Vector2(vp.x * 0.5, r.end.y + 44), "PRESS ANY KEY", 18, Color(HudKit.MUTED, blink * a), HudKit.label_font(), HudKit.CENTER)


## Greedy word wrap with the HUD font's measure (paragraphs split on newlines).
func _wrap(s: String, size: int, width: float) -> PackedStringArray:
	var out := PackedStringArray()
	for para in s.split("\n"):
		var line := ""
		for word in para.split(" ", false):
			var t := word if line == "" else line + " " + word
			if HudKit.width(t, size, HudKit.label_font()) > width and line != "":
				out.append(line)
				line = word
			else:
				line = t
		out.append(line)
	return out
