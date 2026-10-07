class_name WebFetch
extends Node
## Downloads in the browser with its own fetch() (web build only). Godot's HTTPRequest reads a body by its
## Content-Length, but GitHub Pages gzips everything and the browser hands back the unzipped bytes, so the length never
## matches; fetch() unzips and caches natively. Godot polls the download each frame and takes the bytes at the end.

signal done(ok: bool, code: int, bytes: PackedByteArray, error: String)

const JS := """
window.scFetch = window.scFetch || {
	jobs: {},
	start(key, url, fresh) {
		const job = {done: false, ok: false, status: 0, loaded: 0, error: "", bytes: null};
		this.jobs[key] = job;
		fetch(url, {cache: fresh ? "no-cache" : "default"}).then(async (r) => {
			job.status = r.status;
			if (!r.ok) { job.done = true; return; }
			const reader = r.body.getReader();
			const parts = [];
			for (;;) {
				const {done, value} = await reader.read();
				if (done) break;
				if (this.jobs[key] !== job) return;  // cancelled
				parts.push(value);
				job.loaded += value.length;
			}
			const out = new Uint8Array(job.loaded);
			let o = 0;
			for (const p of parts) { out.set(p, o); o += p.length; }
			job.bytes = out.buffer;
			job.ok = true;
			job.done = true;
		}).catch((e) => { job.error = String(e); job.done = true; });
	},
	state(key) {
		const j = this.jobs[key];
		return j ? JSON.stringify({done: j.done, ok: j.ok, status: j.status, loaded: j.loaded, error: j.error}) : "";
	},
	take(key) { const j = this.jobs[key]; delete this.jobs[key]; return j && j.bytes ? j.bytes : new ArrayBuffer(0); },
	cancel(key) { delete this.jobs[key]; },
};
"""

static var _next := 0
var _key := ""
var loaded := 0  ## bytes received so far (after the browser unzips them)


func _ready() -> void:
	JavaScriptBridge.eval(JS, true)
	set_process(false)


## Starts a download; fresh asks the server again (the manifest), otherwise the browser's cache may answer (packs,
## whose names change with every version).
func start(url: String, fresh := false) -> void:
	cancel()
	_next += 1
	_key = "k%d" % _next
	loaded = 0
	JavaScriptBridge.eval("window.scFetch.start(%s, %s, %s)" % [JSON.stringify(_key), JSON.stringify(url), "true" if fresh else "false"], true)
	set_process(true)


func busy() -> bool:
	return _key != ""


func cancel() -> void:
	if _key != "":
		JavaScriptBridge.eval("window.scFetch.cancel(%s)" % JSON.stringify(_key), true)
	_key = ""
	set_process(false)


func _process(_delta: float) -> void:
	var st = JSON.parse_string(str(JavaScriptBridge.eval("window.scFetch.state(%s)" % JSON.stringify(_key), true)))
	if not (st is Dictionary):
		return
	loaded = int(st["loaded"])
	if not st["done"]:
		return
	var bytes := PackedByteArray()
	if st["ok"]:
		var b = JavaScriptBridge.eval("window.scFetch.take(%s)" % JSON.stringify(_key), true)
		if b is PackedByteArray:
			bytes = b
	else:
		JavaScriptBridge.eval("window.scFetch.cancel(%s)" % JSON.stringify(_key), true)
	_key = ""
	set_process(false)
	done.emit(bool(st["ok"]), int(st["status"]), bytes, String(st["error"]))
