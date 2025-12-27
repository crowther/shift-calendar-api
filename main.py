import sys
import datetime
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse

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

# Default date range: today to 52 weeks out
def get_default_date_range() -> tuple[datetime.date, datetime.date]:
    today = datetime.date.today()
    future = today + datetime.timedelta(weeks=52)
    return today, future

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Landing page with calendar subscription links"""
    base_url = "http://localhost:8000"  # TODO: Make this configurable

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Shift Calendar Subscriptions</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                line-height: 1.6;
            }}
            h1 {{ color: #333; }}
            .calendar-link {{
                background: #f5f5f5;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }}
            .calendar-link h3 {{ margin-top: 0; }}
            code {{
                background: #e9ecef;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }}
            a {{ color: #007bff; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>Shift Calendar Subscriptions</h1>
        <p>Subscribe to these calendars in your favorite calendar application (Google Calendar, Apple Calendar, Outlook, etc.)</p>

        <div class="calendar-link">
            <h3>All Shifts</h3>
            <p><a href="{base_url}/calendars/all.ics">{base_url}/calendars/all.ics</a></p>
            <p>Includes all 5 shifts combined</p>
        </div>

        <div class="calendar-link">
            <h3>Shift 1</h3>
            <p><a href="{base_url}/calendars/shift1.ics">{base_url}/calendars/shift1.ics</a></p>
        </div>

        <div class="calendar-link">
            <h3>Shift 2</h3>
            <p><a href="{base_url}/calendars/shift2.ics">{base_url}/calendars/shift2.ics</a></p>
        </div>

        <div class="calendar-link">
            <h3>Shift 3</h3>
            <p><a href="{base_url}/calendars/shift3.ics">{base_url}/calendars/shift3.ics</a></p>
        </div>

        <div class="calendar-link">
            <h3>Shift 4</h3>
            <p><a href="{base_url}/calendars/shift4.ics">{base_url}/calendars/shift4.ics</a></p>
        </div>

        <div class="calendar-link">
            <h3>Shift 5</h3>
            <p><a href="{base_url}/calendars/shift5.ics">{base_url}/calendars/shift5.ics</a></p>
        </div>

        <h2>How to Subscribe</h2>
        <ul>
            <li><strong>Google Calendar:</strong> Settings → Add calendar → From URL</li>
            <li><strong>Apple Calendar:</strong> File → New Calendar Subscription</li>
            <li><strong>Outlook:</strong> Add calendar → Subscribe from web</li>
        </ul>
    </body>
    </html>
    """
    return html

@app.get("/calendars/all.ics")
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
            "Content-Disposition": "attachment; filename=all-shifts.ics",
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

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
