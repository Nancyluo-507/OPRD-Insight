import {
    getUser, listJournals, listFollows, followJournal, unfollowJournal,
    updateSettings, listJobs, enqueueJob,
    listFavorites, listUserArticles,
    listReports, getReport,
} from "./api.js";

import { getUserId, getToken, isLoggedIn, login, register, logout as authLogout } from "./auth.js";

async function ensureUser() {
    if (!isLoggedIn()) return null;
    return getUserId();
}

// ========================================
// Subscription Page (Journals only)
// ========================================

async function renderFollowedJournals(userId) {
    const el = document.getElementById("followed-journals");
    if (!el) return;
    try {
        const data = await listFollows(userId);
        const journals = data.journals || [];
        if (journals.length === 0) {
            el.innerHTML = '<p style="color:#64748b">No journals followed yet. Browse the list below.</p>';
            return;
        }
        el.innerHTML = journals.map(j =>
            `<div class="journal-item">
                <div>
                    <span class="journal-name">${j.title}</span>
                    <span class="journal-publisher">${j.publisher || ""}</span>
                </div>
                <button class="unfollow-btn" data-jid="${j.id}">Unfollow</button>
            </div>`
        ).join("");
        el.querySelectorAll(".unfollow-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                await unfollowJournal(userId, btn.dataset.jid);
                renderFollowedJournals(userId);
                renderAllJournals(userId);
            });
        });
    } catch (e) {
        el.innerHTML = `<p style="color:#dc2626">Error: ${e.message}</p>`;
    }
}

async function renderAllJournals(userId) {
    const el = document.getElementById("journal-list");
    if (!el) return;
    try {
        const [journalsData, followsData] = await Promise.all([
            listJournals(),
            listFollows(userId),
        ]);
        const journals = journalsData.journals || [];
        const followedIds = new Set((followsData.journals || []).map(j => j.id));

        const searchTerm = (el._searchValue || "").toLowerCase().trim();

        const groups = {};
        for (const j of journals) {
            const pub = j.publisher || "Other";
            if (!groups[pub]) groups[pub] = [];
            groups[pub].push(j);
        }

        let html = "";
        for (const [publisher, js] of Object.entries(groups)) {
            const filtered = searchTerm ? js.filter(j => j.title.toLowerCase().includes(searchTerm)) : js;
            if (filtered.length === 0) continue;

            const openKey = "pub_" + publisher;
            if (el._openGroups === undefined) el._openGroups = {};
            if (el._openGroups[openKey] === undefined) el._openGroups[openKey] = true;
            const isOpen = el._openGroups[openKey];

            html += `<div class="pub-group">
                <div class="pub-header ${isOpen ? 'open' : ''}" data-pub="${openKey}">
                    <span class="pub-arrow">${isOpen ? '\u25BC' : '\u25B6'}</span>
                    <span class="pub-name">${publisher}</span>
                    <span class="pub-count">${filtered.length}</span>
                </div>
                <div class="pub-body" style="display:${isOpen ? 'block' : 'none'}">
                    ${filtered.map(j => {
                        const isF = followedIds.has(j.id);
                        return `<div class="journal-item">
                            <div>
                                <span class="journal-name">${j.title}</span>
                                <span class="journal-publisher">${j.short_name || ""}</span>
                            </div>
                            <button class="${isF ? 'follow-btn following' : 'follow-btn'}" data-jid="${j.id}">
                                ${isF ? 'Following' : 'Follow'}
                            </button>
                        </div>`;
                    }).join("")}
                </div>
            </div>`;
        }

        if (!html) {
            html = '<p style="color:#64748b">No journals match your search.</p>';
        }

        el.innerHTML = html;

        el.querySelectorAll(".pub-header").forEach(h => {
            h.addEventListener("click", () => {
                const key = h.dataset.pub;
                if (!el._openGroups) el._openGroups = {};
                el._openGroups[key] = !el._openGroups[key];
                const body = h.nextElementSibling;
                body.style.display = el._openGroups[key] ? "block" : "none";
                h.classList.toggle("open");
                h.querySelector(".pub-arrow").textContent = el._openGroups[key] ? "\u25BC" : "\u25B6";
            });
        });

        el.querySelectorAll(".follow-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const jid = btn.dataset.jid;
                if (btn.classList.contains("following")) {
                    await unfollowJournal(userId, jid);
                } else {
                    await followJournal(userId, jid);
                }
                renderAllJournals(userId);
                renderFollowedJournals(userId);
            });
        });
    } catch (e) {
        el.innerHTML = `<p style="color:#dc2626">Error: ${e.message}</p>`;
    }
}

