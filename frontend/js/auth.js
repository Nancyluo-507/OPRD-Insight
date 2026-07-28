// Auth module — handles login/register/token

const API = "";

export function getToken() {
    return localStorage.getItem("chemvigil_token");
}

export function getUserId() {
    const uid = localStorage.getItem("chemvigil_user_id");
    return uid ? parseInt(uid) : null;
}

export function getUserName() {
    return localStorage.getItem("chemvigil_user_name") || "";
}

export function isLoggedIn() {
    return !!getToken();
}

export async function login(name, password) {
    const resp = await fetch(`${API}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, password }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "Login failed");
    localStorage.setItem("chemvigil_token", data.token);
    localStorage.setItem("chemvigil_user_id", data.user.id);
    localStorage.setItem("chemvigil_user_name", data.user.name);
    return data.user;
}

export async function register(name, password, email) {
    const resp = await fetch(`${API}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, password, email }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "Registration failed");
    localStorage.setItem("chemvigil_token", data.token);
    localStorage.setItem("chemvigil_user_id", data.user.id);
    localStorage.setItem("chemvigil_user_name", data.user.name);
    return data.user;
}

export function logout() {
    localStorage.removeItem("chemvigil_token");
    localStorage.removeItem("chemvigil_user_id");
    localStorage.removeItem("chemvigil_user_name");
}

export function authHeaders() {
    const token = getToken();
    return token ? { "Authorization": `Bearer ${token}` } : {};
}
