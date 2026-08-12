import { apiClient } from "../../lib/api";
import type {
  CurrentUser,
  LoginRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  TokenResponse,
} from "./types";

export function login(payload: LoginRequest) {
  return apiClient.post<TokenResponse, LoginRequest>("/auth/login", payload);
}

export function fetchCurrentUser() {
  return apiClient.get<CurrentUser>("/auth/me");
}

export function refreshAccessToken(payload: RefreshTokenRequest) {
  return apiClient.post<RefreshTokenResponse, RefreshTokenRequest>(
    "/auth/refresh",
    payload,
  );
}

export function logout(payload: RefreshTokenRequest) {
  return apiClient.post<{ message: string }, RefreshTokenRequest>(
    "/auth/logout",
    payload,
  );
}
