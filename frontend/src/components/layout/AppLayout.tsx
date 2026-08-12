import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../../modules/auth/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <div className="sidebar__title">BUYMA AI Platform</div>
          <div className="sidebar__subtitle">Admin MVP</div>
        </div>

        <nav className="sidebar__nav" aria-label="Main navigation">
          <NavLink
            to="/knowledge-bases"
            className={({ isActive }) =>
              `sidebar__link ${isActive ? "sidebar__link--active" : ""}`
            }
          >
            Knowledge Bases
          </NavLink>
          <button className="sidebar__link sidebar__link--disabled" disabled>
            Documents
          </button>
          <button className="sidebar__link sidebar__link--disabled" disabled>
            RAG（準備中）
          </button>
          <button className="sidebar__link sidebar__link--disabled" disabled>
            Settings（準備中）
          </button>
        </nav>
      </aside>

      <div className="app-main">
        <header className="app-header">
          <div>
            <div className="app-header__title">管理画面</div>
            {user ? (
              <div className="app-header__meta">
                {user.username} / {user.email}
              </div>
            ) : null}
          </div>
          <button className="secondary-button" onClick={() => void logout()}>
            Logout
          </button>
        </header>

        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
