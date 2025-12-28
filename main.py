import sys
import os
import datetime
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response, Query
from fastapi.staticfiles import StaticFiles

# Add generator module to path
generator_path = os.getenv("GENERATOR_PATH", str(Path(__file__).parent.parent / "shift-calendar-generator"))
sys.path.insert(0, generator_path)
import generator

# Path to the template file
TEMPLATE_FILE = os.getenv("TEMPLATE_FILE", str(Path(__file__).parent.parent / "shift-calendar-generator" / "template.csv"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.exists(TEMPLATE_FILE):
        raise FileNotFoundError(f"Template file not found: {TEMPLATE_FILE}")
    yield

app = FastAPI(
    title="Shift Calendar API",
    description="Generate iCalendar feeds for shift schedules",
    version="0.1.0",
    lifespan=lifespan
)

# Parse date from string (YYYY-MM-DD format)
def parse_date(date_str: str) -> datetime.date:
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

# Default date range: 1 year back to 1 year forward
def get_default_date_range() -> tuple[datetime.date, datetime.date]:
    today = datetime.date.today()
    date_from = today - datetime.timedelta(days=365)
    date_to = today + datetime.timedelta(days=365)
    return date_from, date_to

def get_date_range(date_from_str: Optional[str], date_to_str: Optional[str]) -> tuple[datetime.date, datetime.date]:
    # Use provided dates or default range
    if date_from_str and date_to_str:
        try:
            date_from = parse_date(date_from_str)
            date_to = parse_date(date_to_str)
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

        if date_to < date_from:
            raise ValueError("date_to must be greater than or equal to date_from")
    else:
        date_from, date_to = get_default_date_range()
    return date_from, date_to   

@app.get("/calendars/all_shifts.ics")
def get_all_shifts(
    date_from_str: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)", alias="date_from"),
    date_to_str: Optional[str] = Query(None, description="End date (YYYY-MM-DD)", alias="date_to")
):
    """Generate calendar with all 5 shifts"""
    try:
        date_from, date_to = get_date_range(date_from_str, date_to_str)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        cal = generator.generate_calendar(
            template_file=TEMPLATE_FILE,
            date_from=date_from,
            date_to=date_to,
            selected_shifts=None  # All shifts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate calendar: {str(e)}")

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
    date_from_str: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)", alias="date_from"),
    date_to_str: Optional[str] = Query(None, description="End date (YYYY-MM-DD)", alias="date_to")
):
    """Generate calendar for one or more shifts (e.g., '1' or '1,3,5')"""
    try:
        selected_shifts = {int(s.strip()) for s in shift_numbers.split(',')}

        # Validate shift numbers
        if not selected_shifts:
            raise HTTPException(
                status_code=400,
                detail="At least one shift must be specified"
            )

        if any(shift < 1 or shift > 5 for shift in selected_shifts):
            raise HTTPException(
                status_code=400,
                detail="All shift numbers must be between 1 and 5"
            )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid shift numbers format. Use comma-separated integers (e.g., '1,3,5')"
        )

    try:
        date_from, date_to = get_date_range(date_from_str, date_to_str)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        cal = generator.generate_calendar(
            template_file=TEMPLATE_FILE,
            date_from=date_from,
            date_to=date_to,
            selected_shifts=selected_shifts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate calendar: {str(e)}")

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
