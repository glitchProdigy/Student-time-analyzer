# Student Time-Use Analyzer

A desktop application (Tkinter GUI) that helps a student record how their
available time is spent — on study, travel, entertainment, sleep, personal
work and other activities — and provides useful analysis of that time
distribution.

## 1. Project Description

Students often lose track of how their day is actually spent. This
application lets a student log each activity with a date, category and
duration, then instantly see totals, percentages, top time-consumers, and
visual charts of their time usage, plus compare different periods (e.g. this
week vs last week).

## 2. Objectives

- Provide a simple GUI to record daily activities.
- Store records persistently so data survives app restarts.
- Calculate category-wise totals and percentage distribution.
- Identify the most time-consuming category and individual activities.
- Compare time usage between different periods.
- Visualize the data using pie, bar and line charts.
- Validate all user input and handle errors/corrupted files gracefully.

## 3. Features

- Add / Edit / Delete time-use records.
- Search by activity name, filter by category, date, or date range.
- Dashboard with summary cards (total records, total hours, average
  hours/day, days tracked, top category).
- Analysis tab: category totals, percentages, top category, top 5
  activities, and two-period comparison.
- Charts tab: donut/pie chart (% by category), bar chart (hours by
  category), line chart (daily trend).
- CSV (default) or JSON persistent storage.
- Full input validation with clear Tkinter message-box errors.
- Exception handling around file I/O, parsing, and chart generation.

## 4. Technologies / Libraries Used

| Technology | Purpose |
|---|---|
| Python 3.9+ | Core language |
| Tkinter (`ttk`) | Desktop GUI |
| Pandas | DataFrame storage, filtering, grouping/statistics |
| NumPy | Numerical calculations (mean, array differences) |
| Matplotlib | Pie, bar and line chart visualizations |
| CSV / JSON | File-based persistent storage |

## 5. Project Structure

```
student_time_use_analyzer/
├── main.py              # Tkinter GUI and application control
├── data_manager.py      # File handling, CRUD, load/save (Pandas)
├── analysis.py          # Calculations, filtering, statistics, comparisons
├── visualization.py     # Matplotlib charts embedded in Tkinter
├── validation.py        # Input validation and custom exceptions
├── data/
│   └── time_records.csv # Auto-created persistent data file
├── tests/
│   └── test_app.py      # unittest test suite
├── sample_data.csv      # Sample records you can copy into data/
├── requirements.txt
└── README.md
```

### Module Explanations

- **validation.py** — Standalone functions (`validate_date`,
  `validate_duration`, etc.) and a `ValidationError` exception. No GUI or
  file dependency, so it is fully unit-testable.
- **data_manager.py** — `DataManager` class. Holds the Pandas DataFrame in
  memory, loads/saves it to CSV or JSON, and exposes
  `add_record / update_record / delete_record / search_by_activity /
  filter_by_category / filter_by_date / filter_by_date_range`. Recovers
  gracefully from a missing or corrupted data file.
- **analysis.py** — Pure functions that take a DataFrame and return
  Pandas/NumPy-computed statistics: `category_totals_hours`,
  `category_percentages`, `most_time_consuming_category`,
  `most_time_consuming_activities`, `summary_statistics`,
  `compare_periods`, `daily_totals_hours`.
- **visualization.py** — `draw_category_pie_chart`, `draw_category_bar_chart`,
  `draw_daily_trend_line_chart`. Each builds a Matplotlib `Figure` and embeds
  it into a Tkinter frame via `FigureCanvasTkAgg`, with a fallback error
  label if chart generation fails.
- **main.py** — `TimeUseApp(tk.Tk)` class with a `ttk.Notebook` of 5 tabs
  (Dashboard, Add/Edit Record, Records, Analysis, Charts). Wires GUI events
  to the other four modules; contains no business logic itself.

## 6. GUI Layout

- **Dashboard** — Summary cards (Total Records, Total Hours, Avg Hours/Day,
  Days Tracked, Top Category) + a table of the top 5 most time-consuming
  activities.
- **Add / Edit Record** — Form with Date, Activity, Category (dropdown),
  Duration (hours + minutes), Description, and Save/Clear buttons. The same
  form is reused for editing (pre-filled) via the Records tab.
- **Records** — Search box, category dropdown filter, exact-date filter,
  date-range filter, Apply/Reset buttons, and a table (Treeview) of records
  with Edit/Delete actions.
- **Analysis** — Text report of category totals, percentages, and the top
  category, plus a two-period comparison tool (enter two date ranges to
  compare category hours side by side).
- **Charts** — Tabbed sub-notebook: Pie (category %), Bar (category hours),
  Line (daily trend).

## 7. Data Format / Schema

Stored as `data/time_records.csv` (or `.json`), one row per record:

| Column | Type | Description |
|---|---|---|
| id | int | Auto-incrementing unique id |
| date | str `YYYY-MM-DD` | Validated calendar date, not in the future |
| activity | str | Non-empty, max 100 chars |
| category | str | One of Study, Travel, Entertainment, Sleep, Personal, Other |
| duration_minutes | int | 1–1440 (up to 24 hours) |
| description | str | Optional, max 300 chars |

## 8. Installation

