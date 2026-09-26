

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import analysis


def clear_frame(frame):
    """Remove all widgets from a Tkinter frame before drawing a new chart."""
    for widget in frame.winfo_children():
        widget.destroy()


def draw_category_pie_chart(frame, df):
    """Pie/Donut chart: percentage distribution of time by category."""
    clear_frame(frame)
    try:
        percentages = analysis.category_percentages(df)
        fig, ax = plt.subplots(figsize=(5.2, 4.2))

        if percentages.empty:
            ax.text(0.5, 0.5, "No data yet.\nAdd some records first.",
                    ha="center", va="center", fontsize=11)
            ax.axis("off")
        else:
            wedges, texts, autotexts = ax.pie(
                percentages.values,
                labels=percentages.index,
                autopct="%1.1f%%",
                startangle=90,
                wedgeprops=dict(width=0.45),  # donut style
            )
            ax.set_title("Time Distribution by Category")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)
    except Exception as e:
        _show_chart_error(frame, e)


def draw_category_bar_chart(frame, df):
    """Bar chart: total hours spent in each category."""
    clear_frame(frame)
    try:
        totals = analysis.category_totals_hours(df)
        fig, ax = plt.subplots(figsize=(5.2, 4.2))

        if totals.empty:
            ax.text(0.5, 0.5, "No data yet.\nAdd some records first.",
                    ha="center", va="center", fontsize=11)
            ax.axis("off")
        else:
            ax.bar(totals.index, totals.values, color="#4C72B0")
            ax.set_ylabel("Hours")
            ax.set_title("Total Hours per Category")
            ax.tick_params(axis="x", rotation=30)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)
    except Exception as e:
        _show_chart_error(frame, e)


def draw_daily_trend_line_chart(frame, df):
    """Line chart: total hours logged per day (trend over time)."""
    clear_frame(frame)
    try:
        daily = analysis.daily_totals_hours(df)
        fig, ax = plt.subplots(figsize=(5.2, 4.2))

        if daily.empty:
            ax.text(0.5, 0.5, "No data yet.\nAdd some records first.",
                    ha="center", va="center", fontsize=11)
            ax.axis("off")
        else:
            ax.plot(daily.index, daily.values, marker="o", color="#DD8452")
            ax.set_ylabel("Hours")
            ax.set_title("Daily Time Logged (Trend)")
            ax.tick_params(axis="x", rotation=45)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)
    except Exception as e:
        _show_chart_error(frame, e)


def _show_chart_error(frame, error):
    """Fallback UI shown inside the chart frame if chart generation fails."""
    import tkinter as tk
    clear_frame(frame)
    label = tk.Label(
        frame,
        text=f"Could not generate chart:\n{error}",
        fg="red",
        wraplength=350,
        justify="center",
    )
    label.pack(expand=True)
