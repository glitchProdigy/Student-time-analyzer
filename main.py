"""
main.py
-------
Student Time-Use Analyzer - Tkinter GUI and application control.

Run with:  python main.py

This module only handles GUI layout and event wiring. All business logic
lives in data_manager.py, analysis.py, validation.py and visualization.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import pandas as pd

from data_manager import DataManager
from validation import validate_record, ValidationError, VALID_CATEGORIES
import analysis
import visualization


class TimeUseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Time-Use Analyzer")
        self.geometry("1000x680")
        self.minsize(900, 600)

        # Central data manager instance shared across all tabs
        self.dm = DataManager()

        # Track which record id is currently loaded for editing (None = add mode)
        self.editing_id = None

        self._build_ui()
        self.refresh_all()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_add = ttk.Frame(self.notebook)
        self.tab_records = ttk.Frame(self.notebook)
        self.tab_analysis = ttk.Frame(self.notebook)
        self.tab_charts = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_add, text="Add / Edit Record")
        self.notebook.add(self.tab_records, text="Records")
        self.notebook.add(self.tab_analysis, text="Analysis")
        self.notebook.add(self.tab_charts, text="Charts")

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_all())

        self._build_dashboard_tab()
        self._build_add_tab()
        self._build_records_tab()
        self._build_analysis_tab()
        self._build_charts_tab()

    # ---------------- Dashboard ----------------
    def _build_dashboard_tab(self):
        frame = self.tab_dashboard
        title = ttk.Label(frame, text="Dashboard", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", padx=12, pady=(12, 4))

        self.cards_frame = ttk.Frame(frame)
        self.cards_frame.pack(fill="x", padx=12, pady=8)

        self.card_labels = {}
        card_names = [
            ("total_records", "Total Records"),
            ("total_hours", "Total Hours Logged"),
            ("average_daily_hours", "Avg Hours / Day"),
            ("days_tracked", "Days Tracked"),
            ("top_category", "Top Category"),
        ]
        for i, (key, label) in enumerate(card_names):
            card = ttk.LabelFrame(self.cards_frame, text=label)
            card.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")
            self.cards_frame.columnconfigure(i, weight=1)
            value_lbl = ttk.Label(card, text="-", font=("Segoe UI", 14, "bold"))
            value_lbl.pack(padx=10, pady=14)
            self.card_labels[key] = value_lbl

        ttk.Label(frame, text="Top 5 Most Time-Consuming Activities",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(16, 4))

        columns = ("activity", "total_hours")
        self.top_activities_tree = ttk.Treeview(frame, columns=columns, show="headings", height=6)
        self.top_activities_tree.heading("activity", text="Activity")
        self.top_activities_tree.heading("total_hours", text="Total Hours")
        self.top_activities_tree.pack(fill="x", padx=12, pady=4)

        ttk.Button(frame, text="Refresh Dashboard", command=self.refresh_all).pack(
            anchor="w", padx=12, pady=10
        )

    # ---------------- Add / Edit Record ----------------
    def _build_add_tab(self):
        frame = self.tab_add
        title = ttk.Label(frame, text="Add / Edit Time-Use Record", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 10))

        form = ttk.Frame(frame)
        form.grid(row=1, column=0, sticky="nw", padx=12)

        # Date
        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=6)
        self.entry_date = ttk.Entry(form, width=30)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.grid(row=0, column=1, pady=6, sticky="w")

        # Activity
        ttk.Label(form, text="Activity Name:").grid(row=1, column=0, sticky="w", pady=6)
        self.entry_activity = ttk.Entry(form, width=30)
        self.entry_activity.grid(row=1, column=1, pady=6, sticky="w")

        # Category
        ttk.Label(form, text="Category:").grid(row=2, column=0, sticky="w", pady=6)
        self.combo_category = ttk.Combobox(form, values=VALID_CATEGORIES, width=27, state="readonly")
        self.combo_category.grid(row=2, column=1, pady=6, sticky="w")

        # Duration
        ttk.Label(form, text="Duration - Hours:").grid(row=3, column=0, sticky="w", pady=6)
        dur_frame = ttk.Frame(form)
        dur_frame.grid(row=3, column=1, pady=6, sticky="w")
        self.entry_hours = ttk.Entry(dur_frame, width=8)
        self.entry_hours.insert(0, "0")
        self.entry_hours.pack(side="left")
        ttk.Label(dur_frame, text="  Minutes:").pack(side="left")
        self.entry_minutes = ttk.Entry(dur_frame, width=8)
        self.entry_minutes.insert(0, "0")
        self.entry_minutes.pack(side="left")

        # Description
        ttk.Label(form, text="Description (optional):").grid(row=4, column=0, sticky="nw", pady=6)
        self.entry_description = tk.Text(form, width=32, height=4)
        self.entry_description.grid(row=4, column=1, pady=6, sticky="w")

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=14, sticky="w")

        self.btn_save = ttk.Button(btn_frame, text="Add Record", command=self.on_save_record)
        self.btn_save.pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_form).pack(side="left")

        self.form_status_label = ttk.Label(form, text="", foreground="green")
        self.form_status_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=6)

    # ---------------- Records (table + search/filter) ----------------
    def _build_records_tab(self):
        frame = self.tab_records
        title = ttk.Label(frame, text="Records", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", padx=12, pady=(12, 4))

        controls = ttk.Frame(frame)
        controls.pack(fill="x", padx=12, pady=6)

        ttk.Label(controls, text="Search activity:").grid(row=0, column=0, sticky="w")
        self.search_entry = ttk.Entry(controls, width=18)
        self.search_entry.grid(row=0, column=1, padx=4)

        ttk.Label(controls, text="Category:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.filter_category_combo = ttk.Combobox(
            controls, values=["All"] + VALID_CATEGORIES, width=14, state="readonly"
        )
        self.filter_category_combo.set("All")
        self.filter_category_combo.grid(row=0, column=3, padx=4)

        ttk.Label(controls, text="Date:").grid(row=0, column=4, sticky="w", padx=(10, 0))
        self.filter_date_entry = ttk.Entry(controls, width=12)
        self.filter_date_entry.grid(row=0, column=5, padx=4)

        ttk.Label(controls, text="From:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.filter_start_entry = ttk.Entry(controls, width=12)
        self.filter_start_entry.grid(row=1, column=1, pady=(6, 0), sticky="w")

        ttk.Label(controls, text="To:").grid(row=1, column=2, sticky="w", pady=(6, 0))
        self.filter_end_entry = ttk.Entry(controls, width=12)
        self.filter_end_entry.grid(row=1, column=3, pady=(6, 0), sticky="w")

        ttk.Button(controls, text="Apply Filters", command=self.on_apply_filters).grid(
            row=1, column=4, padx=6, pady=(6, 0)
        )
        ttk.Button(controls, text="Reset", command=self.on_reset_filters).grid(
            row=1, column=5, padx=6, pady=(6, 0)
        )

        # Table
        columns = ("id", "date", "activity", "category", "duration", "description")
        self.records_tree = ttk.Treeview(frame, columns=columns, show="headings", height=16)
        headings = {
            "id": "ID", "date": "Date", "activity": "Activity", "category": "Category",
            "duration": "Duration", "description": "Description",
        }
        widths = {"id": 40, "date": 90, "activity": 150, "category": 100, "duration": 90, "description": 260}
        for col in columns:
            self.records_tree.heading(col, text=headings[col])
            self.records_tree.column(col, width=widths[col])
        self.records_tree.pack(fill="both", expand=True, padx=12, pady=8)

        action_frame = ttk.Frame(frame)
        action_frame.pack(fill="x", padx=12, pady=6)
        ttk.Button(action_frame, text="Edit Selected", command=self.on_edit_selected).pack(side="left", padx=4)
        ttk.Button(action_frame, text="Delete Selected", command=self.on_delete_selected).pack(side="left", padx=4)

    # ---------------- Analysis ----------------
    def _build_analysis_tab(self):
        frame = self.tab_analysis
        title = ttk.Label(frame, text="Time Analysis", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", padx=12, pady=(12, 4))

        self.analysis_text = tk.Text(frame, height=16, wrap="word")
        self.analysis_text.pack(fill="both", expand=True, padx=12, pady=6)
        self.analysis_text.configure(state="disabled")

        compare_frame = ttk.LabelFrame(frame, text="Compare Two Periods (e.g. two weeks)")
        compare_frame.pack(fill="x", padx=12, pady=8)

        ttk.Label(compare_frame, text="Period 1 From:").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.cmp1_start = ttk.Entry(compare_frame, width=12)
        self.cmp1_start.grid(row=0, column=1, padx=4)
        ttk.Label(compare_frame, text="To:").grid(row=0, column=2, padx=4)
        self.cmp1_end = ttk.Entry(compare_frame, width=12)
        self.cmp1_end.grid(row=0, column=3, padx=4)

        ttk.Label(compare_frame, text="Period 2 From:").grid(row=1, column=0, padx=4, pady=4, sticky="w")
        self.cmp2_start = ttk.Entry(compare_frame, width=12)
        self.cmp2_start.grid(row=1, column=1, padx=4)
        ttk.Label(compare_frame, text="To:").grid(row=1, column=2, padx=4)
        self.cmp2_end = ttk.Entry(compare_frame, width=12)
        self.cmp2_end.grid(row=1, column=3, padx=4)

        ttk.Button(compare_frame, text="Compare", command=self.on_compare_periods).grid(
            row=0, column=4, rowspan=2, padx=10
        )

        self.compare_result_text = tk.Text(frame, height=8, wrap="word")
        self.compare_result_text.pack(fill="x", padx=12, pady=6)
        self.compare_result_text.configure(state="disabled")

    # ---------------- Charts ----------------
    def _build_charts_tab(self):
        frame = self.tab_charts
        title = ttk.Label(frame, text="Visual Reports", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", padx=12, pady=(12, 4))

        chart_notebook = ttk.Notebook(frame)
        chart_notebook.pack(fill="both", expand=True, padx=12, pady=8)

        self.pie_frame = ttk.Frame(chart_notebook)
        self.bar_frame = ttk.Frame(chart_notebook)
        self.line_frame = ttk.Frame(chart_notebook)

        chart_notebook.add(self.pie_frame, text="Category % (Pie)")
        chart_notebook.add(self.bar_frame, text="Category Hours (Bar)")
        chart_notebook.add(self.line_frame, text="Daily Trend (Line)")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def on_save_record(self):
        try:
            clean = validate_record(
                self.entry_date.get(),
                self.entry_activity.get(),
                self.combo_category.get(),
                self.entry_hours.get(),
                self.entry_minutes.get(),
                self.entry_description.get("1.0", "end"),
            )
        except ValidationError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        try:
            if self.editing_id is None:
                self.dm.add_record(**clean)
                self.form_status_label.config(text="Record added successfully.", foreground="green")
            else:
                self.dm.update_record(self.editing_id, **clean)
                self.form_status_label.config(text="Record updated successfully.", foreground="green")
                self.editing_id = None
                self.btn_save.config(text="Add Record")
        except (ValueError, IOError) as e:
            messagebox.showerror("Save Error", f"Could not save record:\n{e}")
            return

        self.clear_form(keep_status=True)
        self.refresh_all()

    def clear_form(self, keep_status=False):
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_activity.delete(0, "end")
        self.combo_category.set("")
        self.entry_hours.delete(0, "end")
        self.entry_hours.insert(0, "0")
        self.entry_minutes.delete(0, "end")
        self.entry_minutes.insert(0, "0")
        self.entry_description.delete("1.0", "end")
        self.editing_id = None
        self.btn_save.config(text="Add Record")
        if not keep_status:
            self.form_status_label.config(text="")

    def on_apply_filters(self):
        df = self.dm.get_all()
        keyword = self.search_entry.get().strip()
        category = self.filter_category_combo.get()
        date_val = self.filter_date_entry.get().strip()
        start_val = self.filter_start_entry.get().strip()
        end_val = self.filter_end_entry.get().strip()

        try:
            if keyword:
                df = self.dm.search_by_activity(keyword)
            if category and category != "All":
                df = df[df["category"] == category] if not df.empty else df
            if date_val:
                df = df[df["date"] == date_val] if not df.empty else df
            if start_val and end_val:
                df = df[(df["date"] >= start_val) & (df["date"] <= end_val)] if not df.empty else df
        except Exception as e:
            messagebox.showerror("Filter Error", f"Could not apply filters:\n{e}")
            return

        self._populate_records_tree(df)

    def on_reset_filters(self):
        self.search_entry.delete(0, "end")
        self.filter_category_combo.set("All")
        self.filter_date_entry.delete(0, "end")
        self.filter_start_entry.delete(0, "end")
        self.filter_end_entry.delete(0, "end")
        self._populate_records_tree(self.dm.get_all())

    def on_edit_selected(self):
        selected = self.records_tree.selection()
        if not selected:
            messagebox.showinfo("Edit Record", "Please select a record first.")
            return
        values = self.records_tree.item(selected[0], "values")
        record_id = int(values[0])
        row = self.dm.df[self.dm.df["id"] == record_id]
        if row.empty:
            messagebox.showerror("Edit Record", "Record no longer exists.")
            return
        row = row.iloc[0]

        self.notebook.select(self.tab_add)
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, row["date"])
        self.entry_activity.delete(0, "end")
        self.entry_activity.insert(0, row["activity"])
        self.combo_category.set(row["category"])
        hours, minutes = divmod(int(row["duration_minutes"]), 60)
        self.entry_hours.delete(0, "end")
        self.entry_hours.insert(0, str(hours))
        self.entry_minutes.delete(0, "end")
        self.entry_minutes.insert(0, str(minutes))
        self.entry_description.delete("1.0", "end")
        self.entry_description.insert("1.0", row["description"])

        self.editing_id = record_id
        self.btn_save.config(text="Update Record")
        self.form_status_label.config(text=f"Editing record #{record_id}", foreground="blue")

    def on_delete_selected(self):
        selected = self.records_tree.selection()
        if not selected:
            messagebox.showinfo("Delete Record", "Please select a record first.")
            return
        values = self.records_tree.item(selected[0], "values")
        record_id = int(values[0])
        if not messagebox.askyesno("Confirm Delete", f"Delete record #{record_id}?"):
            return
        try:
            self.dm.delete_record(record_id)
        except (ValueError, IOError) as e:
            messagebox.showerror("Delete Error", str(e))
            return
        self.refresh_all()

    def on_compare_periods(self):
        s1, e1 = self.cmp1_start.get().strip(), self.cmp1_end.get().strip()
        s2, e2 = self.cmp2_start.get().strip(), self.cmp2_end.get().strip()
        if not all([s1, e1, s2, e2]):
            messagebox.showerror("Compare Periods", "Please fill in all four date fields (YYYY-MM-DD).")
            return
        try:
            result = analysis.compare_periods(self.dm.df, s1, e1, s2, e2)
        except Exception as e:
            messagebox.showerror("Compare Error", f"Could not compare periods:\n{e}")
            return

        lines = [f"Period 1: {s1} to {e1}   |   Period 2: {s2} to {e2}\n"]
        lines.append(f"{'Category':<15}{'Period 1 (h)':<15}{'Period 2 (h)':<15}{'Change (h)':<12}")
        categories = result["period1"].index
        if len(categories) == 0:
            lines.append("No data available in these periods.")
        else:
            for cat in categories:
                p1v = result["period1"][cat]
                p2v = result["period2"][cat]
                diff = result["difference"][cat]
                lines.append(f"{cat:<15}{p1v:<15}{p2v:<15}{diff:<12}")

        self.compare_result_text.configure(state="normal")
        self.compare_result_text.delete("1.0", "end")
        self.compare_result_text.insert("1.0", "\n".join(lines))
        self.compare_result_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # Refresh / populate helpers
    # ------------------------------------------------------------------
    def refresh_all(self):
        self._populate_records_tree(self.dm.get_all())
        self._refresh_dashboard()
        self._refresh_analysis_text()
        self._refresh_charts()

    def _populate_records_tree(self, df: pd.DataFrame):
        for row in self.records_tree.get_children():
            self.records_tree.delete(row)
        for _, r in df.iterrows():
            hours, minutes = divmod(int(r["duration_minutes"]), 60)
            duration_str = f"{hours}h {minutes}m"
            self.records_tree.insert(
                "", "end",
                values=(r["id"], r["date"], r["activity"], r["category"], duration_str, r["description"]),
            )

    def _refresh_dashboard(self):
        stats = analysis.summary_statistics(self.dm.df)
        self.card_labels["total_records"].config(text=str(stats["total_records"]))
        self.card_labels["total_hours"].config(text=f'{stats["total_hours"]} h')
        self.card_labels["average_daily_hours"].config(text=f'{stats["average_daily_hours"]} h')
        self.card_labels["days_tracked"].config(text=str(stats["days_tracked"]))
        top_cat = stats["top_category"] or "-"
        self.card_labels["top_category"].config(text=f'{top_cat}')

        for row in self.top_activities_tree.get_children():
            self.top_activities_tree.delete(row)
        top_activities = analysis.most_time_consuming_activities(self.dm.df, top_n=5)
        for _, r in top_activities.iterrows():
            self.top_activities_tree.insert("", "end", values=(r["activity"], r["total_hours"]))

    def _refresh_analysis_text(self):
        df = self.dm.df
        totals_hours = analysis.category_totals_hours(df)
        percentages = analysis.category_percentages(df)
        top_cat, top_cat_hours = analysis.most_time_consuming_category(df)

        lines = ["CATEGORY-WISE TOTALS AND PERCENTAGES\n" + "-" * 45]
        if totals_hours.empty:
            lines.append("No records yet. Add some records to see analysis.")
        else:
            for cat in totals_hours.index:
                lines.append(f"{cat:<15} {totals_hours[cat]:>8.2f} h   ({percentages[cat]:>5.1f}%)")
            lines.append("")
            lines.append(f"Most time-consuming category: {top_cat} ({top_cat_hours} h)")

        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", "\n".join(lines))
        self.analysis_text.configure(state="disabled")

    def _refresh_charts(self):
        df = self.dm.df
        visualization.draw_category_pie_chart(self.pie_frame, df)
        visualization.draw_category_bar_chart(self.bar_frame, df)
        visualization.draw_daily_trend_line_chart(self.line_frame, df)


if __name__ == "__main__":
    app = TimeUseApp()
    app.mainloop()
