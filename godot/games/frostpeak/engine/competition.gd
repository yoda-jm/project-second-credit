class_name Competition
extends RefCounted
## A Frostpeak Games competition: athletes (players in hot seat, or CPU rivals), a programme of events, results and
## medals. Each event is played by every athlete in turn; CPU athletes get results drawn from their skill.

const EVENTS := ["speed_skating", "ski_jump"]
const EVENT_TITLES := {"speed_skating": "SPEED SKATING 500 M", "ski_jump": "SKI JUMP K90"}
const LOWER_IS_BETTER := {"speed_skating": true, "ski_jump": false}
## Our own nations: names and flag colours (three stripes).
const NATIONS := [
	{"name": "Norvalia", "code": "NVL", "flag": [Color(0.8, 0.1, 0.15), Color(1, 1, 1), Color(0.1, 0.2, 0.6)]},
	{"name": "Glaciera", "code": "GLC", "flag": [Color(0.6, 0.85, 1.0), Color(1, 1, 1), Color(0.6, 0.85, 1.0)]},
	{"name": "Pinemark", "code": "PNM", "flag": [Color(0.1, 0.45, 0.2), Color(0.95, 0.85, 0.3), Color(0.1, 0.45, 0.2)]},
	{"name": "Aurelia", "code": "AUR", "flag": [Color(0.95, 0.75, 0.2), Color(0.1, 0.1, 0.1), Color(0.8, 0.15, 0.1)]},
	{"name": "Borealis", "code": "BOR", "flag": [Color(0.2, 0.2, 0.55), Color(0.35, 0.85, 0.6), Color(0.2, 0.2, 0.55)]},
	{"name": "Kestria", "code": "KES", "flag": [Color(1, 1, 1), Color(0.85, 0.2, 0.3), Color(1, 1, 1)]},
]

var athletes: Array[Dictionary] = []  ## {name, nation (index), cpu: bool, skill: 0..1}
var programme: Array = []
var current := 0  ## index into programme
var results := {}  ## event -> {athlete index: value}
var rng := RandomNumberGenerator.new()


func _init(players: Array = [], cpu_rivals := 3, seed := 1, events: Array = EVENTS) -> void:
	rng.seed = seed
	programme = events.duplicate()
	var used := {}
	for p in players:
		athletes.append({"name": p["name"], "nation": p["nation"], "cpu": false, "skill": 0.0})
		used[p["nation"]] = true
	var names := ["Ivo Brandt", "Sanna Lind", "Tomas Arve", "Mira Kolt", "Oleg Vesk", "Anja Rimm"]
	var k := 0
	for i in cpu_rivals:
		while used.has(k % NATIONS.size()):
			k += 1
		athletes.append({"name": names[k % names.size()], "nation": k % NATIONS.size(), "cpu": true,
			"skill": rng.randf_range(0.55, 0.9)})
		used[k % NATIONS.size()] = true
		k += 1
	for ev in programme:
		results[ev] = {}


func event_name() -> String:
	return programme[current] if current < programme.size() else ""


func finished() -> bool:
	return current >= programme.size()


func record(athlete: int, value: float) -> void:
	results[event_name()][athlete] = value


## CPU athletes' results for the current event, from their skill (deterministic for a seed).
func play_cpus() -> void:
	var ev := event_name()
	for i in athletes.size():
		var a := athletes[i]
		if not a["cpu"]:
			continue
		var form: float = clampf(a["skill"] + rng.randf_range(-0.12, 0.12), 0.0, 1.0)
		match ev:
			"speed_skating": record(i, snappedf(lerpf(45.0, 38.4, form), 0.01))
			"ski_jump": record(i, snappedf(lerpf(78.0, 118.0, form) + rng.randf_range(-3.0, 3.0), 0.1))


## Athlete indices for an event, best first.
func ranking(ev: String) -> Array:
	var r: Dictionary = results[ev]
	var order: Array = r.keys()
	var lower: bool = LOWER_IS_BETTER[ev]
	order.sort_custom(func(a, b): return r[a] < r[b] if lower else r[a] > r[b])
	return order


## Medals so far: athlete index -> [gold, silver, bronze].
func medals() -> Dictionary:
	var out := {}
	for i in athletes.size():
		out[i] = [0, 0, 0]
	for ev in programme:
		var rk := ranking(ev)
		for place in mini(3, rk.size()):
			out[rk[place]][place] += 1
	return out


func next_event() -> void:
	current += 1
