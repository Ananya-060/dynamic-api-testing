"""
core/reporter.py

Custom HTML report generator for the Dynamic API Testing Framework.
Hooks into pytest's lifecycle to capture every test result, then
produces a self-contained, professional HTML dashboard at
reports/report.html when the session ends.
"""

import html as _html
import pytest
from datetime import datetime
from pathlib import Path

REPORT_PATH = Path("reports/report.html")


class CustomHtmlReporter:
    """Pytest plugin that generates a rich HTML test-execution dashboard."""

    def __init__(self):
        self.results = []
        self.session_start = None
        self.session_end = None

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def pytest_sessionstart(self, session):
        self.session_start = datetime.now()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()

        # Capture each test exactly once (on 'call', or on 'setup' if skipped)
        if report.when == "call" or (report.when == "setup" and report.skipped):
            parts = item.nodeid.replace("\\", "/").split("::")
            module = parts[0].replace("tests/", "")
            name = parts[-1]

            error = ""
            if report.failed:
                if hasattr(report.longrepr, "reprcrash"):
                    error = str(report.longrepr.reprcrash.message)
                else:
                    error = str(report.longrepr)[:400]
            elif report.skipped:
                longrepr = report.longrepr
                if isinstance(longrepr, tuple) and len(longrepr) >= 3:
                    error = str(longrepr[2])
                else:
                    error = str(longrepr)

            status = "passed" if report.passed else "failed" if report.failed else "skipped"
            self.results.append({
                "nodeid": item.nodeid,
                "module": module,
                "name": name,
                "status": status,
                "duration": round(report.duration, 3),
                "error": error,
            })

    def pytest_sessionfinish(self, session, exitstatus):
        self.session_end = datetime.now()
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(self._build_html(), encoding="utf-8")
        print(f"\n[Report] file:///{REPORT_PATH.resolve().as_posix()}\n")

    # ------------------------------------------------------------------
    # HTML generation
    # ------------------------------------------------------------------

    def _build_html(self) -> str:
        results = self.results
        total   = len(results)
        passed  = sum(1 for r in results if r["status"] == "passed")
        failed  = sum(1 for r in results if r["status"] == "failed")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        pass_rate = round((passed / total * 100) if total else 0, 1)

        total_dur = round(
            (self.session_end - self.session_start).total_seconds(), 2
        ) if (self.session_start and self.session_end) else 0
        avg_dur = round(
            sum(r["duration"] for r in results) / total, 3
        ) if total else 0
        timestamp = (
            self.session_start.strftime("%d %b %Y, %H:%M:%S")
            if self.session_start else "N/A"
        )

        # Status colour for header
        overall_color = "#3fb950" if failed == 0 else "#f85149"
        overall_label = "✓ ALL PASSED" if failed == 0 else f"✗ {failed} FAILED"

        # Pass-rate colour for donut centre
        rate_color = "#3fb950" if pass_rate >= 80 else ("#d29922" if pass_rate >= 50 else "#f85149")

        # SVG donut arcs
        r_val = 45
        circumference = round(2 * 3.14159 * r_val, 2)
        passed_arc  = round((passed  / total * circumference) if total else 0, 2)
        failed_arc  = round((failed  / total * circumference) if total else 0, 2)
        skipped_arc = round((skipped / total * circumference) if total else 0, 2)
        gap = round(circumference, 2)

        failed_offset  = round(-passed_arc, 2)
        skipped_offset = round(-(passed_arc + failed_arc), 2)

        # Table rows
        rows = []
        for i, r in enumerate(results, 1):
            status = r["status"]
            icon   = {"passed": "✓", "failed": "✗", "skipped": "⊘"}[status]
            err_e  = _html.escape(r["error"])
            err_short = (err_e[:130] + "…") if len(err_e) > 130 else err_e
            err_class = "error-msg" if status != "passed" else "error-msg none-msg"
            rows.append(f"""
        <tr data-status="{status}">
          <td class="row-num">{i}</td>
          <td>
            <div class="test-name">{_html.escape(r['name'])}</div>
            <div class="test-module">{_html.escape(r['module'])}</div>
          </td>
          <td><span class="badge {status}">{icon} {status.upper()}</span></td>
          <td class="duration">{r['duration']}s</td>
          <td><span class="{err_class}" title="{err_e}">{err_short or '—'}</span></td>
        </tr>""")
        rows_html = "\n".join(rows)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>API Test Report</title>