function initSubscription(userId) {
    renderFollowedJournals(userId);
    renderAllJournals(userId);

    const searchInput = document.getElementById("journalSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            const el = document.getElementById("journal-list");
            if (el) el._searchValue = searchInput.value;
            renderAllJournals(userId);
        });
    }

    const refreshBtn = document.getElementById("refreshJournalsBtn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => renderAllJournals(userId));
    }
}

// ========================================
// Topics Page (User Interest)
// ========================================

async function renderInterests(userId) {
    const el = document.getElementById("interest-list");
    if (!el) return;
    try {
        const resp = await fetch(`/api/v1/user/${userId}/interests`);
        const data = await resp.json();
        const interests = data.interests || [];
        if (interests.length === 0) {
            el.innerHTML = '<p style="color:#64748b">No research interests yet. Create one above.</p>';
            return;
        }
        el.innerHTML = interests.map(i =>
            `<div class="topic-item" style="border-left:4px solid #2456c3;padding:12px 16px;margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <div style="font-weight:600;color:#0f172a;font-size:15px;">${i.name}</div>
                        <div style="font-size:12px;color:#2456c3;margin:4px 0;">${i.domain}</div>
                        <div style="font-size:13px;color:#475569;">${(i.description || "").substring(0, 120)}${(i.description || "").length > 120 ? "..." : ""}</div>
                        ${i.keywords ? `<div style="font-size:12px;color:#94a3b8;margin-top:4px;">Keywords: ${i.keywords}</div>` : ""}
                    </div>
                    <button class="delete-btn" data-iid="${i.id}" style="flex-shrink:0;">Delete</button>
                </div>
            </div>`
        ).join("");
        el.querySelectorAll(".delete-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                if (!confirm("Delete this interest?")) return;
                await fetch(`/api/v1/interests/${btn.dataset.iid}`, { method: "DELETE" });
                renderInterests(userId);
            });
        });
    } catch (e) {
        el.innerHTML = `<p style="color:#dc2626">Error: ${e.message}</p>`;
    }
}

async function initTopics(userId) {
    // Load domains into select
    const domainSelect = document.getElementById("interestDomainSelect");
    if (domainSelect) {
        try {
            const resp = await fetch("/api/v1/domains");
            const data = await resp.json();
            data.domains.forEach(d => {
                const opt = document.createElement("option");
                opt.value = d;
                opt.textContent = d;
                domainSelect.appendChild(opt);
            });
        } catch (e) {
            console.warn("Failed to load domains:", e);
        }
    }

    renderInterests(userId);

    const createBtn = document.getElementById("createInterestBtn");
    if (createBtn) {
        createBtn.addEventListener("click", async () => {
            const name = document.getElementById("interestNameInput").value.trim();
            const domain = document.getElementById("interestDomainSelect").value;
            const description = document.getElementById("interestDescInput").value.trim();
            const keywords = document.getElementById("interestKeywordsInput").value.trim();
            if (!name) { alert("Please enter a name"); return; }
            if (!domain) { alert("Please select a domain"); return; }
            if (!description) { alert("Please describe your research interest"); return; }
            createBtn.disabled = true;
            createBtn.textContent = "Creating...";
            try {
                const resp = await fetch(`/api/v1/user/${userId}/interests`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, domain, description, keywords }),
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.detail || err.error || resp.statusText);
                }
                document.getElementById("interestNameInput").value = "";
                document.getElementById("interestDescInput").value = "";
                document.getElementById("interestKeywordsInput").value = "";
                document.getElementById("interestDomainSelect").value = "";
                renderInterests(userId);
            } catch (e) {
                alert("Error: " + e.message);
            } finally {
                createBtn.disabled = false;
                createBtn.textContent = "Create";
            }
        });
    }
}

