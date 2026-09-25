extends GdUnitTestSuite
## Smoke test: the boot scene loads and has its title.


func test_boot_scene_has_title() -> void:
	var runner := scene_runner("res://boot/boot.tscn")
	var title: Label = runner.find_child("Title")
	assert_object(title).is_not_null()
	assert_str(title.text).is_equal("SECOND CREDIT")
