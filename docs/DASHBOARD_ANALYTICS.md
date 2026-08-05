# Dashboard analytics reference

This document describes every analytics value displayed on the dashboard, its
source records, its calculation, its filters, and its time window.

The application has two dashboard experiences:

1. **Owner Executive Command Center** — the dashboard shown to owners in the
   current UI. It uses `GET /api/v1/dashboard/command-center`.
2. **Recruiter performance cockpit** — the dashboard shown to recruiters. It
   uses `GET /api/v1/dashboard/recruiter-command`.

`GET /api/v1/dashboard/analytics` still has an owner-shaped response for
backward compatibility, but the owner UI does not render it. Owners use the
Command Center instead.

## Quick reference

| Concern | Owner Command Center | Recruiter dashboard |
| --- | --- | --- |
| API | `GET /api/v1/dashboard/command-center` | `GET /api/v1/dashboard/recruiter-command` |
| Access | Owner role only | Owner or recruiter; UI uses it for recruiters |
| Default requested range | Last 30 calendar days through today | Last 30 calendar days through today |
| Default date source | Office date in `OFFICE_TIMEZONE` (default `Asia/Dubai`) | Browser-supplied dates; service uses server `date.today()` for most “today” values |
| Date-time query bounds | Start/end of day in office timezone | Start/end of day in UTC where the query is time-bounded |
| Live refresh | WebSocket event, visibility return, or filter/range change | Same |
| Main data domain | Jobs, clients, applications, offers, placements, recruiter activity, attendance | Recruiter-owned candidates, submissions, assigned jobs, interviews, offers, placements |

## Core records and terminology

| Term | Record / fields used |
| --- | --- |
| Candidate | `candidates`: `created_at`, `created_by`, `candidate_status` |
| Submission / application | `candidate_applications`: `submitted_at`, `submitted_by`, `owner_status`, `in_pipeline`, `current_stage`, `applied_date` |
| Job | `job_requirements`: `status`, `assigned_to`, `open_positions`, `priority`, `created_at`, client, department, location |
| Pipeline stage | `pipeline_stages`: `name`, `order_no`; current stage is `candidate_applications.current_stage` |
| Pipeline activity | `application_stage_history`: `created_at`, `moved_by`, stage and application |
| Interview | `interviews`: `scheduled_datetime`, `status`, feedback |
| Offer | `offers`: `offer_date`, `joining_date`, `status` |
| Placement | `placements`: `joined_date`, `revenue_generated` |
| Attendance | `attendance_records`: office `date`, `check_in`, `check_out` |
| Client activity | `client_activities.created_at` |

An **approved pipeline candidate** is an application where
`in_pipeline = true` and `owner_status = "approved"`.

## Date, time, and filter semantics

### Default dashboard date range

The frontend initializes the range as:

- `end`: the browser’s local calendar date today.
- `start`: 30 local calendar days before `end`.

It sends ISO date-only strings (`YYYY-MM-DD`) to the selected dashboard API.
The displayed header shows those same inclusive dates.

### Owner Command Center time model

The Command Center uses `OFFICE_TIMEZONE`, defaulting to `Asia/Dubai`.

- `start_dt`: selected start date at `00:00:00` office time.
- `end_dt`: selected end date at `23:59:59.999999` office time.
- “Today”, yesterday, calendar month, and week are calculated using the office
  date.
- A week is **Sunday through Saturday**.
- The previous comparison range has the same inclusive duration as the selected
  range and ends on the day before it starts.

The dashboard’s `start`/`end` filter is not a universal historical filter.
It applies to measures that explicitly use it, such as rates, recruiter
placements, scheduled interviews, activity feed dates, and some trend filters.
Current-state measures intentionally ignore it; for example, open jobs,
assigned workload, and the current funnel.

### Recruiter dashboard time model

The recruiter cockpit uses the same office-timezone date boundaries and
selected/prior-period comparisons as the Command Center. Current-state measures
such as the funnel, pending actions, and open jobs intentionally ignore the
historical range. Its trend always shows six calendar months.

