# Game 1 audio: provenance

Everything here is original and licensed CC BY-SA 4.0, like the rest of the project's assets.

- `sfx/*.wav`: synthesised from scratch by `tools/audio/glimmerdeep_sfx.py` (NumPy oscillators, noise and filters;
  no samples). Regenerate with `python3 tools/audio/glimmerdeep_sfx.py`.
- `music/cave_theme.mid`: composed as code in `tools/audio/glimmerdeep_music.py`.
- `music/cave_theme.ogg`: that MIDI rendered with FluidSynth (LGPL-2.1) and the FluidR3_GM SoundFont
  (MIT, by Frank Wen), made loop-seamless and encoded with oggenc. Regenerate with
  `python3 tools/audio/glimmerdeep_music.py`.
