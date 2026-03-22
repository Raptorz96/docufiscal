import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './layouts/AppLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import { ClientiPage } from './pages/ClientiPage';
import { ContrattiPage } from './pages/ContrattiPage';
import { DocumentiPage } from './pages/DocumentiPage';
import ProfilePage from './pages/ProfilePage';
import { DocumentProvider } from './context/DocumentContext';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <DocumentProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
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
              <Route path="/documenti" element={<DocumentiPage />} />
              <Route path="/profilo" element={<ProfilePage />} />
            </Route>
          </Routes>
        </Router>
      </DocumentProvider>
    </AuthProvider>
  );
}

export default App;