// ========================================
// Email Page
// ========================================

async function renderEmailStatus(userId) {
    const statusEl = document.getElementById("email-status-detail");
    const previewEl = document.getElementById("email-report-preview");
    const deliveryList = document.getElementById("email-delivery-list");
    const statsEl = document.getElementById("email-status-stats");
    const retryBtn = document.getElementById("retryEmailsBtn");
    if (!statusEl) return;
    try {
        // Check user settings
        const user = await getUser(userId);
        if (!user.email_enabled || !user.target_email) {
            statusEl.innerHTML = `
                <div style="color:#dc2626;font-size:16px;margin-bottom:8px;">\u25BC Email Not Configured</div>
                <div style="font-size:14px;color:#64748b;">Go to <strong>Settings</strong> page to enable email and set your target address.</div>`;
            if (statsEl) statsEl.innerHTML = "";
            if (retryBtn) retryBtn.style.display = "none";
            return;
        }

        // Fetch deliveries + jobs + stats
        const [deliveryData, jobData, statsData] = await Promise.all([
            fetch(`/api/v1/user/${userId}/email-deliveries?limit=20`).then(r => r.json()),
            listJobs(),
            fetch(`/api/v1/email-deliveries/stats`).then(r => r.json()).catch(() => null),
        ]);
        const deliveries = deliveryData.deliveries || [];
        const jobs = jobData.jobs || [];

        // Stats display
        if (statsEl && statsData) {
            statsEl.innerHTML = `
                <div style="font-size:13px;color:#475569;">Total: <strong>${statsData.total}</strong></div>
                <div style="font-size:13px;color:#16a34a;">Sent: <strong>${statsData.sent}</strong></div>
                <div style="font-size:13px;color:#dc2626;">Failed: <strong>${statsData.failed}</strong></div>
                <div style="font-size:13px;color:#64748b;">Rate: <strong>${statsData.success_rate}%</strong></div>`;
            if (retryBtn) {
                retryBtn.style.display = statsData.failed > 0 ? "inline-block" : "none";
            }
        }

        const lastFetch = jobs.find(j => j.type === "FETCH_JOURNAL" && j.status === "SUCCESS");
        const lastSummary = jobs.find(j => j.type === "WEEKLY_SUMMARY" && j.status === "SUCCESS");
        const lastPush = deliveries.find(d => d.kind === "new_articles" && d.status === "SENT");

        let statusHtml = `<div style="color:#16a34a;font-size:16px;margin-bottom:8px;">\u25B6Email Configured</div>
            <div style="font-size:14px;color:#64748b;margin-bottom:12px;">
                Sending to: <strong>${user.target_email}</strong>
            </div>`;

        if (lastFetch) {
            statusHtml += `<div style="font-size:13px;color:#475569;">Last RSS fetch: ${new Date(lastFetch.created_at).toLocaleDateString()}`;
        } else {
            statusHtml += `<div style="font-size:13px;color:#94a3b8;">No RSS fetch yet</div>`;
        }
        if (lastPush) {
            statusHtml += `<div style="font-size:13px;color:#475569;">Last push: ${new Date(lastPush.created_at).toLocaleDateString()} \u25B6${lastPush.subject} (${lastPush.article_count} articles) </div>`;
        }
        if (lastSummary) {
            statusHtml += `<div style="font-size:13px;color:#475569;">Last report: ${new Date(lastSummary.created_at).toLocaleDateString()} \u25B6/div>`;
        }
        statusEl.innerHTML = statusHtml;

        // Delivery history table
        if (deliveryList) {
            if (deliveries.length === 0) {
                deliveryList.innerHTML = '<p style="color:#94a3b8;font-size:14px;">No delivery records yet.</p>';
            } else {
                let rows = "";
                for (const d of deliveries) {
                    const color = {SENT:"#16a34a",FAILED:"#dc2626",PENDING:"#f59e0b",SKIPPED:"#64748b"}[d.status] || "#64748b";
                    rows += `<tr>
                        <td style="padding:8px 10px;border-bottom:1px solid #e2e8f0;font-size:13px;">${d.created_at ? new Date(d.created_at).toLocaleString() : '-'}</td>
                        <td style="padding:8px 10px;border-bottom:1px solid #e2e8f0;font-size:13px;">${d.kind}</td>
                        <td style="padding:8px 10px;border-bottom:1px solid #e2e8f0;font-size:13px;color:${color};font-weight:600;">${d.status}</td>
                        <td style="padding:8px 10px;border-bottom:1px solid #e2e8f0;font-size:13px;">${d.article_count || 0}</td>
                        <td style="padding:8px 10px;border-bottom:1px solid #e2e8f0;font-size:12px;color:#94a3b8;">${(d.error_message || '')}</td>
                    </tr>`;
                }
                deliveryList.innerHTML = `<table style="width:100%;border-collapse:collapse;">
                    <thead><tr>
                        <th style="padding:8px 10px;text-align:left;font-size:12px;color:#64748b;border-bottom:2px solid #e2e8f0;">Time</th>
                        <th style="padding:8px 10px;text-align:left;font-size:12px;color:#64748b;border-bottom:2px solid #e2e8f0;">Kind</th>
                        <th style="padding:8px 10px;text-align:left;font-size:12px;color:#64748b;border-bottom:2px solid #e2e8f0;">Status</th>
                        <th style="padding:8px 10px;text-align:left;font-size:12px;color:#64748b;border-bottom:2px solid #e2e8f0;">Articles</th>
                        <th style="padding:8px 10px;text-align:left;font-size:12px;color:#64748b;border-bottom:2px solid #e2e8f0;">Error</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>`;
            }
        }

        // Latest report preview
        const reportData = await listReports(userId);
        const reports = reportData.reports || [];
        if (reports.length > 0) {
            const latest = reports[0];
            previewEl.innerHTML = `
                <div style="color:#0f172a;font-weight:600;margin-bottom:4px;">${latest.title}</div>
                <div style="font-size:12px;color:#64748b;margin-bottom:8px;">${new Date(latest.created_at).toLocaleString()}</div>
                <div style="font-size:13px;color:#475569;">${latest.topic_count} topics, ${latest.total_matches} matched articles</div>`;
        } else {
            previewEl.innerHTML = 'No report generated yet.';
        }

    } catch (e) {
        statusEl.innerHTML = `<div style="color:#dc2626;">Error: ${e.message}</div>`;
    }
}

