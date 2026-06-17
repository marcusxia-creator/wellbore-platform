const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchWells(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item) params.append(key, item);
      });
    } else if (value) {
      params.set(key, value);
    }
  });
  const query = params.toString();
  return request(`/wells/${query ? `?${query}` : ""}`);
}

export async function fetchWellStatuses() {
  return request("/well-statuses/");
}

export async function fetchActualWellStatuses(status) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  const query = params.toString();
  return request(`/actual-well-statuses/${query ? `?${query}` : ""}`);
}

export async function fetchWellTypes() {
  return request("/well-types/");
}

export async function fetchProductionInjectionFormations() {
  return request("/production-injection-formations/");
}
