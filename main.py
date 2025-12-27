import sys
import datetime
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

# Add parent directory to path to import from shift-calendar-generator
sys.path.insert(0, str(Path(__file__).parent.parent / "shift-calendar-generator"))
import generator

app = FastAPI(
    title="Shift Calendar API",
    description="Generate iCalendar feeds for shift schedules",
    version="0.1.0"
)

# Path to the template file in the generator project
TEMPLATE_FILE = str(Path(__file__).parent.parent / "shift-calendar-generator" / "template.csv")

# Mount static files
app.mount("/", StaticFiles(directory=str(Path(__file__).parent / "static"), html=True), name="static")

# Default date range: today to 52 weeks out
def get_default_date_range() -> tuple[datetime.date, datetime.date]:
    today = datetime.date.today()
    future = today + datetime.timedelta(weeks=52)
    return today, future

@app.get("/calendars/all_shifts.ics")
def get_all_shifts():
    """Generate calendar with all 5 shifts"""
    date_from, date_to = get_default_date_range()

    cal = generator.generate_calendar(
        template_file=TEMPLATE_FILE,
        date_from=date_from,
        date_to=date_to,
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

@app.get("/calendars/shift{shift_number}.ics")
def get_shift_calendar(shift_number: int):
    """Generate calendar for a specific shift (1-5)"""
    if shift_number < 1 or shift_number > 5:
        return Response(
            content="Shift number must be between 1 and 5",
            status_code=400
        )

    date_from, date_to = get_default_date_range()

    cal = generator.generate_calendar(
        template_file=TEMPLATE_FILE,
        date_from=date_from,
        date_to=date_to,
        selected_shifts={shift_number}
    )

    return Response(
        content=cal.to_ical(),
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=shift{shift_number}.ics",
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
    )

@app.get("/calendars/shift{shift_numbers}.ics")
def get_custom_calendar(shift_numbers: str):
    """Generate calendar for custom combination of shifts (e.g., '1,3,5')"""
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

    date_from, date_to = get_default_date_range()

    cal = generator.generate_calendar(
        template_file=TEMPLATE_FILE,
        date_from=date_from,
        date_to=date_to,
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
