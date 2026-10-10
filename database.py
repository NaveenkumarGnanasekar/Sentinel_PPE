"""
database.py
-----------
SQLite persistence layer for the PPE Sentinel dashboard.

Keeps the exact same table schema used by the original Django/Channels
project (app1/consumers.py -> setup_database) so historical logic,
column order and semantics are preserved:

    detections(id, class_id, class_name, confidence, track_id, bbox, timestamp)

A QMutex guards access because the detection thread writes while the
UI thread reads concurrently.
"""

import os
import sqlite3
from collections import Counter
from datetime import datetime

from PyQt5.QtCore import QMutex, QMutexLocker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "detections.db")

TIME_BUCKETS = [
    ("06:00 - 12:00", 6, 12),
    ("12:00 - 18:00", 12, 18),
    ("18:00 - 24:00", 18, 24),
    ("00:00 - 06:00", 0, 6),
]


class DetectionDB:
    """Thin, thread-safe wrapper around the detections SQLite table."""

    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._mutex = QMutex()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        with QMutexLocker(self._mutex):
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        class_id INTEGER,
                        class_name TEXT,
                        confidence REAL,
                        track_id INTEGER,
                        bbox TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    def insert(self, class_id, class_name, confidence, track_id, bbox, timestamp):
        with QMutexLocker(self._mutex):
            self._conn.execute(
                """INSERT INTO detections
                   (class_id, class_name, confidence, track_id, bbox, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (class_id, class_name, confidence, track_id, str(bbox), timestamp),
            )
            self._conn.commit()

    def clear(self):
        with QMutexLocker(self._mutex):
            self._conn.execute("DELETE FROM detections")
            self._conn.execute("DELETE FROM sqlite_sequence WHERE name='detections'")
            self._conn.commit()

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    def fetch_all(self, limit=None):
        with QMutexLocker(self._mutex):
            q = "SELECT * FROM detections ORDER BY timestamp DESC"
            if limit:
                q += f" LIMIT {int(limit)}"
            return self._conn.execute(q).fetchall()

    def compute_stats(self, limit=None):
        """Reproduces the aggregate stats originally computed in
        app1/views.py (detection_list / fetch_detections)."""
        rows = self.fetch_all(limit=limit)

        total_detections = len(rows)
        class_ids = {row[1] for row in rows}
        class_names = {row[2] for row in rows}
        class_counts = Counter(row[2] for row in rows)

        time_buckets = {label: 0 for label, _, _ in TIME_BUCKETS}
        for row in rows:
            try:
                ts = datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                continue
            hour = ts.hour
            for label, start, end in TIME_BUCKETS:
                if start <= hour < end:
                    time_buckets[label] += 1
                    break

        violations = sum(count for name, count in class_counts.items()
                          if "no " in name.lower())

        return {
            "rows": rows,
            "total_detections": total_detections,
            "total_class_ids": len(class_ids),
            "total_class_names": len(class_names),
            "class_counts": class_counts,
            "most_frequent": class_counts.most_common(6),
            "time_buckets": time_buckets,
            "violations": violations,
        }

    def close(self):
        with QMutexLocker(self._mutex):
            self._conn.close()
