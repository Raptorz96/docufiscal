# Sidebar Layout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a responsive sidebar navigation to all protected pages, wrapping them in a shared AppLayout.

**Architecture:** Create `AppLayout.tsx` with a fixed left sidebar and `<Outlet />` for page content. Use a React Router v6 nested route group so all protected pages share the layout. Login page remains standalone. No new dependencies needed.

**Tech Stack:** React 19, React Router DOM v7, TailwindCSS 3, TypeScript 5.9 with `verbatimModuleSyntax: true` (use `import type` for all type-only imports)

---

### Task 1: Pin bcrypt in backend requirements.txt

**Files:**
- Modify: `../backend/requirements.txt`

**Step 1: Update requirements.txt**

Replace the line `passlib[bcrypt]` with:
```
passlib[bcrypt]
bcrypt==4.0.1
```

File result:
```
fastapi
uvicorn[standard]
sqlalchemy
alembic
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
bcrypt==4.0.1
python-multipart
python-dotenv
email-validator
psycopg2-binary
```

**Step 2: Commit**
```bash
git add ../backend/requirements.txt
git commit -m "fix: pin bcrypt==4.0.1 for passlib compatibility"
```

---

### Task 2: Extract DashboardPage

**Files:**
- Create: `src/pages/DashboardPage.tsx`
- Modify: `src/App.tsx` (remove inline Dashboard component, import DashboardPage)

**Step 1: Create `src/pages/DashboardPage.tsx`**

```tsx
const DashboardPage: React.FC = () => {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
    </div>
  );
};

export default DashboardPage;
```

Full file content:
```tsx
import React from 'react';

const DashboardPage: React.FC = () => {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
    </div>
  );
};

export default DashboardPage;
```

**Step 2: Verify dev server still compiles** (check no TS errors in terminal)

**Step 3: Commit**
```bash
git add src/pages/DashboardPage.tsx
git commit -m "feat: extract DashboardPage from App.tsx"
```

---

### Task 3: Create AppLayout with sidebar

**Files:**
- Create: `src/layouts/AppLayout.tsx`

This is the main task. The component manages:
- `sidebarOpen: boolean` state for mobile toggle
- Sidebar markup (desktop always visible, mobile slide-in overlay)
- `<Outlet />` for nested route content

**Step 1: Create `src/layouts/AppLayout.tsx`**

Full file content:
```tsx
import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import * as authService from '../services/authService';

interface NavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    to: '/',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    label: 'Clienti',
    to: '/clienti',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    label: 'Contratti',
    to: '/contratti',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
];

const activeLinkClass = 'flex items-center gap-3 px-4 py-2.5 rounded-lg bg-slate-700 text-white font-medium';
const inactiveLinkClass = 'flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-300 hover:bg-slate-700 hover:text-white transition-colors';

const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    authService.removeToken();
    navigate('/login');
  };

  const displayName = user ? `${user.nome} ${user.cognome}` : '';

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Brand */}
      <div className="px-6 py-5 border-b border-slate-700">
        <span className="text-white font-bold text-lg tracking-tight">DocuFiscal</span>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => isActive ? activeLinkClass : inactiveLinkClass}
            onClick={() => setSidebarOpen(false)}
          >
            {item.icon}
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User + Logout */}
      <div className="px-3 py-4 border-t border-slate-700">
        <div className="flex items-center gap-3 px-4 py-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-white text-sm font-semibold">
            {user?.nome?.[0]?.toUpperCase() ?? '?'}
          </div>
          <span className="text-slate-300 text-sm truncate">{displayName}</span>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-300 hover:bg-red-600 hover:text-white transition-colors text-sm"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span>Logout</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:flex-col w-64 bg-slate-800 flex-shrink-0">
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black bg-opacity-50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-slate-800 flex flex-col transform transition-transform duration-200 md:hidden ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {sidebarContent}
      </aside>

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Mobile top bar */}
        <header className="md:hidden flex items-center gap-4 px-4 py-3 bg-slate-800 text-white flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-1 rounded hover:bg-slate-700 transition-colors"
            aria-label="Apri menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <span className="font-bold tracking-tight">DocuFiscal</span>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
```

**Step 2: Verify TypeScript compiles** — check terminal for TS errors

**Step 3: Commit**
```bash
git add src/layouts/AppLayout.tsx
git commit -m "feat: add AppLayout with responsive sidebar"
```

---

### Task 4: Wire AppLayout into App.tsx routing

**Files:**
- Modify: `src/App.tsx`

**Step 1: Update App.tsx**

Replace entire file content with:
```tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './layouts/AppLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import { ClientiPage } from './pages/ClientiPage';
import { ContrattiPage } from './pages/ContrattiPage';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/clienti" element={<ClientiPage />} />
            <Route path="/contratti" element={<ContrattiPage />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
```

**Key change:** `ProtectedRoute` now wraps `AppLayout` (which renders `<Outlet />`). All protected pages are children of that route — no per-route wrapping.

**Step 2: Verify in browser**
- Navigate to `/` → sidebar visible, Dashboard content shown
- Navigate to `/clienti` → Clienti link highlighted in sidebar
- Resize to mobile → hamburger appears, sidebar slides in/out
- Logout button works
- Direct `/login` access has no sidebar

**Step 3: Commit**
```bash
git add src/App.tsx src/pages/DashboardPage.tsx
git commit -m "feat: wire AppLayout with nested routes, extract DashboardPage"
```

---

## Done

Total files changed: 5
- `../backend/requirements.txt` — bcrypt pinned
- `src/pages/DashboardPage.tsx` — new
- `src/layouts/AppLayout.tsx` — new
- `src/App.tsx` — updated routing
- `src/pages/DashboardPage.tsx` (committed with App.tsx update)
