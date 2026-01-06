import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import Index from "./pages/Index";
import Projects from "./pages/Projects";
import Requirements from "./pages/Requirements";
import TestCases from "./pages/TestCases";
import Defects from "./pages/Defects";
import Releases from "./pages/Releases";
import Analytics from "./pages/Analytics";
import Compliance from "./pages/Compliance";
import Team from "./pages/Team";
import Settings from "./pages/Settings";
import Copilot from "./pages/Copilot";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

// Protected route component
interface ProtectedRouteProps {
  element: React.ReactNode;
}

const ProtectedRoute = ({ element }: ProtectedRouteProps) => {
  const token = localStorage.getItem("authToken");
  return token ? <>{element}</> : <Navigate to="/login" replace />;
};

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("authToken"));

  useEffect(() => {
    // Listen for storage changes (logout from another tab)
    const handleStorageChange = () => {
      setIsAuthenticated(!!localStorage.getItem("authToken"));
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<ProtectedRoute element={<Index />} />} />
            <Route path="/projects" element={<ProtectedRoute element={<Projects />} />} />
            <Route path="/requirements" element={<ProtectedRoute element={<Requirements />} />} />
            <Route path="/test-cases" element={<ProtectedRoute element={<TestCases />} />} />
            <Route path="/defects" element={<ProtectedRoute element={<Defects />} />} />
            <Route path="/releases" element={<ProtectedRoute element={<Releases />} />} />
            <Route path="/analytics" element={<ProtectedRoute element={<Analytics />} />} />
            <Route path="/compliance" element={<ProtectedRoute element={<Compliance />} />} />
            <Route path="/team" element={<ProtectedRoute element={<Team />} />} />
            <Route path="/settings" element={<ProtectedRoute element={<Settings />} />} />
            <Route path="/copilot" element={<ProtectedRoute element={<Copilot />} />} />
            <Route path="/profile" element={<ProtectedRoute element={<Profile />} />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
