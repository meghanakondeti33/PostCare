import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import type { User } from './types';
import { getStoredUser, clearAuthToken } from './services/api';
import { Navigation } from './components/Navigation';
import { LoginPage } from './pages/LoginPage';
import { PlatformAdminPage } from './pages/PlatformAdminPage';
import { HospitalAdminPage } from './pages/HospitalAdminPage';
import { CampaignManagerPage } from './pages/CampaignManagerPage';
import { ClinicalReviewerPage } from './pages/ClinicalReviewerPage';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(getStoredUser());

  const handleLogout = () => {
    clearAuthToken();
    setUser(null);
  };

  const getDefaultRoute = () => {
    if (!user) return '/login';
    switch (user.role) {
      case 'PLATFORM_ADMIN':
        return '/platform';
      case 'HOSPITAL_ADMIN':
        return '/hospital';
      case 'CAMPAIGN_MANAGER':
        return '/campaigns';
      case 'CLINICAL_REVIEWER':
        return '/review';
      default:
        return '/login';
    }
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        {user && <Navigation user={user} onLogout={handleLogout} />}

        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
          <Routes>
            <Route
              path="/login"
              element={!user ? <LoginPage onLoginSuccess={setUser} /> : <Navigate to={getDefaultRoute()} replace />}
            />

            {/* Platform Admin Routes */}
            <Route
              path="/platform/*"
              element={user?.role === 'PLATFORM_ADMIN' ? <PlatformAdminPage /> : <Navigate to={getDefaultRoute()} replace />}
            />

            {/* Hospital Admin Routes */}
            <Route
              path="/hospital/*"
              element={user?.role === 'HOSPITAL_ADMIN' || user?.role === 'PLATFORM_ADMIN' ? <HospitalAdminPage /> : <Navigate to={getDefaultRoute()} replace />}
            />

            {/* Campaign Manager Routes */}
            <Route
              path="/campaigns/*"
              element={user?.role === 'CAMPAIGN_MANAGER' || user?.role === 'HOSPITAL_ADMIN' || user?.role === 'PLATFORM_ADMIN' ? <CampaignManagerPage /> : <Navigate to={getDefaultRoute()} replace />}
            />
            <Route
              path="/queue"
              element={user?.role === 'CAMPAIGN_MANAGER' || user?.role === 'HOSPITAL_ADMIN' || user?.role === 'PLATFORM_ADMIN' ? <CampaignManagerPage /> : <Navigate to={getDefaultRoute()} replace />}
            />

            {/* Clinical Reviewer Routes */}
            <Route
              path="/review/*"
              element={user?.role === 'CLINICAL_REVIEWER' || user?.role === 'HOSPITAL_ADMIN' || user?.role === 'PLATFORM_ADMIN' ? <ClinicalReviewerPage /> : <Navigate to={getDefaultRoute()} replace />}
            />

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to={getDefaultRoute()} replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
