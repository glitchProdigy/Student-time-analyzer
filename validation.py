"""
validation.py
--------------
Input validation utilities for the Student Time-Use Analyzer.

This module has NO dependency on Tkinter or file handling so it can be
tested in isolation (see tests/test_app.py).
"""

from datetime import datetime

# The fixed set of categories allowed by the project spec
VALID_CATEGORIES = ["Study", "Travel", "Entertainment", "Sleep", "Personal", "Other"]

# Reasonable upper bound for a single activity's duration (24 hours in minutes)
MAX_DURATION_MINUTES = 24 * 60


class ValidationError(Exception):
    """Raised when user input fails a validation rule.
    A single, simple exception type keeps error handling easy to follow
    for a B.Tech-level project, while still giving a clear message.
    """
    pass


def validate_activity_name(name: str) -> str:
    """Ensure activity name is not empty/whitespace. Returns the cleaned name."""
    if name is None:
        raise ValidationError("Activity name is required.")
    name = name.strip()
    if len(name) == 0:
        raise ValidationError("Activity name cannot be empty.")
    if len(name) > 100:
        raise ValidationError("Activity name is too long (max 100 characters).")
    return name


def validate_category(category: str) -> str:
    """Ensure category is one of the fixed allowed categories."""
    if category is None or category.strip() == "":
        raise ValidationError("Category is required.")
    category = category.strip().title()
    if category not in VALID_CATEGORIES:
        raise ValidationError(
            f"Invalid category '{category}'. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    return category


def validate_date(date_str: str) -> str:
    """Ensure date is a valid calendar date in YYYY-MM-DD format.
    Returns the normalised date string.
    """
    if date_str is None or date_str.strip() == "":
        raise ValidationError("Date is required.")
    date_str = date_str.strip()
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("Invalid date. Please use YYYY-MM-DD format (e.g. 2026-09-26).")

    if parsed.date() > datetime.now().date():
        raise ValidationError("Date cannot be in the future.")
    return parsed.strftime("%Y-%m-%d")


def validate_duration(hours_str: str, minutes_str: str) -> int:
    """Combine hours + minutes fields into total minutes, validating both.
    Returns total duration in minutes as a positive int.
    """
    try:
        hours = int(hours_str) if str(hours_str).strip() != "" else 0
        minutes = int(minutes_str) if str(minutes_str).strip() != "" else 0
    except ValueError:
        raise ValidationError("Duration (hours/minutes) must be whole numbers.")

    if hours < 0 or minutes < 0:
        raise ValidationError("Duration cannot be negative.")
    if minutes >= 60:
        raise ValidationError("Minutes must be between 0 and 59.")

    total_minutes = hours * 60 + minutes
    if total_minutes <= 0:
        raise ValidationError("Duration must be greater than 0.")
    if total_minutes > MAX_DURATION_MINUTES:
        raise ValidationError("Duration cannot exceed 24 hours (1440 minutes) for a single activity.")

    return total_minutes


def validate_description(description: str) -> str:
    """Description is optional; just trim and cap length."""
    if description is None:
        return ""
    description = description.strip()
    if len(description) > 300:
        raise ValidationError("Description is too long (max 300 characters).")
    return description


def validate_record(date_str, activity, category, hours_str, minutes_str, description=""):
    """Run all field validations together and return a clean dict.
    Raises ValidationError on the FIRST failing field, with a clear message.
    """
    clean_date = validate_date(date_str)
    clean_activity = validate_activity_name(activity)
    clean_category = validate_category(category)
    clean_duration = validate_duration(hours_str, minutes_str)
    clean_description = validate_description(description)

    return {
        "date": clean_date,
        "activity": clean_activity,
        "category": clean_category,
        "duration_minutes": clean_duration,
        "description": clean_description,
    }
