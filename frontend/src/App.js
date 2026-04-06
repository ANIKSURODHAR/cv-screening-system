import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import AdminDashboard from "./pages/AdminDashboard";
import RecruiterDashboard from "./pages/RecruiterDashboard";
import CandidateDashboard from "./pages/CandidateDashboard";

/** Protect routes based on authentication and role. */
function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: "#0a0e17", color: "#3b82f6", fontSize: 18, fontWeight: 700 }}>
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    // Redirect to their correct dashboard
    if (user?.role === "admin" || user?.is_superuser) return <Navigate to="/admin" replace />;
    if (user?.role === "recruiter") return <Navigate to="/recruiter" replace />;
    return <Navigate to="/candidate" replace />;
  }

  return children;
}

/** Redirect authenticated users away from login/register. */
function GuestRoute({ children }) {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) return null;

  if (isAuthenticated) {
    if (user?.role === "admin" || user?.is_superuser) return <Navigate to="/admin" replace />;
    if (user?.role === "recruiter") return <Navigate to="/recruiter" replace />;
    return <Navigate to="/candidate" replace />;
  }

  return children;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<GuestRoute><LoginPage /></GuestRoute>} />
      <Route path="/register" element={<GuestRoute><RegisterPage /></GuestRoute>} />

      {/* Admin */}
      <Route path="/admin" element={
        <ProtectedRoute allowedRoles={["admin"]}>
          <AdminDashboard />
        </ProtectedRoute>
      } />

      {/* Recruiter */}
      <Route path="/recruiter" element={
        <ProtectedRoute allowedRoles={["recruiter"]}>
          <RecruiterDashboard />
        </ProtectedRoute>
      } />

      {/* Candidate */}
      <Route path="/candidate" element={
        <ProtectedRoute allowedRoles={["candidate"]}>
          <CandidateDashboard />
        </ProtectedRoute>
      } />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