The legacy `/analytics` recruiter response still uses UTC/server-calendar
semantics and remains available for integrations; the current recruiter UI
does not request it.

### Command Center filters

The Command Center exposes recruiter, client, department, job status, and
location filters.

These filters apply through `job_requirements`:

- **Recruiter** means the user assigned to the job (`job_requirements.assigned_to`).
- **Client** means the job’s client.
- **Department**, **job status**, and **location** mean the matching job field.

Consequences:

- Recruiter activity stage moves are scoped by the job’s assignee, not solely
  by the person who performed the move.
- Candidate uploads are scoped by uploader for a recruiter filter. When any
  job-oriented filter is selected, uploads must also have an application on a
  matching job.
- Attendance is not job-linked. It honors the recruiter filter but deliberately
  ignores client, department, job-status, and location filters.
- Active-client count only honors the client filter.
- Client health initially loads every client, then applies the client filter;
  other job filters affect each client card’s job-derived values.

## Owner Executive Command Center

### Executive overview

| Card | Computation | Date/filter behavior |
| --- | --- | --- |
| Active Open Jobs | Count of `job_requirements` where `status = "open"` | Current state; job filters apply |
| Active Clients | Count of `clients` where `status = "active"` | Current state; client filter applies |
| Total Candidates in Pipeline | Count of approved in-pipeline applications | Current state; job filters apply |
| Placements This Month | Count of placements whose `joined_date` is from the first office-date day of this month through office today | Job filters apply. Delta compares with the preceding calendar month |
| Offer Acceptance Rate | `accepted offers / all offers × 100`, grouped by offer status | Uses `offer_date` in selected range. Delta compares the immediately preceding range of equal length |
| Average Time to Hire | Average of `placement.joined_date - application.applied_date`; falls back to `submitted_at` date when `applied_date` is null | Joined date must be inside selected range. Delta compares with the immediately preceding equal-length range |
| Recruiters At/Above Avg Load | `active recruiters with assigned open jobs >= team average / active recruiters × 100` | Current workload; values use active recruiters and job filters |
| Candidate-to-Placement Conversion | `placements / submissions × 100` | Placements use `joined_date`; submissions use `submitted_at`; both use selected range. Delta compares with preceding equal-length range |

The placements card includes a six-month monthly placements sparkline. A delta
of `100%` means the previous value was zero and the current value is positive.
No rate is returned when its denominator is zero.

### Business trend

The trend chart has fixed rolling bucket counts, independent of the selected
dashboard range:

| Selected grain | Buckets shown | Event date |
| --- | ---: | --- |
| Weekly | 12 | Sunday-start week containing the event |
| Monthly | 6 | Calendar month |
| Quarterly | 8 | Calendar quarter |
| Yearly | 5 | Calendar year |

Series definitions:

- **Applications**: `candidate_applications.submitted_at`.
- **Interviews**: `interviews.scheduled_datetime`; this counts scheduled event
  timestamps, regardless of interview status.
- **Offers**: `offers.offer_date`.
- **Placements**: `placements.joined_date`.

All series are job-filtered and include zero-value buckets so missing activity
appears as zero rather than disappearing.

### Hiring funnel

The funnel is a current snapshot of approved in-pipeline applications in these
ordered stages: **Applied, Shortlisted, Interview, Offer, Joined**.

For every stage after Applied:

```text
conversion_pct = current stage count / prior stage count × 100
dropoff_pct = 100 - conversion_pct
```

The largest positive drop-off is highlighted. This is a comparison of current
stage populations, not a cohort conversion analysis: candidates can move,
leave, or enter stages at different times.

### Recruiter performance and workload

Only recruiters and users marked active appear.

| Field | Computation |
| --- | --- |
| Placements | Joined placements in selected range, scoped to jobs assigned to that recruiter |
| Active candidates | Approved in-pipeline applications on that recruiter’s assigned jobs |
| Interviews | `scheduled` interviews in selected range on assigned jobs |
| Offer acceptance | Accepted offers divided by all offers, based on offer date in selected range |
| Average time to hire | Same placement-to-application date calculation as the executive KPI, scoped to assigned jobs |
| Assigned jobs | Current count of open jobs assigned to recruiter |
| Productivity score | Relative score among visible active recruiters: 60% placements, 20% scheduled interviews, 15% offer acceptance, 5% inverse time to hire |

