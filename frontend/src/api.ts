const API_URL = "http://localhost:5000";

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

// Auth
export async function register(email: string, password: string) {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Registration failed");
  }

  return response.json();
}

export async function login(email: string, password: string) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Login failed");
  }

  return response.json();
}

// Interviews
export async function startInterview(stack: string, difficulty: string) {
  const response = await fetch(`${API_URL}/interviews/start`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ stack, difficulty }),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Failed to start interview");
  }

  return response.json();
}

export async function sendAnswer(interviewId: string, answer: string) {
  const response = await fetch(`${API_URL}/interviews/send`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ interview_id: interviewId, answer }),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Failed to send answer");
  }

  return response.json();
}

export async function getHint(interviewId: string) {
  const response = await fetch(`${API_URL}/interviews/hint`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ interview_id: interviewId }),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Failed to get hint");
  }

  return response.json();
}

export async function getUserInterviews() {
  const response = await fetch(`${API_URL}/interviews/my`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Failed to fetch interviews");
  }

  return response.json();
}

// Feedback
export async function generateFeedback(interviewId: string) {
  const response = await fetch(`${API_URL}/feedbacks/generate`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ interview_id: interviewId }),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Failed to generate feedback");
  }

  return response.json();
}


export async function submitMetrics(data: {
  interview_id: string;
  csat: number;
  ces: number;
  nps: number;
  comment?: string;
}) {
  const response = await fetch(`${API_URL}/metrics/submit`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to submit metrics");
  }

  return response.json();
}