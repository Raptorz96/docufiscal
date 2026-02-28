# Sidebar Layout Design — 2026-02-28

## Goal
Add a persistent sidebar navigation to all protected pages of DocuFiscal.

## Architecture

**Pattern:** AppLayout with React Router v6 nested routes (Approach A)

- `src/layouts/AppLayout.tsx` — sidebar + `<Outlet />`
- `src/pages/DashboardPage.tsx` — extracts inline Dashboard from App.tsx
- `App.tsx` — updated with a protected route group wrapping AppLayout
- `backend/requirements.txt` — pin `bcrypt==4.0.1`

## Layout (Desktop)

```
+------------------+---------------------------+
|  DocuFiscal      |  [page content]           |
|  ─────────────   |                           |
|  Dashboard       |                           |
|  Clienti         |                           |
|  Contratti       |                           |
|                  |                           |
|  ─────────────   |                           |
|  Mario R.        |                           |
|  [Logout]        |                           |
+------------------+---------------------------+
```

- Sidebar: `w-64`, `bg-slate-800`, fixed left, full height
- Main content: `ml-64`, scrollable

## Layout (Mobile)

- Sidebar hidden by default
- Top bar with hamburger icon (`☰`) + app name
- Sidebar slides in as overlay on hamburger click
- Dark backdrop closes sidebar on click

## Sidebar Components

- **Logo/Brand:** "DocuFiscal" text top of sidebar
- **Nav links:** `NavLink` with active class `bg-slate-700 text-white`, inactive `text-slate-300 hover:bg-slate-700`
- **Icons:** simple SVG inline icons (no extra deps)
- **User section:** username from `useAuth()`, Logout button calls `authService.removeToken()` + navigates to /login

## Routing Change

Before:
```tsx
<Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
<Route path="/clienti" element={<ProtectedRoute><ClientiPage /></ProtectedRoute>} />
```

After:
```tsx
<Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
  <Route path="/" element={<DashboardPage />} />
  <Route path="/clienti" element={<ClientiPage />} />
  <Route path="/contratti" element={<ContrattiPage />} />
</Route>
<Route path="/login" element={<LoginPage />} />
```

## Colors
- Sidebar bg: `slate-800`
- Active link: `slate-700` bg + `white` text
- Inactive link: `slate-300` text + `slate-700` hover
- Main bg: `gray-50`
- Top bar (mobile): `slate-800`
