# Project Submission — Sentinel

## 1. Project title
**Sentinel — Real-Time PPE Compliance Command Center**

## 2. Short description
Sentinel is a desktop application that uses a YOLO object-detection model to watch a live camera feed and
detect whether workers are wearing a safety vest and helmet. When a violation persists for more than three
seconds it raises an on-screen and audio alert, and every detection is logged to a database for analytics,
search and CSV export.

## 3. Links
| Item | Link |
|---|---|
| GitHub repository (source code + README) | https://github.com/NaveenkumarGnanasekar/Sentinel_PPE |
| Demo video (in the repo) | `demo/demo.mp4` (also `demo/demo.webm`) |
| Architecture diagram | `docs/architecture.png` |
| Screenshots | `docs/screenshots/` |
| Deployment / testing | Desktop app (no hosted URL). Reviewers can test with the repo's *"Testing without a camera or a worksite"* section — a bundled demo database loads the Analytics and Logs pages instantly. |

## 4. Project description

### Problem statement
Helmets and high-visibility vests prevent serious injuries on construction sites, factories and warehouses,
but PPE compliance is normally enforced by supervisors walking the floor. That does not scale: one person
cannot watch every worker, camera and shift, violations are noticed late or never, and there is no objective
record of how often they happen. Sentinel automates the watching and keeps an auditable log.

### Target users
- **Site / EHS safety officers** — real-time alerts and an audit trail.
- **Supervisors and foremen** — a live view of who is missing a vest or helmet.
- **Facility and operations managers** — compliance and time-of-day analytics to spot risky shifts.
- **Students and researchers** — a readable reference for a YOLO + tracking + desktop-UI pipeline.

### Technical approach
A background thread (`QThread`) captures frames with OpenCV and runs them through a custom-trained YOLO
model that recognises four classes: *NO-Safety Vest*, *No Helmet*, *Safety Vest* and *shoes*. Detections are
filtered by a live-adjustable confidence threshold and class selection, then matched across frames with a
greedy IoU tracker (IoU > 0.3) so each object keeps a persistent ID. A rule engine flags a **sustained
violation** when a *No Vest* or *No Helmet* detection stays on the same ID for more than 3 seconds — this
avoids false alarms from single-frame flickers — and triggers the alert banner and sound. Every detection is
stored in SQLite (class, confidence, track ID, bounding box, IST timestamp) behind a mutex for thread
safety. The annotated frames and detections reach the PyQt5 interface via Qt signals, so the UI never
freezes; the Analytics and Logs pages read the database on a timer.

### Technologies / components used
- **Python 3**, **Ultralytics YOLO**, **PyTorch** — detection model and inference
- **OpenCV** — camera capture and frame annotation
- **PyQt5** with a custom QSS dark theme — native desktop UI (Live Monitor, Analytics, Logs, Settings)
- **Matplotlib** — embedded donut and bar charts
- **SQLite** — detection log and statistics
- **pygame** — audio alerts · **pytz** — timestamps (Asia/Kolkata)
- **Qt concurrency primitives** — `QThread`, signals/slots, `QMutex`

### Real-world impact
- Surfaces persistent violations within seconds instead of waiting for a supervisor to notice.
- Applies the same rule to every worker on every shift, without fatigue or distraction.
- Turns anecdotes into data — the log and analytics support audits, safety training and incident reviews.
- Runs on a single laptop and ordinary camera: no cloud, server or special hardware.
- The pipeline is model-agnostic, so it can be extended to other safety rules (gloves, goggles, zones).

### Known limitations (for honesty in Q&A)
One camera at a time; simple IoU tracking can swap IDs under occlusion; counts are detection events rather
than unique workers; the model has no positive "Helmet" class; formal accuracy benchmarking is not part of
this repository.

## 5. Credits
Detection pipeline, trained model and dataset originate from ApyCoder's
*Real-Time-PPE-Detection-with-Django-and-Yolo* (MIT). Sentinel re-implements the platform as a native PyQt5
desktop application with a new UI, live analytics, log export and configuration.