Each productivity input is min/max normalized across the visible recruiter
cohort. A score is therefore comparative, not an absolute percentage.

Workload labels use the average assigned open-job count among visible
recruiters:

- **Overloaded**: at least 8 jobs and at least 1.5× the average.
- **Heavy**: at least 1.2× the average.
- **Light**: at most `max(50% of average, 1)`.
- **Balanced**: all remaining cases.

The workload insight is rule-based. It recommends redistribution only when an
overloaded recruiter exists and another recruiter has two or fewer jobs.

### Client health

Each client card includes:

| Field | Computation |
| --- | --- |
| Open positions | Sum of `open_positions` on open jobs |
| Placements | All placements with joining date from 2000-01-01 through office today |
| Candidates in pipeline | Approved in-pipeline applications |
| Average hiring time | Average time to hire for placements in selected range |
| Jobs pending too long | Open jobs created at least 45 days ago |
| Last activity | Latest of job creation, placement joining date, application submission timestamp, or client-activity timestamp |

Client badges:

- **Inactive**: client status is not `active`.
- **Needs Attention**: active client has a pending-too-long job, no recorded
  activity, or last activity more than 30 days ago.
- **Healthy**: active client that does not meet either condition above.

### Open job health

The table includes jobs currently `open` or `on_hold`.

| Field | Computation |
| --- | --- |
| Days open | Non-negative difference between office today and job `created_at` date |
| Candidates | All applications with `in_pipeline = true` for the job; owner approval is not required for this column |
| Current stage | The stage with the highest count among approved in-pipeline applications; ties depend on query result order |
| Healthy | Default classification |
| Urgent | High/urgent priority, or open at least 30 days |
| Overdue | Open at least 45 days; also sets the SLA flag |
| Frozen | Job status is `on_hold` |

The job-health counts summarize the displayed classification. Rows are ordered
with SLA-exceeded jobs first, then by most days open.

### Candidate pipeline summary

“Today” and “yesterday” use office-day boundaries.

| Card | Computation |
| --- | --- |
| New Candidates Today | Distinct candidates created today that have an application on a matching job |
| Interviews Today | Interviews with `status = "scheduled"` and scheduled timestamp today |
| Offers Pending | Offers with `status = "pending"` |
| Expected Joins This Week | Offers where the application’s current stage is `Offer` and `joining_date` is Sunday–Saturday of the current office week |
| Rejected Today | Distinct candidates created today with `candidate_status = "rejected"` and a matching application |
| Candidates On Hold | In-pipeline applications whose current stage is `On Hold` |

New candidates, interviews, and rejected candidates show a numeric delta versus
the prior office day. The remaining cards are current counts.

### Recruiter activity feed

The preview requests five events; **View all** requests up to 500. Both are
sorted newest first and contain only database-backed recruiter actions:

| Type | Source and inclusion rule |
| --- | --- |
| Candidate uploaded | Candidate `created_at`; `created_by` must match a recruiter user ID, email, or full name |
| Checked in | Active recruiter’s `attendance_records.check_in` |
| Checked out | Active recruiter’s `attendance_records.check_out` |
| Pipeline stage move | `application_stage_history.created_at`, where `moved_by` is a recruiter |

Every feed event must be in the selected office-timezone date range and cannot
have a timestamp in the future. The modal additionally filters the retrieved
events into browser-local **day**, **Sunday–Saturday week**, or **month**
periods. When open, the modal refetches after dashboard filters, selected dates,
or live refresh key changes.

### Alerts and action center

Alerts are generated only when their count is positive:

