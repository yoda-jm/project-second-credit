class_name LinksBall
extends RefCounted
## The ball's state, small enough to copy for look-ahead simulations: position on the plan (m), the height of its
## bottom, horizontal and vertical velocity, and the mode it is in (rolling, flying, inside the loop or a pipe,
## dropped in the cup, lost in water).

enum Mode { ROLL, AIR, LOOP, PIPE, SUNK, LOST }

var pos := Vector2.ZERO
var z := 0.0
var vel := Vector2.ZERO
var vz := 0.0
var mode := Mode.ROLL
var t := 0.0            ## time in the loop or pipe (s), or since sinking
var data := {}          ## the loop or pipe being travelled
var lip_cool := false   ## after a lip-out, until the ball has left the cup
var at_rest := true
var hits := 0           ## bank and gadget contacts this shot


func copy() -> LinksBall:
	var b := LinksBall.new()
	b.pos = pos
	b.z = z
	b.vel = vel
	b.vz = vz
	b.mode = mode
	b.t = t
	b.data = data
	b.lip_cool = lip_cool
	b.at_rest = at_rest
	b.hits = hits
	return b


func place(p: Vector2, ground: float) -> void:
	pos = p
	z = ground
	vel = Vector2.ZERO
	vz = 0.0
	mode = Mode.ROLL
	t = 0.0
	data = {}
	lip_cool = false
	at_rest = true
	hits = 0


## The ball's centre in 3D (x east, y up, z south), for the view.
func world(radius: float) -> Vector3:
	return Vector3(pos.x, z + radius, pos.y)