```bash
# 1. (Optional) create a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

## 9. How to Run

```bash
python main.py
```

The app will create `data/time_records.csv` automatically on first run. To
start with example data instead, copy the provided sample file:

```bash
cp sample_data.csv data/time_records.csv      # macOS/Linux
copy sample_data.csv data\time_records.csv    # Windows
```

## 10. How the Application Works

1. On startup, `DataManager` loads existing records from `data/time_records.csv`
   into a Pandas DataFrame (or starts empty if none exists).
2. Adding a record: the form values pass through `validation.validate_record()`;
   if valid, `DataManager.add_record()` appends a row and immediately saves
   to disk.
3. Editing: selecting a row in Records → "Edit Selected" loads its values
   back into the Add/Edit form; saving calls `update_record()` instead of
   `add_record()`.
4. Search/Filter: the Records tab calls the matching `DataManager` method
   and repopulates the table with the filtered DataFrame.
5. Analysis/Charts tabs call functions in `analysis.py`
   (Pandas `groupby`, NumPy `mean`) and `visualization.py` (Matplotlib)
   directly on the current DataFrame, refreshing whenever the underlying
   data changes.

## 11. Testing

### Automated tests (`tests/test_app.py`)

Run from the project root:

```bash
python -m unittest tests/test_app.py -v
```

Covers:
- Adding a valid record
- Invalid duration (negative, zero)
- Empty activity name
- Invalid date (bad format, nonexistent date)
- Invalid category
- Searching records by activity keyword
- Filtering by category and by date range
- Calculating category totals
- Calculating percentage distribution
- Saving and reloading data (persistence across "restarts")
- Recovering gracefully from a corrupted data file
- Chart generation (smoke test)

### Manual Testing Checklist

- [ ] Add a record with all fields filled → appears in Records table
- [ ] Add a record with empty activity → error message shown, not saved
- [ ] Add a record with duration 0 → error message shown
- [ ] Add a record with an invalid date (e.g. `2026-13-40`) → error shown
- [ ] Edit an existing record → values update correctly in table and charts
- [ ] Delete a record → removed from table, confirmation dialog appears first
- [ ] Search by partial activity name → only matching rows shown
- [ ] Filter by category → only that category's rows shown
- [ ] Filter by date range → only rows within range shown
- [ ] Close and reopen the app → previously added records still present
- [ ] Corrupt `data/time_records.csv` manually → app still starts (resets data, backs up corrupted file)
- [ ] Dashboard summary cards match manually calculated totals
- [ ] Pie chart percentages sum to ~100%
- [ ] Bar chart hours match Analysis tab totals
- [ ] Compare two periods → shows correct hours per category per period

## 12. Future Improvements

- Multi-user profiles / login.
- Weekly/monthly automatic goal tracking and reminders/notifications.
- Export analysis report as PDF.
- Cloud sync or database backend (SQLite) for larger datasets.
- Dark mode / theming.
- Undo/redo for record edits and deletes.

## 13. Viva Questions and Answers

**Q1. Why did you use Pandas instead of plain lists/dictionaries?**
A: Pandas DataFrames make grouping, filtering, and aggregation (totals,
percentages, sums by category/date) much simpler and more efficient than
manual loops, and they convert directly to/from CSV and JSON.

**Q2. Where is NumPy actually used, and why not just use Pandas alone?**
A: NumPy is used in `analysis.py` for the average-daily-hours calculation
(`np.mean`) and for computing the numeric difference between two periods'
category totals as an array subtraction. It's shown explicitly to
demonstrate array-based numerical computation, as required by the spec.

**Q3. How is data persisted, and what happens if the file is corrupted?**
A: Data is stored in `data/time_records.csv` and saved after every add,
edit or delete. On load, `DataManager.load()` wraps the read in a
try/except; if parsing fails (corrupted or malformed file), it renames the
bad file to a `.corrupted_backup` and starts with a fresh, empty DataFrame
instead of crashing.

**Q4. How is input validated?**
A: `validation.py` has one function per field (date, activity name,
category, duration, description) plus a combined `validate_record()`. Each
raises a `ValidationError` with a specific message, which `main.py` catches
and displays via `messagebox.showerror`.

**Q5. Why split the code into separate modules instead of one big file?**
A: Separation of concerns — GUI code (`main.py`) stays independent of
business logic (`analysis.py`, `data_manager.py`, `validation.py`) and
chart rendering (`visualization.py`). This makes each part independently
testable (see `tests/test_app.py`) and easier to maintain or extend.

**Q6. How do you calculate the percentage distribution of time?**
A: `analysis.category_percentages()` sums `duration_minutes` per category
with `groupby`, divides each category's total by the grand total of all
recorded minutes, and multiplies by 100.

**Q7. How does the "compare periods" feature work?**
A: `analysis.compare_periods()` filters the DataFrame into two date ranges,
computes category-hour totals for each independently, aligns both on the
union of categories present (filling missing ones with 0), and subtracts
them using NumPy arrays to get the hour change per category.

**Q8. What exception handling have you implemented?**
A: Try/except blocks around: CSV/JSON parsing (corrupted file recovery),
file save operations (`IOError`), record lookups for edit/delete
(`ValueError` if id not found), user input validation (`ValidationError`),
period comparison, and chart generation (falls back to an on-screen error
label instead of crashing the GUI).

**Q9. Why Tkinter and not a web framework?**
A: The spec requires a Python desktop application with a simple, beginner
-friendly interface; Tkinter ships with Python (no extra install), keeps
the project dependency-light, and is well suited to a B.Tech CSE course
project.

**Q10. How would you extend this to support multiple students?**
A: Add a "student profile" concept — e.g. a login screen that selects/creates
a profile, and store each profile's records in a separate CSV/JSON file
(or an added `student_id` column filtered on load), without changing the
core `DataManager`/`analysis` logic.
