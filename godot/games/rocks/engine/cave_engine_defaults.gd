class_name CaveEngineDefaults
extends RefCounted
## Presets for the BDCFF "Engine=" tag (BD1, BD2, PLCK, 1stB, CrDr, CrLi). Port of GDash's
## C64Import::cave_set_*_defaults (MIT, Copyright (c) 2007-2013 Czirkos Zoltan; see GDASH_LICENSE.txt).

const E = preload("res://games/rocks/engine/cave_elements.gd")
const NAMES: Array[String] = ["BD1", "BD2", "PLCK", "1stB", "CrDr", "CrLi"]

const _COMMON := {
	"amoeba_growth_prob": 31250, "amoeba_fast_growth_prob": 250000,
	"lineshift": true, "wraparound_objects": true,
	"voodoo_disappear_in_explosion": true, "voodoo_any_hurt_kills_player": false,
	"level_hatching_delay_time": [2, 2, 2, 2, 2],
	"pushing_stone_prob": 250000, "pushing_stone_prob_sweet": 1000000,
	"max_time": 999, "pal_timing": true,
}

const _BD1 := {
	"level_amoeba_threshold": [200, 200, 200, 200, 200],
	"amoeba_timer_started_immediately": true, "amoeba_timer_wait_for_hatching": false,
	"diagonal_movements": false, "voodoo_collects_diamonds": false, "voodoo_dies_by_stone": false,
	"creatures_backwards": false, "creatures_direction_auto_change_on_start": false,
	"creatures_direction_auto_change_time": 0,
	"intermission_instantlife": true, "intermission_rewardlife": false,
	"magic_wall_stops_amoeba": false, "magic_wall_breakscan": true, "magic_timer_wait_for_hatching": false,
	"active_is_first_found": false, "short_explosions": true, "slime_predictable": true,
	"snap_element": E.SPACE, "scheduling": CaveScheduling.BD1, "level_ckdelay": [12, 6, 3, 1, 0],
}

const _BD2 := {
	"level_amoeba_threshold": [200, 200, 200, 200, 200],
	"amoeba_timer_started_immediately": false, "amoeba_timer_wait_for_hatching": false,
	"diagonal_movements": false, "voodoo_collects_diamonds": false, "voodoo_dies_by_stone": false,
	"creatures_backwards": false, "creatures_direction_auto_change_on_start": false,
	"creatures_direction_auto_change_time": 0,
	"intermission_instantlife": true, "intermission_rewardlife": false,
	"magic_wall_stops_amoeba": false, "magic_timer_wait_for_hatching": false,
	"active_is_first_found": false, "short_explosions": true, "slime_predictable": true,
	"snap_element": E.SPACE, "scheduling": CaveScheduling.BD2, "level_ckdelay": [9, 8, 7, 6, 6],
}

const _PLCK := {
	"amoeba_timer_started_immediately": false, "amoeba_timer_wait_for_hatching": false,
	"border_scan_first_and_last": false, "diagonal_movements": false,
	"voodoo_collects_diamonds": false, "voodoo_dies_by_stone": false,
	"creatures_backwards": false, "creatures_direction_auto_change_on_start": false,
	"creatures_direction_auto_change_time": 0,
	"intermission_instantlife": true, "intermission_rewardlife": false,
	"magic_wall_stops_amoeba": false, "magic_timer_wait_for_hatching": false,
	"active_is_first_found": false, "short_explosions": true,
	"snap_element": E.SPACE, "scheduling": CaveScheduling.PLCK,
}

const _1STB := {
	"amoeba_timer_started_immediately": false, "amoeba_timer_wait_for_hatching": true,
	"voodoo_collects_diamonds": true, "voodoo_dies_by_stone": true,
	"creatures_direction_auto_change_on_start": true,
	"intermission_instantlife": false, "intermission_rewardlife": true,
	"magic_timer_wait_for_hatching": true, "active_is_first_found": true, "short_explosions": false,
	"slime_predictable": true, "snap_element": E.SPACE, "scheduling": CaveScheduling.PLCK,
	"amoeba_enclosed_effect": E.PRE_DIA_1, "dirt_looks_like": E.DIRT2,
}

const _CRDR := {
	"amoeba_timer_started_immediately": false, "amoeba_timer_wait_for_hatching": true,
	"voodoo_collects_diamonds": true, "voodoo_dies_by_stone": true,
	"creatures_direction_auto_change_on_start": false,
	"intermission_instantlife": false, "intermission_rewardlife": true,
	"magic_timer_wait_for_hatching": true, "active_is_first_found": true, "short_explosions": false,
	"slime_predictable": true, "snap_element": E.SPACE, "scheduling": CaveScheduling.CRDR,
	"amoeba_enclosed_effect": E.PRE_DIA_1, "water_does_not_flow_down": true,
	"skeletons_worth_diamonds": 1, "gravity_affects_all": false,
}

const _CRLI := {
	"amoeba_timer_started_immediately": false, "amoeba_timer_wait_for_hatching": true,
	"voodoo_collects_diamonds": true, "voodoo_dies_by_stone": true,
	"creatures_direction_auto_change_on_start": false,
	"intermission_instantlife": false, "intermission_rewardlife": true,
	"magic_timer_wait_for_hatching": true, "active_is_first_found": true, "short_explosions": false,
	"slime_predictable": true, "scheduling": CaveScheduling.PLCK,
	"amoeba_enclosed_effect": E.PRE_DIA_1,
}


## Applies the preset named in an Engine= tag. Returns false for an unknown engine name.
static func apply(cave: CaveProperties, engine_name: String) -> bool:
	var presets := [_BD1, _BD2, _PLCK, _1STB, _CRDR, _CRLI]
	for i in NAMES.size():
		if NAMES[i].to_lower() == engine_name.to_lower():
			for k in _COMMON:
				cave.set(k, _COMMON[k].duplicate() if _COMMON[k] is Array else _COMMON[k])
			var p: Dictionary = presets[i]
			for k in p:
				cave.set(k, p[k].duplicate() if p[k] is Array else p[k])
			return true
	return false
