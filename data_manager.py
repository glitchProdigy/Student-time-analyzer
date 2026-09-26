
import os
import json
import pandas as pd

COLUMNS = ["id", "date", "activity", "category", "duration_minutes", "description"]

DEFAULT_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "time_records.csv")
DEFAULT_JSON_PATH = os.path.join(os.path.dirname(__file__), "data", "time_records.json")


class DataManager:
    """Owns the DataFrame of records and all file I/O."""

    def __init__(self, storage_path: str = DEFAULT_CSV_PATH):
        self.storage_path = storage_path
        self.df = pd.DataFrame(columns=COLUMNS)
        self.load()

    # ---------------------------------------------------------------
    # Loading / Saving
    # ---------------------------------------------------------------
    def load(self):
        """Load records from disk. Handles missing or corrupted files
        by falling back to an empty DataFrame instead of crashing."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        if not os.path.exists(self.storage_path):
            self.df = pd.DataFrame(columns=COLUMNS)
            return

        try:
            if self.storage_path.endswith(".json"):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                self.df = pd.DataFrame(records, columns=COLUMNS)
            else:
                self.df = pd.read_csv(self.storage_path)
                # Make sure every expected column exists even if file was hand-edited
                for col in COLUMNS:
                    if col not in self.df.columns:
                        self.df[col] = None
                self.df = self.df[COLUMNS]
        except (pd.errors.EmptyDataError, json.JSONDecodeError, ValueError, OSError) as e:
            # Corrupted file -> back it up and start fresh instead of losing the app
            backup_path = self.storage_path + ".corrupted_backup"
            try:
                os.replace(self.storage_path, backup_path)
            except OSError:
                pass
            self.df = pd.DataFrame(columns=COLUMNS)
            print(f"Warning: data file was corrupted and has been reset. Details: {e}")

        # Ensure correct dtypes
        if not self.df.empty:
            self.df["id"] = pd.to_numeric(self.df["id"], errors="coerce").fillna(0).astype(int)
            self.df["duration_minutes"] = pd.to_numeric(
                self.df["duration_minutes"], errors="coerce"
            ).fillna(0).astype(int)
            self.df["description"] = self.df["description"].fillna("")

    def save(self):
        """Persist the current DataFrame to disk (CSV or JSON based on path)."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            if self.storage_path.endswith(".json"):
                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump(self.df.to_dict(orient="records"), f, indent=2)
            else:
                self.df.to_csv(self.storage_path, index=False)
        except OSError as e:
            raise IOError(f"Could not save data file: {e}")

    # ---------------------------------------------------------------
    # CRUD operations
    # ---------------------------------------------------------------
    def add_record(self, date, activity, category, duration_minutes, description=""):
        """Add a new record and persist it. Returns the new record's id."""
        new_id = int(self.df["id"].max()) + 1 if not self.df.empty else 1
        new_row = {
            "id": new_id,
            "date": date,
            "activity": activity,
            "category": category,
            "duration_minutes": int(duration_minutes),
            "description": description,
        }
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.save()
        return new_id

    def update_record(self, record_id, date, activity, category, duration_minutes, description=""):
        """Edit an existing record in place by id."""
        idx = self.df.index[self.df["id"] == record_id]
        if len(idx) == 0:
            raise ValueError(f"Record with id {record_id} not found.")
        i = idx[0]
        self.df.loc[i, "date"] = date
        self.df.loc[i, "activity"] = activity
        self.df.loc[i, "category"] = category
        self.df.loc[i, "duration_minutes"] = int(duration_minutes)
        self.df.loc[i, "description"] = description
        self.save()

    def delete_record(self, record_id):
        """Remove a record by id."""
        before = len(self.df)
        self.df = self.df[self.df["id"] != record_id].reset_index(drop=True)
        if len(self.df) == before:
            raise ValueError(f"Record with id {record_id} not found.")
        self.save()

    def get_all(self) -> pd.DataFrame:
        """Return a copy of all records, sorted by date descending."""
        if self.df.empty:
            return self.df.copy()
        return self.df.sort_values(by="date", ascending=False).reset_index(drop=True)

    # ---------------------------------------------------------------
    # Search / Filter
    # ---------------------------------------------------------------
    def search_by_activity(self, keyword: str) -> pd.DataFrame:
        """Case-insensitive substring search on activity name."""
        if self.df.empty or not keyword:
            return self.get_all()
        mask = self.df["activity"].str.contains(keyword, case=False, na=False)
        return self.df[mask].sort_values(by="date", ascending=False).reset_index(drop=True)

    def filter_by_category(self, category: str) -> pd.DataFrame:
        if self.df.empty or not category or category == "All":
            return self.get_all()
        return self.df[self.df["category"] == category].sort_values(
            by="date", ascending=False
        ).reset_index(drop=True)

    def filter_by_date(self, date_str: str) -> pd.DataFrame:
        if self.df.empty or not date_str:
            return self.get_all()
        return self.df[self.df["date"] == date_str].reset_index(drop=True)

    def filter_by_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        if self.df.empty:
            return self.df.copy()
        mask = (self.df["date"] >= start_date) & (self.df["date"] <= end_date)
        return self.df[mask].sort_values(by="date", ascending=False).reset_index(drop=True)
