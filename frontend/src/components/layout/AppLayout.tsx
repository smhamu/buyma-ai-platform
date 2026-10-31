import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../../modules/auth/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <div className="sidebar__title">BUYMA AI Platform</div>
          <div className="sidebar__subtitle">管理コンソール MVP</div>
        </div>

        <nav className="sidebar__nav" aria-label="メインナビゲーション">
          <NavLink
            to="/knowledge-bases"
            className={({ isActive }) =>
              `sidebar__link ${isActive ? "sidebar__link--active" : ""}`
            }
          >
            ナレッジベース
          </NavLink>
          <div className="sidebar__section">ラグジュアリー商品リサーチ</div>
          <NavLink to="/research-ingestion" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>リサーチ取込</NavLink>
          <NavLink to="/product-research" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>商品リサーチ候補</NavLink>
          <NavLink to="/suppliers" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>仕入先</NavLink>
          <NavLink to="/supplier-policy-review" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>ポリシーレビュー</NavLink>
          <NavLink to="/brands" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>ブランド</NavLink>
          <div className="sidebar__section">アカウント</div>
          <NavLink to="/notification-settings" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>通知設定</NavLink>
          {user?.role === "admin" && <NavLink to="/integration-settings" className={({isActive})=>`sidebar__link ${isActive?"sidebar__link--active":""}`}>外部サービス連携</NavLink>}
        </nav>
      </aside>

      <div className="app-main">
        <header className="app-header">
          <div>
            <div className="app-header__title">管理コンソール</div>
            {user ? (
              <div className="app-header__meta">
                {user.username} · {user.email}
              </div>
            ) : null}
          </div>
          <button className="secondary-button" onClick={() => void logout()}>
            ログアウト
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