function initEmail(userId) {
    renderEmailStatus(userId);

    // Retry failed deliveries
    const retryBtn = document.getElementById("retryEmailsBtn");
    if (retryBtn) {
        retryBtn.addEventListener("click", async () => {
            retryBtn.disabled = true;
            retryBtn.textContent = "Retrying...";
            try {
                const resp = await fetch(`/api/v1/email-deliveries/retry`, { method: "POST" });
                const data = await resp.json();
                alert(`Retry job enqueued: #${data.job_id}`);
                setTimeout(() => renderEmailStatus(userId), 3000);
            } catch (e) {
                alert("Error: " + e.message);
            }
            retryBtn.disabled = false;
            retryBtn.textContent = "🔄 Retry Failed Deliveries";
        });
    }

    const fetchBtn = document.getElementById("fetchNowBtn");
    if (fetchBtn) {
        fetchBtn.addEventListener("click", async () => {
            fetchBtn.disabled = true;
            fetchBtn.textContent = "Fetching...";
            try {
                const result = await enqueueJob("FETCH_JOURNAL", userId);
                alert("Fetch job enqueued: #" + result.job_id);
                setTimeout(() => renderEmailStatus(userId), 2000);
            } catch (e) {
                alert("Error: " + e.message);
            }
            fetchBtn.disabled = false;
            fetchBtn.textContent = "Trigger RSS Fetch";
        });
    }

    const reportBtn = document.getElementById("genReportBtn");
    if (reportBtn) {
        reportBtn.addEventListener("click", async () => {
            reportBtn.disabled = true;
            reportBtn.textContent = "Generating...";
            try {
                const result = await enqueueJob("WEEKLY_SUMMARY", userId, {user_id: userId, send_email: true});
                alert("Weekly summary job enqueued: #" + result.job_id);
                setTimeout(() => renderEmailStatus(userId), 5000);
            } catch (e) {
                alert("Error: " + e.message);
            }
            reportBtn.disabled = false;
            reportBtn.textContent = "Generate Weekly Report";
        });
    }

    const testBtn = document.getElementById("sendTestEmailBtn");
    if (testBtn) {
        testBtn.addEventListener("click", async () => {
            testBtn.disabled = true;
            testBtn.textContent = "Sending...";
            try {
                const user = await getUser(userId);
                if (!user.email_enabled || !user.target_email) {
                    alert("Please configure email in Settings first.");
                    testBtn.disabled = false;
                    testBtn.textContent = "Send Test Email";
                    return;
                }
                const result = await enqueueJob("SEND_EMAIL", userId, {
                    kind: "topic_notification",
                    to_email: user.target_email,
                    subject: "ChemVigil Test Email",
                    user_id: userId,
                    html: "<h1>Test</h1><p>Your email configuration is working!</p>"
                });
                alert("Test email job enqueued: #" + result.job_id);
                setTimeout(() => renderEmailStatus(userId), 3000);
            } catch (e) {
                alert("Error: " + e.message);
            }
            testBtn.disabled = false;
            testBtn.textContent = "Send Test Email";
        });
    }

    const pushBtn = document.getElementById("pushNewBtn");
    if (pushBtn) {
        pushBtn.addEventListener("click", async () => {
            pushBtn.disabled = true;
            pushBtn.textContent = "Pushing...";
            try {
                const result = await enqueueJob("NEW_ARTICLES", userId, {user_id: userId});
                alert("Push job enqueued: #" + result.job_id);
                setTimeout(() => renderEmailStatus(userId), 3000);
            } catch (e) {
                alert("Error: " + e.message);
            }
            pushBtn.disabled = false;
            pushBtn.textContent = "Push New Articles";
        });
    }
}

