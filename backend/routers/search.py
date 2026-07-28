from fastapi import APIRouter, Query, Header, HTTPException
from fastapi.responses import HTMLResponse
from database.database import SessionLocal
from database.models import EmailDelivery, User, Job
from services.search.search_service import search_papers
from services.models.paper import paper_to_dict
from utils.helpers import require_auth, verify_token, check_rate_limit

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search")
def search(q: str, limit: int = Query(default=50, le=100), cursor: str = "*", time_range: str = "all", authorization: str = Header(None)):
    ip_key = authorization or f"ip:{q[:20]}"
    check_rate_limit(ip_key, max_requests=30, window_sec=60)
    data = search_papers(query=q, page_size=limit, cursor=cursor, time_range=time_range)
    return {
        "query": q,
        "count": len(data["papers"]),
        "total": data["total_count"],
        "cursor": cursor,
        "next_cursor": data["next_cursor"],
        "results": [paper_to_dict(p) for p in data["papers"]],
    }


def _html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


@router.get("/daily-email", response_class=HTMLResponse)
def daily_email_page(authorization: str = Header(None), token: str = None):
    uid = None
    if authorization:
        uid = verify_token(authorization[7:]) if authorization.startswith("Bearer ") else None
    if not uid and token:
        uid = verify_token(token)
    if not uid:
        return HTMLResponse("<h1>Unauthorized</h1><p>Please provide a valid token via <code>?token=...</code> or <code>Authorization: Bearer ...</code> header.</p>", status_code=401)

    db = SessionLocal()
    try:
        deliveries = db.query(EmailDelivery).order_by(EmailDelivery.created_at.desc()).limit(30).all()
        users = db.query(User).filter(User.is_active == True).all()
        recent_jobs = db.query(Job).order_by(Job.created_at.desc()).limit(10).all()
    finally:
        db.close()

    rows = ""
    for d in deliveries:
        status_color = {"SENT": "#16a34a", "FAILED": "#dc2626", "PENDING": "#f59e0b", "SKIPPED": "#64748b"}.get(d.status, "#64748b")
        rows += f"""<tr>
            <td>{_html_escape(d.created_at.strftime('%m-%d %H:%M')) if d.created_at else '-'}</td>
            <td>{_html_escape(d.kind or '')}</td>
            <td><span style="color:{status_color};font-weight:600;">{_html_escape(d.status)}</span></td>
            <td>{_html_escape(d.to_email or '-')}</td>
            <td>{_html_escape(d.subject or '-')}</td>
            <td>{d.article_count}</td>
            <td style="font-size:12px;color:#94a3b8;">{_html_escape((d.error_message or '')[:60])}</td>
        </tr>"""

    user_rows = ""
    for u in users:
        enabled = "✅" if u.email_enabled else "❌"
        user_rows += f"""<tr>
            <td>{u.id}</td>
            <td>{_html_escape(u.name)}</td>
            <td>{enabled}</td>
            <td>{_html_escape(u.target_email or '-')}</td>
        </tr>"""

    job_rows = ""
    for j in recent_jobs:
        color = {"SUCCESS": "#16a34a", "FAILED": "#dc2626", "RUNNING": "#3b82f6", "PENDING": "#f59e0b"}.get(j.status, "#64748b")
        job_rows += f"""<tr>
            <td>{_html_escape(j.created_at.strftime('%m-%d %H:%M')) if j.created_at else '-'}</td>
            <td>{_html_escape(j.type)}</td>
            <td><span style="color:{color};font-weight:600;">{_html_escape(j.status)}</span></td>
            <td>{_html_escape((j.last_error or '')[:40])}</td>
        </tr>"""

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>ChemVigil Email Push Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#f1f5f9;padding:30px;color:#0f172a;}}
h1{{font-size:28px;color:#2456c3;margin-bottom:6px;}}
h2{{font-size:20px;margin:24px 0 12px;color:#334155;}}
.desc{{color:#64748b;margin-bottom:24px;}}
.actions{{display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;}}
.btn{{padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600;color:white;}}
.btn-blue{{background:#2456c3;}}
.btn-green{{background:#16a34a;}}
.btn-orange{{background:#f59e0b;}}
.btn:hover{{opacity:0.9;}}
table{{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06);margin-bottom:20px;}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid #e2e8f0;font-size:13px;}}
th{{background:#f8fafc;color:#475569;font-weight:600;}}
.card{{background:white;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06);margin-bottom:20px;}}
</style></head>
<body>
<h1>📨 Email Push Dashboard</h1>
<p class="desc">Track email deliveries and trigger push operations</p>
<div class="actions" id="adminActions">
    <button class="btn btn-blue" onclick="postAction('/api/v1/trigger-fetch')">🔄 Trigger RSS Fetch</button>
    <button class="btn btn-orange" onclick="postAction('/api/v1/trigger-summary')">📊 Generate Weekly Report</button>
    <button class="btn btn-green" onclick="postAction('/api/v1/trigger-push-new')">📬 Push New Articles Now</button>
</div>
<script>
const _token = "{token or (authorization or '').replace('Bearer ', '')}";
async function postAction(url) {{
    try {{
        const resp = await fetch(url, {{ method: 'POST', headers: {{ 'Authorization': 'Bearer ' + _token }} }});
        const text = await resp.text();
        alert('Done: ' + text.substring(0, 200));
    }} catch(e) {{
        alert('Error: ' + e);
    }}
}}
</script>
<h2>📬 Recent Deliveries</h2>
<table>
<thead><tr><th>Time</th><th>Kind</th><th>Status</th><th>To</th><th>Subject</th><th>Articles</th><th>Error</th></tr></thead>
<tbody>{rows or '<tr><td colspan="7" style="text-align:center;color:#94a3b8;">No deliveries yet</td></tr>'}</tbody>
</table>
<div class="card">
<h2>📊 Stats</h2>
<p style="color:#475569;font-size:14px;">Total deliveries: <strong>{len(deliveries)}</strong></p>
</div>
<h2>👤 Users</h2>
<table>
<thead><tr><th>ID</th><th>Name</th><th>Email Enabled</th><th>Target Email</th></tr></thead>
<tbody>{user_rows or '<tr><td colspan="4" style="text-align:center;color:#94a3b8;">No users</td></tr>'}</tbody>
</table>
<h2>⚙ Recent Jobs</h2>
<table>
<thead><tr><th>Time</th><th>Type</th><th>Status</th><th>Error</th></tr></thead>
<tbody>{job_rows or '<tr><td colspan="4" style="text-align:center;color:#94a3b8;">No jobs</td></tr>'}</tbody>
</table>
</body>
</html>""")
