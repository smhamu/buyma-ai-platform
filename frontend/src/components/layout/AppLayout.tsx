import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../../modules/auth/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <div className="sidebar__title">BUYMA AI Platform</div>
          <div className="sidebar__subtitle">Admin Console MVP</div>
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
          <div className="sidebar__section">Luxury Research</div>
          <NavLink to="/research-ingestion" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>Research Ingestion</NavLink>
          <NavLink to="/product-research" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>Research Candidates</NavLink>
          <NavLink to="/suppliers" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>Suppliers</NavLink>
          <NavLink to="/supplier-policy-review" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>Policy Review</NavLink>
          <NavLink to="/brands" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>Brands</NavLink>
          <div className="sidebar__section">Account</div>
          <NavLink to="/notification-settings" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>Notification Settings</NavLink>
        </nav>
      </aside>

      <div className="app-main">
        <header className="app-header">
          <div>
            <div className="app-header__title">Management Console</div>
            {user ? (
              <div className="app-header__meta">
                {user.username} · {user.email}
              </div>
            ) : null}
          </div>
          <button className="secondary-button" onClick={() => void logout()}>
            Logout
          </button>
        </header>

        <main className="content">
          <div className="content__inner">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
