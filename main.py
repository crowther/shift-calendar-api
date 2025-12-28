import sys
import os
import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Response, Query
from fastapi.staticfiles import StaticFiles

# Add generator module to path
generator_path = os.getenv("GENERATOR_PATH", str(Path(__file__).parent.parent / "shift-calendar-generator"))
sys.path.insert(0, generator_path)
import generator

app = FastAPI(
    title="Shift Calendar API",
    description="Generate iCalendar feeds for shift schedules",
    version="0.1.0"
)

# Path to the template file
TEMPLATE_FILE = os.getenv("TEMPLATE_FILE", str(Path(__file__).parent.parent / "shift-calendar-generator" / "template.csv"))

# Parse date from string (YYYY-MM-DD format)
def parse_date(date_str: str) -> datetime.date:
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

# Default date range: 1 year back to 1 year forward
def get_default_date_range() -> tuple[datetime.date, datetime.date]:
    today = datetime.date.today()
    past = today - datetime.timedelta(days=365)
    future = today + datetime.timedelta(days=365)
    return past, future

@app.get("/calendars/all_shifts.ics")
def get_all_shifts(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Generate calendar with all 5 shifts"""
    # Use provided dates or default range
    if date_from and date_to:
        try:
            start_date = parse_date(date_from)
            end_date = parse_date(date_to)
        except ValueError:
            return Response(
                content="Invalid date format. Use YYYY-MM-DD",
                status_code=400
            )
    else:
        start_date, end_date = get_default_date_range()

    cal = generator.generate_calendar(
        template_file=TEMPLATE_FILE,
        date_from=start_date,
        date_to=end_date,
        selected_shifts=None  # All shifts
    )

    return Response(
        content=cal.to_ical(),
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=all_shifts.ics",
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
    )

@app.get("/calendars/shift{shift_numbers}.ics")
def get_shift_calendar(
    shift_numbers: str,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Generate calendar for one or more shifts (e.g., '1' or '1,3,5')"""
    try:
        selected_shifts = {int(s.strip()) for s in shift_numbers.split(',')}

        # Validate shift numbers
        if not selected_shifts:
            return Response(
                content="At least one shift must be specified",
                status_code=400
            )

        if any(shift < 1 or shift > 5 for shift in selected_shifts):
            return Response(
                content="All shift numbers must be between 1 and 5",
                status_code=400
            )

    except ValueError:
        return Response(
            content="Invalid shift numbers format. Use comma-separated integers (e.g., '1,3,5')",
            status_code=400
        )

    # Use provided dates or default range
    if date_from and date_to:
        try:
            start_date = parse_date(date_from)
            end_date = parse_date(date_to)
        except ValueError:
            return Response(
                content="Invalid date format. Use YYYY-MM-DD",
                status_code=400
            )
    else:
        start_date, end_date = get_default_date_range()

    cal = generator.generate_calendar(
        template_file=TEMPLATE_FILE,
        date_from=start_date,
        date_to=end_date,
        selected_shifts=selected_shifts
    )

    filename = f"shift{shift_numbers}.ics"

    return Response(
        content=cal.to_ical(),
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
    )

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Mount static files - must be last so it doesn't override API routes
app.mount("/", StaticFiles(directory=str(Path(__file__).parent / "static"), html=True), name="static")
