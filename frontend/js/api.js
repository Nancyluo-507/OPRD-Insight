const API_BASE = "";

async function request(url, options = {}) {
    const token = localStorage.getItem("chemvigil_token");
    const headers = { "Content-Type": "application/json", ...options.headers };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    const resp = await fetch(`${API_BASE}${url}`, { ...options, headers });
    if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${text.substring(0, 100)}`);
    }
    return resp.json();
}


// ========================================
// Search Papers
// ========================================

export async function searchPaper(keyword, timeRange = "all", signal = null) {
    return request(`/api/v1/search?q=${encodeURIComponent(keyword)}&time_range=${encodeURIComponent(timeRange)}`, { signal });
}


// ========================================
// User
// ========================================

export async function initUser(name = "default") {
    return request(`/api/v1/user/init?name=${encodeURIComponent(name)}`, { method: "POST" });
}

export async function getUser(userId) {
    return request(`/api/v1/user/${userId}`);
}


// ========================================
// Journals
// ========================================

export async function listJournals(search = "", publisher = "") {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (publisher) params.set("publisher", publisher);
    return request(`/api/v1/journals?${params.toString()}`);
}

export async function listFollows(userId) {
    return request(`/api/v1/user/${userId}/follows`);
}

export async function followJournal(userId, journalId) {
    return request(`/api/v1/user/${userId}/follow/${journalId}`, { method: "POST" });
}

export async function unfollowJournal(userId, journalId) {
    return request(`/api/v1/user/${userId}/follow/${journalId}`, { method: "DELETE" });
}


// ========================================
// Topics
// ========================================

export async function listTopics(userId) {
    return request(`/api/v1/user/${userId}/topics`);
}

export async function createTopic(userId, name, keywords = "") {
    return request(`/api/v1/user/${userId}/topics`, {
        method: "POST",
        body: JSON.stringify({ name, keywords }),
    });
}

export async function deleteTopic(topicId) {
    return request(`/api/v1/topics/${topicId}`, { method: "DELETE" });
}


// ========================================
// Matches
// ========================================

export async function listMatches(userId, topicId = null, days = 7) {
    const params = new URLSearchParams();
    if (topicId) params.set("topic_id", topicId);
    params.set("days", days);
    return request(`/api/v1/user/${userId}/matches?${params.toString()}`);
}


// ========================================
// Settings
// ========================================

export async function updateSettings(userId, emailEnabled, targetEmail) {
    return request(`/api/v1/user/${userId}/settings`, {
        method: "PUT",
        body: JSON.stringify({ email_enabled: emailEnabled, target_email: targetEmail }),
    });
}


// ========================================
// Jobs
// ========================================

export async function listJobs(limit = 20) {
    return request(`/api/v1/jobs?limit=${limit}`);
}

export async function enqueueJob(type, userId = null, payload = {}) {
    return request(`/api/v1/jobs/enqueue`, {
        method: "POST",
        body: JSON.stringify({ type, user_id: userId, payload }),
    });
}


// ========================================
// User Articles (Favorites, History)
// ========================================

export async function saveUserArticle(userId, doi, isFavorite, articleTitle = "") {
    return request(`/api/v1/user/${userId}/articles`, {
        method: "POST",
        body: JSON.stringify({ doi, is_favorite: isFavorite, article_title: articleTitle }),
    });
}

export async function listFavorites(userId) {
    return request(`/api/v1/user/${userId}/favorites`);
}

export async function listHistory(userId) {
    return request(`/api/v1/user/${userId}/history`);
}

export async function listUserArticles(userId, isFavorite = null, isRead = null) {
    const params = new URLSearchParams();
    if (isFavorite !== null) params.set("is_favorite", isFavorite);
    if (isRead !== null) params.set("is_read", isRead);
    return request(`/api/v1/user/${userId}/articles?${params.toString()}`);
}


// ========================================
// Reports
// ========================================

export async function listReports(userId, limit = 10) {
    return request(`/api/v1/user/${userId}/reports?limit=${limit}`);
}

export async function getReport(userId, reportId) {
    return request(`/api/v1/reports/${reportId}`);
}
