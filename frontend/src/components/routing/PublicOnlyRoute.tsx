import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../../modules/auth/AuthContext";

export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { status } = useAuth();

  if (status === "loading") {
    return <div className="page-status">認証状態を確認しています...</div>;
  }

  if (status === "authenticated") {
    return <Navigate to="/knowledge-bases" replace />;
  }

  return <>{children}</>;
}