// ========================================
// Favorites Page
// ========================================

async function renderFavorites(userId) {
    const el = document.getElementById("favorites-list");
    const loading = document.getElementById("favorites-loading");
    if (!el) return;
    try {
        const data = await listFavorites(userId);
        const articles = data.articles || [];
        if (loading) loading.style.display = "none";
        if (articles.length === 0) {
            el.innerHTML = '<p style="color:#64748b">No favorites yet.</p>';
            return;
        }
        el.innerHTML = articles.map(a =>
            `<div class="article-item" data-doi="${a.doi}">
                <div class="article-title">${a.article_title || "No title"}</div>
                <div class="article-meta">
                    DOI: <a href="https://doi.org/${a.doi}" target="_blank" rel="noopener">${a.doi || "-"}</a> |
                    ${a.created_at ? new Date(a.created_at).toLocaleDateString() : ""}
                </div>
                <button class="unfav-btn" data-doi="${a.doi}" style="margin-top:6px;padding:4px 10px;background:#fee2e2;color:#dc2626;border:1px solid #fca5a5;border-radius:6px;cursor:pointer;font-size:12px;">Remove Favorite</button>
            </div>`
        ).join("");
        // Attach unfavorite handlers
        el.querySelectorAll(".unfav-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const doi = btn.dataset.doi;
                try {
                    const { saveUserArticle } = await import("./api.js");
                    await saveUserArticle(userId, doi, false);
                    btn.closest(".article-item").remove();
                    const remaining = el.querySelectorAll(".article-item").length;
                    if (remaining === 0) el.innerHTML = '<p style="color:#64748b">No favorites yet.</p>';
                } catch (e) {
                    btn.textContent = "Error";
                    setTimeout(() => { btn.textContent = "Remove Favorite"; }, 2000);
                }
            });
        });
    } catch (e) {
        if (loading) loading.style.display = "none";
        el.innerHTML = `<p style="color:#dc2626">Error: ${e.message}</p>`;
    }
}

