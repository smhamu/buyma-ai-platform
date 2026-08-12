import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";

import { ApiClientError, configureApiClient } from "../../lib/api";
import {
  clearStoredTokens,
  getStoredTokens,
  setStoredTokens,
} from "../../lib/storage";
import {
  fetchCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  refreshAccessToken as refreshRequest,
} from "./api";
import type { CurrentUser, LoginRequest } from "./types";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  status: AuthStatus;
  user: CurrentUser | null;
  login: (payload: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(
    getStoredTokens()?.accessToken ?? null,
  );

  const clearAuth = useCallback(() => {
    clearStoredTokens();
    setAccessToken(null);
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const refreshAccessToken = useCallback(async () => {
    const stored = getStoredTokens();
    if (!stored?.refreshToken) {
      return null;
    }

    try {
      const refreshed = await refreshRequest({
        refresh_token: stored.refreshToken,
      });
      setStoredTokens({
        accessToken: refreshed.access_token,
        refreshToken: stored.refreshToken,
      });
      setAccessToken(refreshed.access_token);
      return refreshed.access_token;
    } catch {
      clearAuth();
      return null;
    }
  }, [clearAuth]);

  useEffect(() => {
    configureApiClient({
      getAccessToken: () => accessToken,
      refreshAccessToken,
      onUnauthorized: clearAuth,
    });
  }, [accessToken, refreshAccessToken, clearAuth]);

  useEffect(() => {
    const stored = getStoredTokens();
    if (!stored?.accessToken) {
      setStatus("unauthenticated");
      return;
    }

    let ignore = false;

    const bootstrap = async () => {
      try {
        const currentUser = await fetchCurrentUser();
        if (!ignore) {
          setUser(currentUser);
          setStatus("authenticated");
        }
      } catch (error) {
        if (error instanceof ApiClientError && error.status === 401) {
          const refreshed = await refreshAccessToken();
          if (refreshed && !ignore) {
            try {
              const currentUser = await fetchCurrentUser();
              if (!ignore) {
                setUser(currentUser);
                setStatus("authenticated");
              }
              return;
            } catch {
              // fall through
            }
          }
        }
        if (!ignore) {
          clearAuth();
        }
      }
    };

    void bootstrap();

    return () => {
      ignore = true;
    };
  }, [clearAuth, refreshAccessToken]);

  const login = useCallback(async (payload: LoginRequest) => {
    const token = await loginRequest(payload);
    setStoredTokens({
      accessToken: token.access_token,
      refreshToken: token.refresh_token,
    });
    setAccessToken(token.access_token);

    const currentUser = await fetchCurrentUser();
    setUser(currentUser);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    const stored = getStoredTokens();
    if (stored?.refreshToken) {
      try {
        await logoutRequest({ refresh_token: stored.refreshToken });
      } catch {
        // backend logout failure should not block client cleanup
      }
    }
    clearAuth();
  }, [clearAuth]);

  const value = useMemo(
    () => ({
      status,
      user,
      login,
      logout,
    }),
    [status, user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