| Alert | Trigger |
| --- | --- |
| Jobs open more than SLA | Number of displayed jobs classified overdue |
| Offers pending approval | Pending offer count |
| Cancelled, no-show, or on-hold interviews | Interview status is `cancelled`, `no_show`, or `on_hold` |
| Recruiters inactive today | Active recruiter appears in leaderboard but has no check-in for office today |
| Jobs without recruiter assigned | Open jobs where `assigned_to` is null |
| Expected joins this week | Same Offer-stage/Sunday–Saturday calculation as pipeline summary |

The feedback alert is intentionally not part of the action center.

### Command Center response and refresh

The response includes executive KPIs, trend, funnel, recruiter leaderboard and
workload, client health, job health, pipeline summary, activity feed, alerts,
and filter options. It is assembled on every request; it does not use seeded,
scheduled, or synthetic dashboard records.

The owner UI refreshes when:

- a Command Center filter or dashboard date range changes;
- the owner dashboard receives a WebSocket dashboard event;
- the browser tab becomes visible again.

Dashboard event producers include candidate upload, client changes, placement
or job changes, and attendance check-in/check-out. The owner refresh is
debounced by 800 ms; the Command Center request is then debounced by 150 ms.

## Recruiter dashboard

Recruiters are restricted to jobs where `job_requirements.assigned_to` is their
user ID. Candidate ownership uses `created_by` matching their user ID, email,
or full name. Submission ownership uses `submitted_by = current_user.id`.

The current recruiter UI is an action-oriented performance cockpit. Competition
metrics use the same job-assignee attribution and productivity formula as the
owner Command Center, ensuring that a recruiter sees the same score and rank
that the owner sees. Submission quality and pending owner-review actions use
`submitted_by`, because those measure the recruiter's own submissions.

The cockpit includes:

- today's interviews, pending reviews/offers, expected joins, and stale
  pipeline candidates;
- period KPIs for placements, conversion, offer acceptance, time to hire,
  submission quality, active pipeline, and open assigned jobs;
- personal rank and score versus the team median, plus a compact leaderboard;
- recruiter-scoped hiring funnel and highest drop-off insight;
- prioritized feedback, stale-candidate, aging-offer, review, job-risk, and
  joining actions;
- recruiter-scoped at-risk jobs and a six-month activity trend.

Raw uploads, attendance, and assigned-job volume do not contribute directly to
rank. The endpoint uses live database aggregates and does not read the
`recruiter_metrics` table.

### Recruiter KPI cards

| Card | Computation |
| --- | --- |
| My Active Jobs | Current count of all jobs assigned to recruiter; label says active but the query does not filter by job status |
| My Candidates | All candidates whose `created_by` matches recruiter identity keys |
| Interviews Today | UI count of the “Today’s interviews” table; any interview scheduled in the current UTC day, regardless of status |
| Offers Sent | Offers on assigned jobs whose status is pending or accepted |
| Placements | All placements on assigned jobs |

The analytics response also provides these values for integrations and legacy
clients:

- pending/approved/rejected submissions from applications submitted by the
  recruiter on assigned jobs;
- clients assigned, distinct client count across assigned jobs;
- assigned open jobs and closed/filled jobs;
- approved in-pipeline count;
- monthly placements from the first server-calendar day of the current month;
- candidate status aliases and owner-shaped compatibility fields.

### Recruiter charts

| Chart | Computation |
| --- | --- |
| My candidates by stage | Approved in-pipeline applications on assigned jobs, grouped by board stage |
| Candidate status | Recruiter-created candidates grouped as Active, Inactive, Pending, and Rejected |
| Candidate uploads monthly | Recruiter-created candidates by `created_at` month for rolling six server-calendar months |
| Placements monthly | Placements on assigned jobs by `joined_date` month for rolling six server-calendar months |
| Interviews vs offers | Current count of scheduled interviews, pending/accepted offers, and placements on assigned jobs |
| Recruiter activity heatmap | Submissions (`submitted_at`) grouped by UTC weekday (Monday=0) and UTC hour, within selected range |
| Client placements | Top eight client placement counts on assigned jobs |

### Recruiter tables and lists