// ========================================
// History Page
// ========================================

async function renderHistory(userId) {
    const el = document.getElementById("history-list");
    const loading = document.getElementById("history-loading");
    if (!el) return;
    try {
        const data = await listHistory(userId);
        const articles = data.articles || [];
        if (loading) loading.style.display = "none";
        if (articles.length === 0) {
            el.innerHTML = '<p style="color:#64748b">No reading history yet.</p>';
            return;
        }
        el.innerHTML = articles.map(a =>
            `<div class="article-item">
                <div class="article-title">${a.article_title || "No title"}</div>
                <div class="article-meta">
                    DOI: ${a.doi || "-"} | ${a.created_at ? new Date(a.created_at).toLocaleDateString() : ""}
                </div>
            </div>`
        ).join("");
    } catch (e) {
        if (loading) loading.style.display = "none";
        el.innerHTML = `<p style="color:#dc2626">Error: ${e.message}</p>`;
    }
}

// ========================================
// Settings Page
// ========================================

async function loadSettings(userId) {
    try {
        const user = await getUser(userId);
        const enabledCheck = document.getElementById("emailEnabledCheck");
        const emailInput = document.getElementById("targetEmailInput");
        if (enabledCheck) enabledCheck.checked = user.email_enabled || false;
        if (emailInput) emailInput.value = user.target_email || "";
    } catch (e) {
        console.error("Failed to load settings", e);
    }
}

function initSettings(userId) {
    loadSettings(userId);
    const saveBtn = document.getElementById("saveSettingsBtn");
    const statusEl = document.getElementById("settingsStatus");
    if (saveBtn) {
        saveBtn.addEventListener("click", async () => {
            const enabled = document.getElementById("emailEnabledCheck").checked;
            const email = document.getElementById("targetEmailInput").value.trim();
            try {
                await updateSettings(userId, enabled, email);
                if (statusEl) statusEl.textContent = "Saved!";
                setTimeout(() => { if (statusEl) statusEl.textContent = ""; }, 2000);
            } catch (e) {
                if (statusEl) statusEl.textContent = "Error: " + e.message;
            }
        });
    }
}

// ========================================
// Init
// ========================================

(async function init() {
    const userId = await ensureUser();

    const observer = new MutationObserver(() => {
        const subPage = document.getElementById("subscription-page");
        if (subPage && subPage.classList.contains("active-page")) {
            renderFollowedJournals(userId);
            renderAllJournals(userId);
        }
        const topicsPage = document.getElementById("topics-page");
        if (topicsPage && topicsPage.classList.contains("active-page")) {
            renderInterests(userId);
        }
        const emailPage = document.getElementById("email-page");
        if (emailPage && emailPage.classList.contains("active-page")) {
            renderEmailStatus(userId);
        }
        const favPage = document.getElementById("favorites-page");
        if (favPage && favPage.classList.contains("active-page")) {
            renderFavorites(userId);
        }
        const setPage = document.getElementById("settings-page");
        if (setPage && setPage.classList.contains("active-page")) {
            loadSettings(userId);
        }
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ["class"], subtree: true });

    const activePage = document.querySelector(".page.active-page");
    if (activePage) {
        const id = activePage.id;
        if (id === "subscription-page") {
            renderFollowedJournals(userId);
            renderAllJournals(userId);
        } else if (id === "topics-page") {
            renderInterests(userId);
        } else if (id === "email-page") {
            renderEmailStatus(userId);
        } else if (id === "favorites-page") {
            renderFavorites(userId);
        } else if (id === "settings-page") {
            loadSettings(userId);
        }
    }

    if (userId) {
        initSubscription(userId);
        initTopics(userId);
        initEmail(userId);
        initSettings(userId);
    }
})();

// ========================================
// Auth UI
// ========================================

