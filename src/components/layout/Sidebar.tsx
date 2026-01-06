import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  FolderKanban,
  FileText,
  CheckSquare,
  Bug,
  Rocket,
  Shield,
  Settings,
  Users,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Building2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Projects", href: "/projects", icon: FolderKanban },
  { name: "Requirements", href: "/requirements", icon: FileText },
  { name: "Test Cases", href: "/test-cases", icon: CheckSquare },
  { name: "Defects", href: "/defects", icon: Bug },
  { name: "Releases", href: "/releases", icon: Rocket },
];

const adminNavigation = [
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Compliance", href: "/compliance", icon: Shield },
  { name: "Team", href: "/team", icon: Users },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen bg-sidebar transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-4">
          {!collapsed && (
            <Link to="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-accent">
                <Shield className="h-5 w-5 text-sidebar-primary-foreground" />
              </div>
              <span className="text-lg font-bold text-sidebar-foreground">
                VeriShip
              </span>
            </Link>
          )}
          {collapsed && (
            <div className="mx-auto flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-accent">
              <Shield className="h-5 w-5 text-sidebar-primary-foreground" />
            </div>
          )}
        </div>

        {/* Organization Selector */}
        {!collapsed && (
          <div className="border-b border-sidebar-border p-4">
            <button className="flex w-full items-center gap-3 rounded-lg bg-sidebar-accent p-2.5 text-left transition-colors hover:bg-sidebar-accent/80">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-sidebar-primary/20">
                <Building2 className="h-4 w-4 text-sidebar-primary" />
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="truncate text-sm font-medium text-sidebar-foreground">
                  VeriShip Inc.
                </p>
                <p className="truncate text-xs text-sidebar-muted">
                  Enterprise Plan
                </p>
              </div>
            </button>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3">
          <div className="space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    "nav-item",
                    isActive && "nav-item-active"
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {!collapsed && <span>{item.name}</span>}
                </Link>
              );
            })}
          </div>

          {/* AI Assistant */}
          {!collapsed && (
            <div className="mt-6">
              <div className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-sidebar-muted">
                AI Assistant
              </div>
              <Link
                to="/copilot"
                className={cn(
                  "nav-item w-full group",
                  location.pathname === "/copilot" && "nav-item-active"
                )}
              >
                <div className="relative">
                  <Sparkles className="h-5 w-5 text-sidebar-primary" />
                  <span className="absolute -right-1 -top-1 flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sidebar-primary opacity-75"></span>
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-sidebar-primary"></span>
                  </span>
                </div>
                <span className="text-sidebar-foreground">Quality Copilot</span>
              </Link>
            </div>
          )}

          {/* Admin Section */}
          <div className="mt-6">
            {!collapsed && (
              <div className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-sidebar-muted">
                Administration
              </div>
            )}
            <div className="space-y-1">
              {adminNavigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={cn(
                      "nav-item",
                      isActive && "nav-item-active"
                    )}
                  >
                    <item.icon className="h-5 w-5 flex-shrink-0" />
                    {!collapsed && <span>{item.name}</span>}
                  </Link>
                );
              })}
            </div>
          </div>
        </nav>

        {/* Collapse Toggle */}
        <div className="border-t border-sidebar-border p-3">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="nav-item w-full justify-center"
          >
            {collapsed ? (
              <ChevronRight className="h-5 w-5" />
            ) : (
              <>
                <ChevronLeft className="h-5 w-5" />
                <span>Collapse</span>
              </>
            )}
          </button>
        </div>
      </div>
    </aside>
  );
}
