# Third-party add-ons (vendored)

| Folder | Project | Version | Source | Licence | Integrity |
|---|---|---|---|---|---|
| `godot_ai/` | Godot AI (Godot MCP editor plugin) | 4.2.3 | https://github.com/hi-godot/godot-ai/releases/tag/v4.2.3 (`godot-ai-v4-plugin.zip`) | MIT (`godot_ai/LICENSE`) | zip SHA-256 `bff05c14…cdb417`, matches the release manifest |
| `gdUnit4/` | GdUnit4 (unit tests) | 6.2.1 | https://github.com/godot-gdunit-labs/gdUnit4/releases/tag/v6.2.1 (source tag, `addons/gdUnit4`) | MIT (`gdUnit4/LICENSE`) | copied unmodified |

Update godot-ai with its dock's **Update** button, not by extracting a new zip over the folder. Update GdUnit4 by
replacing the folder with the new tag's `addons/gdUnit4`. Record the new version here either way.