(async function initAuth() {
    const overlay = document.getElementById("loginOverlay");
    const errorEl = document.getElementById("loginError");
    const successEl = document.getElementById("loginSuccess");
    const nameInput = document.getElementById("authName");
    const passInput = document.getElementById("authPassword");
    const emailInput = document.getElementById("authEmail");
    const emailGroup = document.getElementById("emailGroup");
    const loginBtn = document.getElementById("authLoginBtn");
    const toggleBtn = document.getElementById("authToggleBtn");
    const tabLogin = document.getElementById("tabLogin");
    const tabRegister = document.getElementById("tabRegister");
    const logoutBtn = document.getElementById("logoutBtn");
    const userInfo = document.getElementById("userInfo");

    let isRegisterMode = false;

    function setError(msg) {
        if (!errorEl) return;
        errorEl.textContent = msg;
        errorEl.classList.toggle("show", !!msg);
    }

    function setSuccess(msg) {
        if (!successEl) return;
        successEl.textContent = msg;
        successEl.classList.toggle("show", !!msg);
    }

    function setMode(register) {
        isRegisterMode = register;
        if (register) {
            loginBtn.textContent = "Register";
            toggleBtn.textContent = "Already have an account? Sign In";
            emailGroup.style.display = "block";
            tabLogin.classList.remove("active");
            tabRegister.classList.add("active");
        } else {
            loginBtn.textContent = "Sign In";
            toggleBtn.textContent = "Don't have an account? Register";
            emailGroup.style.display = "none";
            tabLogin.classList.add("active");
            tabRegister.classList.remove("active");
        }
        setError(""); setSuccess("");
    }

    function showUserInfo() {
        const name = localStorage.getItem("chemvigil_user_name") || "";
        const uid = localStorage.getItem("chemvigil_user_id") || "";
        if (userInfo) {
            userInfo.innerHTML = `👤 ${name} (ID: ${uid})`;
        }
        if (overlay) overlay.classList.add("hidden");
    }

    if (isLoggedIn()) {
        const token = getToken();
        if (token) {
            try {
                const resp = await fetch(`/api/v1/auth/me`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (!resp.ok) throw new Error();
                const data = await resp.json();
                if (data.user) {
                    localStorage.setItem("chemvigil_target_email", data.user.target_email || "");
                }
            } catch(e) {}
        }
        showUserInfo();
        return;
    }

    // Show login overlay
    if (overlay) overlay.classList.remove("hidden");
    setError("");

    // Tabs
    if (tabLogin) tabLogin.addEventListener("click", () => setMode(false));
    if (tabRegister) tabRegister.addEventListener("click", () => setMode(true));

    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => setMode(!isRegisterMode));
    }

    // Enter key triggers login
    [nameInput, passInput, emailInput].forEach(el => {
        if (el) el.addEventListener("keydown", e => {
            if (e.key === "Enter" && loginBtn) loginBtn.click();
        });
    });

    if (loginBtn) {
        loginBtn.addEventListener("click", async () => {
            const name = nameInput.value.trim();
            const pass = passInput.value.trim();
            if (!name || !pass) {
                setError("Please enter username and password");
                return;
            }
            loginBtn.disabled = true;
            loginBtn.textContent = isRegisterMode ? "Registering..." : "Signing in...";
            try {
                if (isRegisterMode) {
                    const email = emailInput.value.trim();
                    if (!email) {
                        setError("Email is required for registration");
                        loginBtn.disabled = false;
                        loginBtn.textContent = "Register";
                        return;
                    }
                    await register(name, pass, email);
                    setSuccess("✅ Registration successful!");
                    setTimeout(() => { showUserInfo(); location.reload(); }, 1500);
                } else {
                    const user = await login(name, pass);
                    localStorage.setItem("chemvigil_target_email", user.target_email || "");
                    showUserInfo();
                    location.reload();
                }
            } catch (e) {
                setError(e.message);
            }
            loginBtn.disabled = false;
            loginBtn.textContent = isRegisterMode ? "Register" : "Sign In";
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            authLogout();
            localStorage.removeItem("chemvigil_target_email");
            location.reload();
        });
    }
})();

