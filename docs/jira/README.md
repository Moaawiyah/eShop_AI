# Jira Setup and Backlog Import (SHOP-009)

How to create the `ESHOP` Jira project and import the backlog. The
conventions behind it are in [roadmap section 10](../ROADMAP.md). The owner
runs every step manually in the Jira Cloud web UI. No API, MCP server or
plugin is used.

| Setting | Value |
|---|---|
| Project name | `eShop_AI` |
| Project key | `ESHOP` (Jira generates `ESHOP-1`, `ESHOP-2`, …) |
| Project type | Company-managed software project, Kanban template |
| Plan | Jira Free |
| Permanent task IDs | Roadmap IDs `SHOP-NNN`, kept in the summary and the `Roadmap ID` field |
| Initial import | [`backlog.csv`](backlog.csv): M0–M2, 32 tasks |
| Key mapping | [`issue-map.csv`](issue-map.csv): roadmap ID → Jira key |

Jira's menu labels change from time to time. If a label below differs,
use Jira's search bar or the matching item under **Settings (⚙)**.

## 1. Create the project

1. **Projects → Create project → Software development → Kanban → Use template.**
2. Choose **Company-managed**, not team-managed.
3. Name: `eShop_AI`. Open **Advanced** or **Key** and set the key to `ESHOP`.
4. Select **Create project**.

## 2. Configure the workflow

The required statuses are To Do, In Progress, In Review, Done and Blocked
(`CONTRIBUTING.md` section 1).

1. **Project settings → Workflows**, then select the edit (pencil) icon of
   the project workflow.
2. Add the statuses that are missing. To Do and Blocked go in the To Do
   category, In Progress and In Review in In Progress, and Done in Done.
3. For each status, enable **Allow all statuses to transition to this one**.
4. Remove the template statuses that are not on the list (for example
   Backlog or Selected for Development) only when no issue uses them.
5. Select **Update workflow** (or **Publish**).
6. **Board → Board settings → Columns:** create one column per status in
   the order above, and leave no status unmapped.

## 3. Create the custom field, versions and time tracking

1. **Settings (⚙) → Issues → Custom fields → Create custom field → Short
   text.** Name it `Roadmap ID`, and add it to the screens of the `ESHOP`
   project (the default and Kanban screens).
2. **Project → Releases** (or **Versions**) → **Create version**, three
   times: `M0`, `M1` and `M2`.
3. **Settings (⚙) → Issues → Time tracking:** time tracking is enabled,
   with 8 hours per day and 5 days per week.

## 4. Check for duplicates before an import

1. Run the JQL search `project = ESHOP AND "Roadmap ID" is not EMPTY` and
   check that none of the roadmap IDs about to be imported appear.
2. Import only rows whose `Jira Key` in `issue-map.csv` is blank. For the
   first import, every row is blank and the project is empty.

## 5. Import the CSV

1. **Settings (⚙) → System → Import and export → External System Import →
   CSV.**
2. Upload `docs/jira/backlog.csv`. Use the UTF-8 encoding and the comma
   delimiter, then select **Next**.
3. Import into the existing project `eShop_AI (ESHOP)`.
4. Map the fields:

   | CSV column | Jira field | Notes |
   |---|---|---|
   | Roadmap ID | Roadmap ID (custom field) | Manual: pick the field created in step 3 |
   | Summary | Summary | |
   | Issue Type | Issue Type | All rows are `Task` |
   | Status | Status | Manual: tick **Map field value** and map each value to the same status |
   | Priority | Priority | Highest, High and Medium are Jira defaults |
   | Fix Version | Fix Version(s) | Manual: map to the existing `M0` to `M2` versions |
   | Labels (×4) | Labels | Map all four columns to Labels; empty cells are ignored |
   | Original Estimate | Original Estimate | Seconds (28800 = 1 day). Check the unit in the preview |
   | Description | Description | |

5. Select **Validate**. Fix every error the validation reports before you
   import.
6. Select **Begin import**. Keep **Download a detailed log** and the
   saved configuration file outside the repository. They may contain
   account details.

## 6. Verify the import

Run these JQL searches:

| Check | JQL | Expected |
|---|---|---|
| Issue count | `project = ESHOP` | 32 issues |
| Deferred tasks | `project = ESHOP AND labels = deferred` | Only SHOP-009 and SHOP-125, status To Do |
| Done tasks | `project = ESHOP AND status = Done` | 9 issues (SHOP-001 to SHOP-008 and SHOP-124) |
| Missing resolution | `project = ESHOP AND status = Done AND resolution is EMPTY` | None. If any appear, set Resolution to Done with **Bulk change** |
| Estimates | Open SHOP-010 | Original Estimate shows 2d |

Then sort the search results by the `Roadmap ID` column. No roadmap ID may
appear twice.

## 7. Record the mapping and dependencies

1. In the search `project = ESHOP ORDER BY key ASC`, show the **Key** and
   **Roadmap ID** columns. Then **Export → Export CSV (current fields)**.
2. Fill in the matching `Jira Key` in `docs/jira/issue-map.csv` for each
   roadmap ID. Do not guess keys, and copy each one only from the export.
3. Run `python3 scripts/validate_docs.py --strict`. It rejects duplicate,
   malformed or missing keys.
4. For each dependency listed in an issue description ("Depends on: …"),
   add an **is blocked by** link to the dependency's issue. Use the mapping
   to find its key.
5. Open a pull request with the updated mapping. SHOP-009 is marked Done
   only after the checks in section 6 have passed.

## Later imports

Later milestones are appended to `backlog.csv` when they start. Repeat
sections 4 to 7 for the new rows only. Before importing, remove the rows
that already have a Jira key from a temporary copy of the file, so the
repository file keeps the full backlog.
