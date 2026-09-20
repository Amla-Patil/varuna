# Varuna — Underwater Sonar Object Detection (Desktop App)

SIH 2026 — PySide6 desktop UI integrated with a trained YOLO11s sonar
detection pipeline (NLM preprocessing → YOLO11s detection → annotated
results).

## Project layout

```
varuna/
├── app/
│   ├── main.py                Entry point
│   ├── marine_app.py          Main window, pages, detection UI
│   ├── sonar_integration.py   Bridge between the GUI and sonar_model/
│   └── splash.py              Splash screen
├── sonar_model/                Sonar detection pipeline (kept separate from
│   ├── inference/               the UI - only sonar_integration.py touches it)
│   │   ├── detector.py          Ultralytics YOLO wrapper
│   │   ├── inference_pipeline.py  End-to-end pipeline + JSON saving
│   │   └── visualization.py     Draws bounding boxes / labels
│   ├── preprocessing/
│   │   └── nlm_preprocessing.py  Non-Local Means denoising (matches training)
│   ├── models/
│   │   └── yolo11s_baseline_640_best.pt  Trained weights (bundled default)
│   └── config/
│       └── classes.json         Class ID → name mapping
├── results/                    Overlay images + JSON written here at runtime
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

## Run

```bash
cd app
python main.py
```

The app launches fast — `torch`/`ultralytics` are only imported the first
time you run a detection, not at startup.

## Using the app

1. Open the **Detection** page from the sidebar.
2. Click **Browse** and select a sonar image (PNG/JPG/JPEG/BMP/TIF/TIFF).
3. **Model weights** default to the bundled trained model
   (`sonar_model/models/yolo11s_baseline_640_best.pt`). Click its **Browse**
   button only if you want to swap in a different `.pt` checkpoint.
4. Set a confidence threshold (0–1, e.g. `0.25`).
5. Click **Start Analysis**. Inference runs on a background thread so the UI
   stays responsive.
6. Results appear as an annotated overlay plus a per-class detection
   summary. Both the overlay image and the full JSON result are also saved
   to `results/<image_name>_overlay.png` and
   `results/<image_name>_detection.json`.

The model is loaded once and cached for the app's lifetime — only the
*first* analysis after launch pays the model-load cost. A GPU is used
automatically via CUDA if one is available, otherwise inference runs on CPU.

## Detected classes

| ID | Class |
|----|-------|
| 0  | crab_pot |
| 1  | submarine_pipeline |
| 2  | shipwreck |
| 3  | ghost_net |
| 4  | mine_cylinder |

## Notes

- Preprocessing (NLM denoising) is applied identically to what was used
  during training, so detection quality should match evaluation results.
- CSV/mission-file selection is present in the file picker for future
  mission-log workflows, but current detection only supports image inputs.
