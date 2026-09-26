"""
test_app.py
-----------
Unit tests for the Student Time-Use Analyzer.

Run with:  python -m unittest tests/test_app.py   (from project root)
or:        python -m pytest tests/test_app.py

Covers: adding valid/invalid records, search, filter, totals, percentages,
save/load, and chart generation (smoke test, no display needed).
"""

import os
import sys
import shutil
import tempfile
import unittest

# Make project root importable when running this file directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from validation import validate_record, ValidationError
from data_manager import DataManager
import analysis
import visualization


class TestValidation(unittest.TestCase):
    def test_add_valid_record(self):
        record = validate_record("2026-09-20", "Read Python book", "Study", "2", "30")
        self.assertEqual(record["duration_minutes"], 150)
        self.assertEqual(record["category"], "Study")

    def test_invalid_duration_negative(self):
        with self.assertRaises(ValidationError):
            validate_record("2026-09-20", "Nap", "Sleep", "-1", "0")

    def test_invalid_duration_zero(self):
        with self.assertRaises(ValidationError):
            validate_record("2026-09-20", "Nap", "Sleep", "0", "0")

    def test_empty_activity(self):
        with self.assertRaises(ValidationError):
            validate_record("2026-09-20", "   ", "Study", "1", "0")

    def test_invalid_date_format(self):
        with self.assertRaises(ValidationError):
            validate_record("20-09-2026", "Read", "Study", "1", "0")

    def test_invalid_date_nonexistent(self):
        with self.assertRaises(ValidationError):
            validate_record("2026-02-30", "Read", "Study", "1", "0")

    def test_invalid_category(self):
        with self.assertRaises(ValidationError):
            validate_record("2026-09-20", "Read", "NotACategory", "1", "0")


class TestDataManager(unittest.TestCase):
    def setUp(self):
        # Use a temporary directory so tests never touch real app data
        self.tmp_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.tmp_dir, "test_records.csv")
        self.dm = DataManager(storage_path=self.csv_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_add_record_increases_count(self):
        self.dm.add_record("2026-09-20", "Study DBMS", "Study", 90, "Chapter 3")
        self.assertEqual(len(self.dm.df), 1)

    def test_search_records(self):
        self.dm.add_record("2026-09-20", "Study DBMS", "Study", 90, "")
        self.dm.add_record("2026-09-20", "Play Cricket", "Entertainment", 60, "")
        result = self.dm.search_by_activity("study")
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["activity"], "Study DBMS")

    def test_filter_by_category(self):
        self.dm.add_record("2026-09-20", "Study DBMS", "Study", 90, "")
        self.dm.add_record("2026-09-20", "Sleep", "Sleep", 480, "")
        result = self.dm.filter_by_category("Sleep")
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["category"], "Sleep")

    def test_filter_by_date_range(self):
        self.dm.add_record("2026-09-18", "Study", "Study", 60, "")
        self.dm.add_record("2026-09-25", "Study", "Study", 60, "")
        result = self.dm.filter_by_date_range("2026-09-19", "2026-09-26")
        self.assertEqual(len(result), 1)

    def test_save_and_load_persists_data(self):
        self.dm.add_record("2026-09-20", "Study DBMS", "Study", 90, "")
        # Simulate reopening the app
        new_dm = DataManager(storage_path=self.csv_path)
        self.assertEqual(len(new_dm.df), 1)
        self.assertEqual(new_dm.df.iloc[0]["activity"], "Study DBMS")

    def test_corrupted_file_recovers_gracefully(self):
        with open(self.csv_path, "w") as f:
            f.write("this is not,valid csv data {{{")
        # Should not raise - falls back to empty DataFrame
        dm = DataManager(storage_path=self.csv_path)
        self.assertIsInstance(dm.df, pd.DataFrame)

    def test_update_and_delete_record(self):
        rid = self.dm.add_record("2026-09-20", "Study DBMS", "Study", 90, "")
        self.dm.update_record(rid, "2026-09-20", "Study OS", "Study", 120, "")
        self.assertEqual(self.dm.df.iloc[0]["activity"], "Study OS")
        self.dm.delete_record(rid)
        self.assertEqual(len(self.dm.df), 0)


class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame([
            {"id": 1, "date": "2026-09-20", "activity": "Study DBMS", "category": "Study",
             "duration_minutes": 120, "description": ""},
            {"id": 2, "date": "2026-09-20", "activity": "Sleep", "category": "Sleep",
             "duration_minutes": 480, "description": ""},
            {"id": 3, "date": "2026-09-21", "activity": "Cricket", "category": "Entertainment",
             "duration_minutes": 60, "description": ""},
        ])

    def test_calculating_totals(self):
        totals = analysis.category_totals_hours(self.df)
        self.assertAlmostEqual(totals["Study"], 2.0)
        self.assertAlmostEqual(totals["Sleep"], 8.0)

    def test_calculating_percentages(self):
        percentages = analysis.category_percentages(self.df)
        total_pct = round(percentages.sum(), 1)
        self.assertEqual(total_pct, 100.0)

    def test_most_time_consuming_category(self):
        top_cat, hours = analysis.most_time_consuming_category(self.df)
        self.assertEqual(top_cat, "Sleep")

    def test_summary_statistics(self):
        stats = analysis.summary_statistics(self.df)
        self.assertEqual(stats["total_records"], 3)
        self.assertEqual(stats["days_tracked"], 2)


class TestVisualization(unittest.TestCase):
    def test_charts_generate_without_error(self):
        """Smoke test: chart functions should run without raising, using
        a plain object standing in for a Tkinter frame is not enough since
        FigureCanvasTkAgg needs a real widget, so this uses Tk in headless-safe
        mode where a display is available. If no display is available this
        test is skipped rather than failing the whole suite."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
        except Exception:
            self.skipTest("No display available to test Tkinter chart embedding.")
            return

        df = pd.DataFrame([
            {"id": 1, "date": "2026-09-20", "activity": "Study", "category": "Study",
             "duration_minutes": 60, "description": ""},
        ])
        frame = tk.Frame(root)
        try:
            visualization.draw_category_pie_chart(frame, df)
            visualization.draw_category_bar_chart(frame, df)
            visualization.draw_daily_trend_line_chart(frame, df)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
