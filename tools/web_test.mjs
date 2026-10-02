// Smoke test of the web build in headless Chrome (WebGL 2 through SwiftShader), driven over the DevTools protocol
// with Node's built-in WebSocket, no packages. For each page (the launcher, then each game with ?game=<id>&demo) it
// loads the page, waits for the engine to be ready, clicks to play, waits, and saves screenshots; it collects console
// errors and uncaught exceptions and exits 1 if there were any.
// Usage: node tools/web_test.mjs <play-url> <out-dir> [game ...]   (run by tools/test-web.sh)
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , playUrl, outDir, ...games] = process.argv;
const PORT = 9333;
const READY_TIMEOUT = 900;   // seconds: SwiftShader compiles the engine slowly
const sleep = (s) => new Promise((r) => setTimeout(r, s * 1000));
mkdirSync(outDir, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "sc-web-"));
const chrome = spawn("google-chrome-stable", [
	"--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "--no-first-run",
	"--no-default-browser-check", "--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist",
	"--window-size=1280,720", "--autoplay-policy=no-user-gesture-required", "about:blank",
], { stdio: "ignore" });

let version = null;
for (let i = 0; i < 60 && !version; i++) {
	try { version = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); } catch { await sleep(0.5); }
}
if (!version) { console.error("Chrome did not start"); process.exit(2); }
const ws = new WebSocket(version.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let nextId = 1;
const pending = new Map();
const problems = [];
const log = [];
ws.addEventListener("message", (ev) => {
	const m = JSON.parse(ev.data);
	if (m.id && pending.has(m.id)) {
		const { resolve, reject } = pending.get(m.id);
		pending.delete(m.id);
		m.error ? reject(new Error(m.error.message)) : resolve(m.result);
		return;
	}
	if (m.method === "Runtime.consoleAPICalled") {
		const text = m.params.args.map((a) => a.value ?? a.description ?? "").join(" ");
		log.push(`[${m.params.type}] ${text}`);
		if (m.params.type === "error" || /SCRIPT ERROR|^ERROR:/.test(text)) problems.push(text);
	} else if (m.method === "Runtime.exceptionThrown") {
		const d = m.params.exceptionDetails;
		const text = (d.exception && d.exception.description) || d.text;
		log.push(`[exception] ${text}`);
		problems.push(text);
	}
});
const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
	const id = nextId++;
	pending.set(id, { resolve, reject });
	ws.send(JSON.stringify({ id, method, params, sessionId }));
});

const { targetId } = await send("Target.createTarget", { url: "about:blank" });
const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
const s = (method, params) => send(method, params, sessionId);
await s("Runtime.enable");
await s("Page.enable");
const evaluate = async (expr) => (await s("Runtime.evaluate", { expression: expr, returnByValue: true })).result.value;
const shot = async (name) => {
	const { data } = await s("Page.captureScreenshot", { format: "png" });
	writeFileSync(join(outDir, name + ".png"), Buffer.from(data, "base64"));
	console.log("  screenshot", name);
};

const pages = [{ name: "launcher", query: "", wait: [8, 8] }].concat(
	games.map((g) => ({ name: g, query: `?game=${g}&demo`, wait: [120, 30] })));  // SwiftShader compiles the shaders slowly
let ok = true;
for (const p of pages) {
	const before = problems.length;
	console.log(`page ${p.name}`);
	await s("Page.navigate", { url: playUrl + p.query });
	const t0 = Date.now();
	let ready = false;
	while ((Date.now() - t0) / 1000 < READY_TIMEOUT) {
		const st = await evaluate(`(() => { const b = document.getElementById("play"); const n = document.getElementById("notice");
			if (n && n.style.display === "block") return "failed: " + n.textContent;
			return b && getComputedStyle(b).display !== "none" ? "ready" : (document.getElementById("progress") || {}).textContent; })()`);
		if (st === "ready") { ready = true; break; }
		if (st && st.startsWith("failed")) { problems.push(st); break; }
		await sleep(2);
	}
	console.log(`  ready after ${((Date.now() - t0) / 1000).toFixed(0)} s`);
	if (!ready) { ok = false; await shot(p.name + "-stuck"); continue; }
	await evaluate(`document.getElementById("play").click()`);
	await sleep(p.wait[0]);
	await shot(p.name + "-1");
	await sleep(p.wait[1]);
	await shot(p.name + "-2");
	if (problems.length > before) {
		ok = false;
		console.log(`  ${problems.length - before} problem(s)`);
	}
}
writeFileSync(join(outDir, "console.log"), log.join("\n") + "\n");
console.log(problems.length ? "PROBLEMS:\n" + [...new Set(problems)].slice(0, 30).join("\n") : "no console errors");
ws.close();
chrome.kill();
await sleep(1);
rmSync(profile, { recursive: true, force: true });
process.exit(ok && problems.length === 0 ? 0 : 1);
