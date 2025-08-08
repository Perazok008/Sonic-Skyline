## Sonic Skyline

Sonic Skyline finds a single “horizon” line that separates sky from ground in images and videos and turns its shape into sound. The app provides fast, tunable detection, real‑time visualization, and export options (CSV, visualization overlays, MIDI, and Audio) suitable for DAWs.

### Key capabilities
- Horizon detection (image and video) with tunable parameters
- Real‑time playback with layer toggles and FPS controls
- Two algorithm variants:
  - v1: classic per‑column nearest‑edge (stable on many scenes)
  - v2 (default): fast vectorized top‑down edge search with continuity smoothing
- Exports:
  - CSV: raw horizon coordinates
  - Graph: matplotlib plot of the horizon
  - Overlay: original media with drawn horizon
  - MIDI: horizon as notes in a (simple) major scale
  - Audio (WAV): renders MIDI via FluidSynth (.sf2 required)

---

## Running the app

1) Install Python 3.10+ and dependencies

```bash
pip install -r requirements.txt
```

2) Launch

```bash
python app.py
```

---

## GUI overview

Left side (main content):
- Select File: choose an image or video
- Visualization Layers: toggles for Image/Video, Horizon Line, Axis
- Content area: displays the media with optional overlays
- Buttons: Process, Export (Ableton connect is a placeholder)
- Playback controls (for video): Pause/Resume, timeline slider, and info label showing current/total time and three FPS readouts:
  - Proc: detections/sec (horizon computations)
  - Play: actual display FPS
  - Native: media’s native FPS

Right side (settings panel):
- Edge Detection (Canny)
  - Lower/Upper thresholds
  - Aperture Size (3/5/7)
  - L2 gradient (precision vs. speed)
- Horizon Detection
  - Line Jump Threshold (max per‑column change to keep continuity)
- Playback
  - Processing FPS (detections per second)
  - Display Max FPS (cap for rendering)
- Algorithm (v1, v2)
- Reset/Apply (updates take effect immediately; when paused, the current frame re‑renders with new settings)

Notes
- When paused, toggling layers or changing settings re‑renders the current frame so you can tune parameters on a static image.
- Display Max FPS is honored by the app timer; “Play” FPS shows actual display cadence.

---

## Exports

Open Export, choose formats, base name, and destination. Options:

- CSV: horizon coordinates
  - Image → (x, y) per column where y is height from bottom; -1 indicates missing
  - Video → one line (list of y) per sampled frame
- Graph: matplotlib visualization
- Overlay: original media with horizon drawn
- MIDI: horizon → notes (simple C‑major mapping)
- Audio (WAV): generates MIDI in memory (or to disk if MIDI is also selected), then renders with FluidSynth
  - Requires `.sf2` path in the dialog

Sampling rate (processing frequency)
- Videos are sampled according to “Processing FPS.”
- Example: 5 FPS over a 5s video yields ~25 sampled frames → CSV rows for 25 frames (plus columns per frame if exporting lines).

Progress
- Long video exports show a cancelable progress dialog and keep the UI responsive.

---

## Codebase structure

```
Sonic-Skyline/
  app.py                      # App entry; window wiring; playback UI; export orchestration
  core/
    constants.py              # Fonts, sizes, colors, file filters
    export_manager.py         # Export pipeline (CSV/Graph/Overlay/MIDI/Audio)
  gui/
    export_dialog.py          # Export options dialog
    file_display.py           # Image/video rendering, playback loop, FPS measurement
    file_selection.py         # File selection widget
    finder_settings.py        # Detection, playback, and algorithm settings panel
    ui_components.py          # Reusable UI components (buttons, content area, toggles)
  horizon_finder/
    horizon_finder.py         # HorizonFinder (v1/v2), settings pass‑through
  audio_processing/
    csv_to_midi.py            # CSV → MIDI function (no hardcoded paths)
    midi_to_audio.py          # MIDI → WAV via FluidSynth
  requirements.txt
  README.md
```

---

## Development tips

- Algorithm selection: `FinderSettingsPanel` → Algorithm combo (`v1`, `v2`)
  - v1: bottom‑up nearest‑edge per column with continuity threshold
  - v2: top‑down first edge per column, continuity smoothing (default; faster)
- Coordinate convention: `y` values are heights from bottom (OpenCV draws with `y` from top; conversions handled in renderers)
- The app avoids “baking” overlays into the image — the line is drawn at render time based on visibility toggles

