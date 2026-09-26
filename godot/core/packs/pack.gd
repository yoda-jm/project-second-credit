class_name Pack
extends RefCounted
## A level pack or campaign, shared by every game (see docs/level-packs.md). Packs are data only: a folder with a
## pack.json manifest and level files in the game's own format (or a foreign one its importer reads).
##
##   {
##     "format": 1, "game": "boots", "id": "first-tour", "name": "First Tour", "version": "1.0.0",
##     "author": "Second Credit", "licence": "CC-BY-SA-4.0", "description": "...",
##     "levels": ["first-tour.boots"],               level files, relative to the pack folder, read in order
##     "intro": {"title": "...", "text": "..."},      optional story card before the first level
##     "story": [{"level": 1, "title": "...", "text": "..."}],   cards shown before level N (0-based)
##     "outro": {"title": "...", "text": "..."}       after the last level is won
##   }
##
## Packs load from the game's own folder (res://games/<game>/packs/<id>/) and from the player's folder
## (user://packs/<id>/).

const USER_DIR := "user://packs"

var dir := ""
var id := ""
var game := ""
var name := ""
var version := "1.0.0"
var author := ""
var licence := ""
var description := ""
var levels: Array[String] = []  ## absolute paths
var intro := {}
var outro := {}
var story := {}  ## level index -> {title, text}


static func load_dir(path: String) -> Pack:
	var f := path.path_join("pack.json")
	if not FileAccess.file_exists(f):
		return null
	var data = JSON.parse_string(FileAccess.get_file_as_string(f))
	if typeof(data) != TYPE_DICTIONARY or int(data.get("format", 0)) != 1:
		return null
	var p := Pack.new()
	p.dir = path
	p.id = str(data.get("id", path.get_file()))
	p.game = str(data.get("game", ""))
	p.name = str(data.get("name", p.id))
	p.version = str(data.get("version", "1.0.0"))
	p.author = str(data.get("author", ""))
	p.licence = str(data.get("licence", ""))
	p.description = str(data.get("description", ""))
	for l in data.get("levels", []):
		var rel := str(l)
		if rel.contains(".."):  # packs stay inside their own folder
			continue
		p.levels.append(path.path_join(rel))
	if typeof(data.get("intro")) == TYPE_DICTIONARY:
		p.intro = data["intro"]
	if typeof(data.get("outro")) == TYPE_DICTIONARY:
		p.outro = data["outro"]
	for s in data.get("story", []):
		if typeof(s) == TYPE_DICTIONARY and s.has("level"):
			p.story[int(s["level"])] = s
	return p


## Every pack for a game: its own first (sorted by folder), then the player's.
static func scan(game_id: String) -> Array[Pack]:
	var out: Array[Pack] = []
	for root in ["res://games/%s/packs" % game_id, USER_DIR]:
		if not DirAccess.dir_exists_absolute(root):
			continue
		var names := DirAccess.get_directories_at(root)
		names.sort()
		for n in names:
			var p := load_dir(root.path_join(n))
			if p and p.game == game_id:
				out.append(p)
	return out


static func find(game_id: String, pack_id: String) -> Pack:
	for p in scan(game_id):
		if p.id == pack_id:
			return p
	return null


## The level files' text, one after the other (formats with several levels per file split it themselves).
func levels_text() -> String:
	var s := ""
	for l in levels:
		s += FileAccess.get_file_as_string(l) + "\n"
	return s


## The story card to show before level i (0-based): the intro before the first, else the level's own, or {}.
func card_before(i: int) -> Dictionary:
	if story.has(i):
		return story[i]
	if i == 0 and not intro.is_empty():
		return intro
	return {}
