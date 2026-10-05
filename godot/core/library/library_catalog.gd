class_name LibraryCatalog
extends RefCounted
## What the launcher can do with each game, from what is on this machine and what the channel's manifest offers.
## Pure functions, so the rules are tested without a network (core/tests/test_library.gd). Spec: docs/updater.md

## The game is here and up to date (or the manifest is unknown): Enter plays it.
const READY := "ready"
## Here, and the channel has a newer version the player can download.
const UPDATE := "update"
## Not on this machine; the channel has it: Enter downloads it, then plays.
const MISSING := "missing"
## Being downloaded.
const DOWNLOADING := "downloading"
## Not here, and the channel's version needs a newer launcher than this one.
const NEEDS_LAUNCHER := "needs_launcher"
## Not here and no manifest yet (offline, or the check is off).
const OFFLINE := "offline"
## Not here and not offered on this platform (a game not checked in the browser yet).
const UNAVAILABLE := "unavailable"
## Still being made (no scene in the registry).
const IN_DEVELOPMENT := "in_development"


## ctx keys: manifest (Dictionary, may be empty), local (id -> version of the copy on this machine, "" if none),
## core (this launcher's core serial), web (bool), downloading (Array of ids).
static func state(g: Dictionary, ctx: Dictionary) -> String:
	var id: String = g["id"]
	if g.get("scene", "") == "":
		return IN_DEVELOPMENT
	if id in ctx.get("downloading", []):
		return DOWNLOADING
	var local: String = ctx.get("local", {}).get(id, "")
	var m: Dictionary = ctx.get("manifest", {}).get("games", {}).get(id, {})
	if local != "":
		if not m.is_empty() and m.get("version", "") != local and can_install(m, ctx):
			return UPDATE
		return READY
	if ctx.get("manifest", {}).is_empty():
		return OFFLINE
	if m.is_empty() or (ctx.get("web", false) and not m.get("web", false)):
		return UNAVAILABLE
	if not can_install(m, ctx):
		return NEEDS_LAUNCHER
	return MISSING


## Whether this launcher can run the manifest's version of a game (built against core serial min_core or later).
static func can_install(m: Dictionary, ctx: Dictionary) -> bool:
	return int(m.get("min_core", 0)) <= int(ctx.get("core", 0))


## Whether the channel has a newer launcher than this one.
static func launcher_newer(manifest: Dictionary, core: int) -> bool:
	return int(manifest.get("launcher", {}).get("core", 0)) > core


## The manifest's file entry for this platform's launcher ({} when there is none).
static func launcher_file(manifest: Dictionary, platform: String) -> Dictionary:
	return manifest.get("launcher", {}).get("files", {}).get(platform, {})


## The games with a newer version to download, in registry order.
static func updates(games: Array, ctx: Dictionary) -> Array[String]:
	var out: Array[String] = []
	for g in games:
		if state(g, ctx) == UPDATE:
			out.append(g["id"])
	return out


## The games the player can download now, in registry order.
static func missing(games: Array, ctx: Dictionary) -> Array[String]:
	var out: Array[String] = []
	for g in games:
		if state(g, ctx) == MISSING:
			out.append(g["id"])
	return out


## Total bytes to download for these games.
static func total_size(ids: Array, manifest: Dictionary) -> int:
	var n := 0
	for id in ids:
		n += int(manifest.get("games", {}).get(id, {}).get("size", 0))
	return n


## "14.2 MB", "820 KB".
static func size_text(bytes: int) -> String:
	if bytes >= 1_000_000:
		return "%.1f MB" % (bytes / 1_000_000.0)
	return "%d KB" % maxi(1, bytes / 1000)


## A manifest worth using: the right format and the fields the launcher reads.
static func valid_manifest(m: Variant) -> bool:
	if not (m is Dictionary):
		return false
	if int(m.get("format", 0)) != 1 or not (m.get("games") is Dictionary) or not (m.get("launcher") is Dictionary):
		return false
	for id in m["games"]:
		var g = m["games"][id]
		if not (g is Dictionary) or String(g.get("file", "")) == "" or String(g.get("sha256", "")).length() != 64 \
				or String(g.get("version", "")) == "" or int(g.get("size", 0)) <= 0:
			return false
		if String(g["file"]).contains("/") or String(g["file"]).contains(".."):
			return false  # a file name next to the manifest, never a path
	return true


## A file named in the manifest, as a URL beside the manifest's own.
static func url_beside(manifest_url: String, file: String) -> String:
	return manifest_url.substr(0, manifest_url.rfind("/") + 1) + file
