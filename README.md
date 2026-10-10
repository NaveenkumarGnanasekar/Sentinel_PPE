# Sentinel — PPE Compliance Command Center (PyQt5 Desktop Edition)

A desktop rebuild of **[Real-Time-PPE-Detection-with-Django-and-Yolo](https://github.com/ApyCoder1/Real-Time-PPE-Detection-with-Django-and-Yolo)**.

The original project streamed YOLO detections from a Django Channels
WebSocket server to a browser dashboard. This version keeps the exact
same **detection logic** (same YOLO model, same IoU-based object
tracker, same sustained-violation alert rule, same SQLite logging
schema) but replaces the web stack entirely with a **native PyQt5
desktop application** and a brand-new, original UI design.

## What stayed the same (the "logic")

- YOLO inference on every frame using the trained `best.pt` weights.
- Greedy IoU tracker (`IoU > 0.3`) that assigns incrementing track IDs
  to detections across frames — ported line-for-line from
  `app1/consumers.py`.
- Sustained-violation rule: if class `1` (No Vest) or `2` (No Helmet)
  is tracked on the same ID for **more than 3 seconds**, an audio
  alert fires.
- Adjustable confidence threshold and per-class filtering.
- Every detection is logged to SQLite with
  `(class_id, class_name, confidence, track_id, bbox, timestamp)`.
- The same dashboard statistics: total detections, class counts,
  most frequent classes, and detections bucketed by time-of-day.

## What's new (the "UI")

- A completely original **PyQt5 desktop interface** ("Sentinel"),
  dark industrial-safety theme, no HTML/Chart.js/Bootstrap left.
- **Live Monitor** page — camera feed with on-frame overlays, a live
  scrolling event feed, a sustained-alert banner, and live-tunable
  confidence/class controls.
- **Analytics** page — KPI cards + an embedded matplotlib donut chart
  and time-of-day bar chart, auto-refreshing every 2 seconds.
- **Detection Logs** page — searchable/filterable table with CSV
  export and a "clear log" action (the original had no export).
- **Settings** page — camera index, model path and alert sound
  configuration.

## Project structure

```
ppe_dashboard/
├── main.py                  # entry point
├── database.py               # SQLite persistence (same schema)
├── detection_worker.py       # QThread: camera + YOLO + tracker + alerts
├── requirements.txt
├── assets/
│   ├── best.pt                # YOLO weights (copied from the original repo)
│   └── alert.mp3               # alert sound (copied from the original repo)
└── ui/
    ├── theme.py                # QSS stylesheet / color palette
    ├── widgets.py               # StatCard, DonutChart, BarChart, etc.
    ├── main_window.py            # sidebar nav + page routing + worker control
    └── pages/
        ├── live_page.py
        ├── analytics_page.py
        ├── logs_page.py
        └── settings_page.py
```

## Running it

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

> **Note:** `torch` + `ultralytics` are heavy dependencies (GPU
> optional). On a laptop without a GPU, inference runs on CPU and is
> slower than a discrete GPU setup — lower the input resolution or
> confidence threshold if the feed feels sluggish.

## Class map (from the trained model)

| Class ID | Meaning      | Treated as   |
|----------|--------------|--------------|
| 1        | No Vest      | Violation ⚠️ |
| 2        | No Helmet    | Violation ⚠️ |
| 3        | Safety Vest  | Compliant ✅ |
| 4        | Helmet       | Compliant ✅ |

## Credits

Original detection pipeline, model and dataset by **ApyCoder**
(`Real-Time-PPE-Detection-with-Django-and-Yolo`, MIT License). This
repository is a UI/platform rebuild for academic/college project use.
# Sentinel_PPE
