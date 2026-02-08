import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

export function setAuthToken(token: string | null) {
  if (token) api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  else delete api.defaults.headers.common["Authorization"];
}
