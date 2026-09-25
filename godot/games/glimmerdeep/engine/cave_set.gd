class_name CaveSet
extends RefCounted
## A BDCFF file: game-level properties and its caves.

const DESCRIPTORS := [
	["Name", "STRING", "name"],
	["Description", "STRING", "description"],
	["Author", "STRING", "author"],
	["Date", "STRING", "date"],
	["WWW", "STRING", "www"],
	["Difficulty", "STRING", "difficulty"],
	["Charset", "STRING", "charset"],
	["Fontset", "STRING", "fontset"],
	["Lives", "INT", "initial_lives"],
	["Lives", "INT", "maximum_lives"],
	["BonusLife", "INT", "bonus_life_score"],
	["Story", "LONGSTRING", "story"],
	["Remark", "LONGSTRING", "remark"],
	["TitleScreen", "LONGSTRING", "title_screen"],
	["TitleScreenScroll", "LONGSTRING", "title_screen_scroll"],
]

var name: String = ""
var description: String = ""
var author: String = ""
var date: String = ""
var www: String = ""
var difficulty: String = ""
var charset: String = ""
var fontset: String = ""
var initial_lives: int = 3
var maximum_lives: int = 9
var bonus_life_score: int = 500
var story: String = ""
var remark: String = ""
var title_screen: String = ""
var title_screen_scroll: String = ""
var caves: Array[CaveStored] = []
var highscore: Array = []
var warnings := PackedStringArray()
