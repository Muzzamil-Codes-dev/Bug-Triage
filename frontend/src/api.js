// Thin client for the FastAPI backend. Paths are relative: the app is
// served by FastAPI in production and proxied by Vite in development.

async function request(method, path, body) {
  let response;
  try {
    response = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Could not reach the server. Is it still running?");
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(errorMessage(response, data));
    error.status = response.status;
    throw error;
  }
  return data;
}

function errorMessage(response, data) {
  const detail = data?.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg.replace(/^Value error, /, "")).join("; ");
  }
  if (response.status >= 500) {
    return `The server hit an error (${response.status}). Check the terminal running the server for details.`;
  }
  return `Request failed (${response.status} ${response.statusText}).`;
}

export function createTriage(bugReport) {
  return request("POST", "/bug-triage", { bug_report: bugReport });
}

export function getTriage(threadId) {
  return request("GET", `/bug-triage/${encodeURIComponent(threadId)}`);
}

export function submitReview(threadId, decision, feedback) {
  return request("POST", "/bug-review", {
    thread_id: threadId,
    decision,
    feedback: feedback || null,
  });
}