| UI item | Source / behavior |
| --- | --- |
| My upcoming interviews | Scheduled or completed interviews from today through the next 14 UTC calendar days; first 14 returned, UI shows first 4 |
| My tasks | Recruiter’s own submissions on assigned jobs that remain `pending_review`; first 8 |
| Recent activity | Merged timeline of recruiter-created candidates, owner application decisions, placements, closed jobs, and no client-create records; newest 12, UI shows 5 |
| Recent placements | Most recent joined placements on assigned jobs; first 8 |
| Recently uploaded | Most recent recruiter-created candidates; first 8 |
| Today’s interviews | Any interview scheduled during current UTC day on assigned jobs; first 10 |
| Recent feedback | Most recent non-empty interview feedback on assigned jobs, ordered by scheduled timestamp; first 6 |

These legacy lists remain available from `/analytics`, but the current
recruiter cockpit no longer renders that generic shared response.

## Legacy owner analytics and recruiter-performance API

### Legacy owner analytics response

`GET /api/v1/dashboard/analytics` returns an owner response for compatibility.
The current owner UI does not render it.

Its total candidate, client, recruiter, job, submission, revenue, and placement
KPIs are global current-state values. Its average time to hire is average
`joined_date - submitted_at date` for all placements with both fields.

Legacy owner charts include:

- approved in-pipeline board-stage counts;
- candidate status counts;
- top eight recruiters by placement count through assigned jobs;
- top eight clients by placement count;
- six-month candidate uploads and placements;
- submission activity heatmap for the requested date range.

The legacy owner lists include recent placements, recent mixed activity,
pending owner approvals, today’s interviews, and upcoming interviews. It does
not provide recent candidates or recent feedback in the owner response.

### Recruiter performance API

`GET /api/v1/dashboard/recruiter-performance` is owner-only and supports:

- `period=monthly`: first day of current server month through today.
- `period=till_date`: all records through today.
- `industry`: exact `clients.industry` match.

It considers active recruiter/user pairs and attributes work by
`candidate_applications.submitted_by`.

| Field | Computation |
| --- | --- |
| Positions closed | Placement count, based on `joined_date` |
| Submissions | Applications with `submitted_at` in period |
| Approved submissions | Period submissions where owner status is approved |
| Interviews | Interview scheduled timestamps in period |
| Offers | Offer dates in period |
| Accepted offers | Period offers with status accepted |
| Conversion rate | Placements / submissions × 100 |
| Submission quality | Approved submissions / submissions × 100 |
| Offer acceptance | Accepted offers / offers × 100 |
| Average time to hire | Joined date minus application date, falling back to submission date |
| Average response days | First interview scheduled date minus submission date |
| Monthly placements | Rolling six server-calendar months |

Its productivity score is normalized within the returned recruiter cohort:
35% placements, 25% interviews, 15% submission quality, 15% offer acceptance,
and 10% inverse average response time. It is distinct from the Command Center
leaderboard score.

## Supporting endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/dashboard/notifications` | Returns the recent-activity timeline, limited to 12 by default (maximum 50); `unread_count` equals returned item count |
| `GET /api/v1/dashboard/stats` | Legacy compact projection of `/analytics` KPIs and pipeline stages |
| `GET /api/v1/dashboard/ws?token=...` | Authenticated WebSocket used to request client refreshes after dashboard events |

## Interpretation and data-quality notes

- Counts are records, not always unique candidates. A candidate can have more
  than one application; the pipeline summary explicitly uses distinct
  candidates only for new/rejected candidate cards.
- Placement is treated as a joined placement. Values based on `joined_date`
  exclude rows with no joining date.
- Candidate status and application owner status are separate concepts. A
  candidate can have a status independently of an application’s owner-review
  status.
- “Recent” lists are limited and are not historical reports.
- The Command Center trend and most legacy current-state metrics should not be
  interpreted as restricted to the dashboard header date range.
- Browser-local date display can differ from office-timezone inclusion for an
  event near midnight. The activity-feed API uses office-timezone boundaries;
  the View all period selector uses browser-local calendar boundaries.
- Productivity, workload, health, urgency, and alert classifications are
  operational heuristics implemented in code. They are not predictive models.
