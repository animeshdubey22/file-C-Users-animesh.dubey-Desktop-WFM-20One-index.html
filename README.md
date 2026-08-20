# WFM-One | Enterprise Workforce Management System

An end-to-end, full-stack Workforce Management (WFM) Enterprise platform built for multi-brand contact centers. Features intraday scheduling, forecasting, shrinkage modeling, real-time adherence tracking, 2-stage approval workflows, and multi-tier scheduling consoles.

---

## Quick Start

### 1. Launch with Batch Script
Double-click start_server.bat in the project root directory. It will automatically start the FastAPI/Uvicorn server and open your default browser to:
**http://127.0.0.1:8000**

### 2. Manual Command Line Start
`powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
`

---

## Default Roles & Login Credentials

| Role | Name | Email | Password |
| :--- | :--- | :--- | :--- |
| **WFM Admin** | Animesh Dubey | dmin@houseofbrands.com | dmin |
| **WFM Admin (Corp)** | Animesh Dubey | nimesh.dubey@intelegencia.com | dmin |
| **Team Leader** | Marcus Brody | 	l@houseofbrands.com | leader |
| **Agent** | John Smith | gent@houseofbrands.com | gent |

* **Admin Registration Secret Key**: WFMONE2026 *(Used when registering new WFM analyst/manager/admin accounts)*

---

## Theme Switcher (Dark & Light Themes)

Switch seamlessly between **Dark Slate Theme** and **Clean White / Light Theme**:
* **Floating Pill**: Top-right corner of the window (always visible anywhere).
* **Login & Registration Cards**: Top-right button beside the W1 logo.
* **Sidebar Menu**: Quick toggle below the brand header.
* **Top Navigation Bar**: Located beside the System Time.
* Your theme choice is automatically persisted across browser reloads via localStorage.

---

## Key Features & Modules

### 1. WFM Master Schedule Console
* **Multi-Tier Views**: Switch between **Daily**, **Weekly**, and **Monthly** schedules.
* **Continuous Date Navigation**: Jump between days/weeks/months with < Prev and Next > buttons or pick any custom date.
* **Interactive Edit Schedule Drawer**:
  - **Change Shift**: Modify shift start and end times with audit logging.
  - **Slide Shift**: Quick slide preset buttons (-1 Hr, -30m, +30m, +1 Hr) that adjust shift hours in real-time.
  - **Week Off**: Toggle between off-duty rotation and standard working shifts.
  - **Add Leave**: Schedule PTO, Sick Leave, Emergency Leave, or Unplanned Leave.
  - **Add Activity**: Allocate Coaching, Training, Meeting, Break, or Lunch blocks.

### 2. Team Leader (TL) Hub
* **7-Day Staffing & Coverage Deck**: Responsive visual cards showing coverage health %, multi-segment distribution bars, and breakdown metrics (Working, Off, Leave, Absent, Activity).
* **Team View vs. Agent Drilldown**: Toggle between team-wide matrix and dedicated single-agent rosters.
* **Direct-to-WFM Quick Action Modals**: Submit team leave, activity, and week-off requests directly to Stage 2 WFM approval queue with instant agent notifications.

### 3. Agent Portal
* **Daily, Weekly & Monthly Personal Schedule**: Full intraday timeline breakdown with activity blocks.
* **Request Tracker**: Real-time 2-stage approval workflow tracking (Stage 1: TL Review -> Stage 2: WFM Review -> Applied).

### 4. Enterprise WFM Suite
* **Command Center**: Real-time SLA monitoring, live ASA, call arrival vs. scheduled capacity, and adherence health.
* **Shrinkage Studio**: Configurable in-office and out-of-office shrinkage parameters.
* **Agent Directory**: Full agent roster, skill proficiencies, supervisor mapping, and bulk sync.
* **HOOP Planner**: Operating hours and channel schedules.
* **Forecast Modeler**: Volume & AHT forecasting across Voice, Chat, and Email channels.
* **Staffing Solver**: Multi-channel Erlang C staffing calculations and required headcount solver.
* **Live Adherence & Exceptions**: Real-time state adherence, AUX tracking, and out-of-adherence alerts.
* **Reporting Console**: SLA compliance and agent adherence exportable reports (CSV download).

---

## Project Structure

`
WFM One/
├── index.html          # Main single-page application entry point
├── styles.css          # Design tokens, light/dark themes, glassmorphic styles
├── app.js              # Core UI engine, routing, math solvers, and event listeners
├── main.py             # FastAPI backend server, REST API routes, SQLite data persistence
├── wfm_one.db          # SQLite relational database (schedules, overrides, audit, requests)
├── start_server.bat    # Windows batch launcher (starts server + opens browser)
└── README.md           # Documentation and user guide
`