<style>
/* ── Reset & Base ───────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: #0d1117;
  color: #e1e4e8;
  min-height: 100vh;
  font-size: 14px;
  line-height: 1.5;
}}

/* ── Header ─────────────────────────────────────────────── */
.header {{
  background: linear-gradient(135deg, #1a2035 0%, #0d1b35 100%);
  padding: 24px 48px;
  border-bottom: 1px solid #30363d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.header-brand h1 {{
  font-size: 22px; font-weight: 700; letter-spacing: -0.3px;
}}
.brand-gradient {{
  background: linear-gradient(135deg, #58a6ff, #79c0ff);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.header-brand p {{ font-size: 12px; color: #8b949e; margin-top: 3px; }}
.header-meta {{
  display: flex; gap: 32px;
}}
.meta-item {{ display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }}
.meta-item span {{ font-size: 11px; color: #6e7681; text-transform: uppercase; letter-spacing: 0.06em; }}
.meta-item strong {{ font-size: 13px; color: #e1e4e8; }}

/* ── Main content ───────────────────────────────────────── */
.main {{ padding: 32px 48px 64px; }}

/* ── Summary cards ──────────────────────────────────────── */
.summary-grid {{
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 28px;
}}
.card {{
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 22px 16px;
  text-align: center;
  position: relative;
  overflow: hidden;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}}
.card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
.card::before {{
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  border-radius: 3px 3px 0 0;
}}
.card.total::before  {{ background: linear-gradient(90deg, #58a6ff, #79c0ff); }}
.card.passed::before {{ background: linear-gradient(90deg, #3fb950, #56d364); }}
.card.failed::before {{ background: linear-gradient(90deg, #f85149, #ff7b72); }}
.card.skipped::before{{ background: linear-gradient(90deg, #d29922, #e3b341); }}
.card.rate::before   {{ background: linear-gradient(90deg, #bc8cff, #d2a8ff); }}
.card:hover.total  {{ border-color: rgba(88,166,255,.35); }}
.card:hover.passed {{ border-color: rgba(63,185,80,.35); }}
.card:hover.failed {{ border-color: rgba(248,81,73,.35); }}
.card:hover.skipped{{ border-color: rgba(210,153,34,.35); }}
.card:hover.rate   {{ border-color: rgba(188,140,255,.35); }}
.card .number {{ font-size: 42px; font-weight: 800; line-height: 1; margin-bottom: 6px; }}
.card.total .number  {{ color: #58a6ff; }}
.card.passed .number {{ color: #3fb950; }}
.card.failed .number {{ color: #f85149; }}
.card.skipped .number{{ color: #d29922; }}
.card.rate .number   {{ color: #bc8cff; }}
.card .label {{
  font-size: 10px; color: #8b949e;
  text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600;
}}

/* ── Chart + Stats panel ────────────────────────────────── */
.info-panel {{
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  margin-bottom: 28px;
  overflow: hidden;
}}
.donut-section {{
  display: flex; align-items: center; gap: 28px;
  padding: 28px 32px;
  border-right: 1px solid #30363d;
}}
.donut-wrap {{ position: relative; width: 130px; height: 130px; }}
.donut-wrap svg {{ transform: rotate(-90deg); }}
.donut-center {{
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}}
.donut-pct {{
  font-size: 26px; font-weight: 800;
  color: {rate_color};
  line-height: 1;
}}
.donut-lbl {{
  font-size: 9px; color: #8b949e;
  text-transform: uppercase; letter-spacing: 0.1em;
  margin-top: 2px;
}}
.legend {{ display: flex; flex-direction: column; gap: 11px; }}
.legend-item {{
  display: flex; align-items: center; gap: 8px; font-size: 13px;
}}
.dot {{ width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }}
.dot.passed {{ background: #3fb950; }}
.dot.failed {{ background: #f85149; }}
.dot.skipped{{ background: #d29922; }}
.legend-label {{ color: #8b949e; flex: 1; }}
.legend-count {{ color: #e1e4e8; font-weight: 700; font-size: 14px; }}

.stats-section {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
}}
.stat-block {{
  padding: 28px 24px;
  border-right: 1px solid #30363d;
}}
.stat-block:last-child {{ border-right: none; }}
.stat-block .stat-title {{
  font-size: 10px; color: #8b949e;
  text-transform: uppercase; letter-spacing: 0.1em;
  font-weight: 600; margin-bottom: 8px;
}}
.stat-block .stat-value {{
  font-size: 22px; font-weight: 800; color: #e1e4e8; line-height: 1;
}}
.stat-block .stat-sub {{
  font-size: 12px; color: #6e7681; margin-top: 5px;
}}

/* ── Table section ──────────────────────────────────────── */
.table-header {{
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px;
}}
.table-title {{ font-size: 15px; font-weight: 600; color: #e1e4e8; }}
.filters {{ display: flex; gap: 7px; }}
.filter-btn {{
  padding: 6px 16px; border-radius: 20px;
  border: 1px solid #30363d;
  background: transparent; color: #8b949e;
  font-size: 12px; cursor: pointer;
  transition: all 0.18s; font-family: inherit; font-weight: 500;
}}
.filter-btn:hover {{ background: #21262d; color: #e1e4e8; }}
.filter-btn.f-all     {{ border-color: #30363d; }}
.filter-btn.f-all.active {{ background: #1f3a5f; color: #58a6ff; border-color: #58a6ff; }}
.filter-btn.f-passed.active  {{ background: #1a3a28; color: #3fb950; border-color: #3fb950; }}
.filter-btn.f-failed.active  {{ background: #3a1a1a; color: #f85149; border-color: #f85149; }}
.filter-btn.f-skipped.active {{ background: #3a2e10; color: #d29922; border-color: #d29922; }}

.progress-bar {{
  height: 4px; background: #21262d; border-radius: 3px;
  margin-bottom: 20px; overflow: hidden;
}}
.progress-fill {{
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, #3fb950, #58a6ff);
  width: {pass_rate}%;
  transition: width 1.2s cubic-bezier(.4,0,.2,1);
}}

.table-wrap {{
  background: #161b22; border: 1px solid #30363d;
  border-radius: 12px; overflow: hidden;
}}
table {{ width: 100%; border-collapse: collapse; }}
thead tr {{ background: #1c2128; }}
th {{
  padding: 11px 16px; text-align: left;
  font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.09em;
  color: #6e7681; border-bottom: 1px solid #30363d;
}}
td {{
  padding: 13px 16px; font-size: 13px;
  border-bottom: 1px solid #1c2128; vertical-align: middle;
}}
tbody tr:last-child td {{ border-bottom: none; }}
tbody tr:hover td {{ background: #1c2128; transition: background 0.1s; }}

.row-num {{ color: #6e7681; font-size: 12px; width: 36px; text-align: right; padding-right: 20px; }}
.test-name {{
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 12px; color: #79c0ff;
}}
.test-module {{ font-size: 11px; color: #6e7681; margin-top: 3px; }}
.badge {{
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 11px; border-radius: 20px;
  font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.06em;
  white-space: nowrap;
}}
.badge.passed  {{ background: rgba(63,185,80,.1);  color: #3fb950; border: 1px solid rgba(63,185,80,.25); }}
.badge.failed  {{ background: rgba(248,81,73,.1);  color: #f85149; border: 1px solid rgba(248,81,73,.25); }}
.badge.skipped {{ background: rgba(210,153,34,.1); color: #d29922; border: 1px solid rgba(210,153,34,.25); }}
.duration {{
  font-family: 'Consolas', 'Courier New', monospace;
  color: #8b949e; font-size: 12px; white-space: nowrap;
}}
.error-msg {{
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 11px; color: #f85149;
  max-width: 420px; display: block;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  cursor: default;
}}
.error-msg.none-msg {{ color: #6e7681; }}

/* ── Footer ─────────────────────────────────────────────── */
.footer {{
  margin-top: 48px; padding-top: 20px;
  border-top: 1px solid #21262d;
  text-align: center; font-size: 12px; color: #6e7681;
}}
</style>
</head>
<body>

<!-- ── HEADER ───────────────────────────────────────────── -->
<div class="header">
  <div class="header-brand">
    <h1>API Test Report</h1>
    <p>Execution summary — {timestamp}</p>
  </div>
  <div class="header-meta">
    <div class="meta-item">
      <span>Run Date</span>
      <strong>{timestamp}</strong>
    </div>
    <div class="meta-item">
      <span>Duration</span>
      <strong>{total_dur}s</strong>
    </div>
    <div class="meta-item">
      <span>Overall Status</span>
      <strong style="color:{overall_color}">{overall_label}</strong>
    </div>
  </div>
</div>

<div class="main">

  <!-- ── SUMMARY CARDS ──────────────────────────────────── -->
  <div class="summary-grid">
    <div class="card total">
      <div class="number">{total}</div>
      <div class="label">Total Tests</div>
    </div>
    <div class="card passed">
      <div class="number">{passed}</div>
      <div class="label">Passed</div>
    </div>
    <div class="card failed">
      <div class="number">{failed}</div>
      <div class="label">Failed</div>
    </div>
    <div class="card skipped">
      <div class="number">{skipped}</div>
      <div class="label">Skipped</div>
    </div>
    <div class="card rate">
      <div class="number">{pass_rate}%</div>
      <div class="label">Pass Rate</div>
    </div>
  </div>

  <!-- ── CHART + STATS PANEL ────────────────────────────── -->
  <div class="info-panel">
    <div class="donut-section">
      <div class="donut-wrap">
        <svg width="130" height="130" viewBox="0 0 100 100">
          <!-- background track -->
          <circle cx="50" cy="50" r="{r_val}" fill="none" stroke="#21262d" stroke-width="10"/>
          <!-- passed arc -->
          <circle cx="50" cy="50" r="{r_val}" fill="none" stroke="#3fb950" stroke-width="10"
            stroke-dasharray="{passed_arc} {gap}"
            stroke-dashoffset="0"/>
          <!-- failed arc -->
          <circle cx="50" cy="50" r="{r_val}" fill="none" stroke="#f85149" stroke-width="10"
            stroke-dasharray="{failed_arc} {gap}"
            stroke-dashoffset="{failed_offset}"/>
          <!-- skipped arc -->
          <circle cx="50" cy="50" r="{r_val}" fill="none" stroke="#d29922" stroke-width="10"
            stroke-dasharray="{skipped_arc} {gap}"
            stroke-dashoffset="{skipped_offset}"/>
        </svg>
        <div class="donut-center">
          <div class="donut-pct">{pass_rate}%</div>
          <div class="donut-lbl">Pass Rate</div>
        </div>
      </div>
      <div class="legend">
        <div class="legend-item"><div class="dot passed"></div><span class="legend-label">Passed</span><span class="legend-count">{passed}</span></div>
        <div class="legend-item"><div class="dot failed"></div><span class="legend-label">Failed</span><span class="legend-count">{failed}</span></div>
        <div class="legend-item"><div class="dot skipped"></div><span class="legend-label">Skipped</span><span class="legend-count">{skipped}</span></div>
      </div>
    </div>

    <div class="stats-section">
      <div class="stat-block">
        <div class="stat-title">Total Duration</div>
        <div class="stat-value">{total_dur}s</div>
        <div class="stat-sub">Avg {avg_dur}s per test</div>
      </div>
      <div class="stat-block">
        <div class="stat-title">Test Suite</div>
        <div class="stat-value" style="font-size:14px; padding-top:4px;">API Framework</div>
        <div class="stat-sub">Dynamic data-driven tests</div>
      </div>
      <div class="stat-block">
        <div class="stat-title">Generated</div>
        <div class="stat-value" style="font-size:14px; padding-top:4px;">{timestamp}</div>
        <div class="stat-sub">{total} test cases executed</div>
      </div>
    </div>
  </div>

  <!-- ── TEST RESULTS TABLE ─────────────────────────────── -->
  <div class="table-header">
    <span class="table-title">Test Results <span style="color:#6e7681;font-weight:400">({total})</span></span>
    <div class="filters">
      <button class="filter-btn f-all active"     onclick="filterTests('all', this)">All ({total})</button>
      <button class="filter-btn f-passed"  onclick="filterTests('passed', this)">✓ Passed ({passed})</button>
      <button class="filter-btn f-failed"  onclick="filterTests('failed', this)">✗ Failed ({failed})</button>
      <button class="filter-btn f-skipped" onclick="filterTests('skipped', this)">⊘ Skipped ({skipped})</button>
    </div>
  </div>

  <div class="progress-bar"><div class="progress-fill"></div></div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th style="text-align:right;padding-right:20px">#</th>
          <th>Test Name</th>
          <th>Status</th>
          <th>Duration</th>
          <th>Details / Error</th>
        </tr>
      </thead>
      <tbody id="tbody">
{rows_html}
      </tbody>
    </table>
  </div>

  <div class="footer">
    API Test Report &nbsp;·&nbsp; {timestamp}
  </div>

</div><!-- /main -->

<script>
(function() {{
  function filterTests(status, btn) {{
    // Reset all buttons
    document.querySelectorAll('.filter-btn').forEach(function(b) {{
      b.classList.remove('active');
    }});
    btn.classList.add('active');

    document.querySelectorAll('#tbody tr').forEach(function(row) {{
      row.style.display =
        (status === 'all' || row.dataset.status === status) ? '' : 'none';
    }});
  }}
  window.filterTests = filterTests;
}})();
</script>

</body>
</html>"""
