import { Bell, Search, HelpCircle, User, LogOut, Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useNavigate } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { useTheme } from "@/hooks/use-theme";

interface UserInfo {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
}

export function Header() {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserInfo | null>(null);

  useEffect(() => {
    // Get user from localStorage
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        setUser(JSON.parse(userStr));
      } catch (err) {
        console.error("Error parsing user:", err);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("user");
    toast.success("Logged out successfully!");
    navigate("/login");
  };

  const [searchQuery, setSearchQuery] = useState<string>("");
  const searchTimeout = useRef<number | null>(null);
  const { theme, toggle } = useTheme();

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    if (searchTimeout.current) {
      window.clearTimeout(searchTimeout.current);
    }
    // debounce dispatch
    searchTimeout.current = window.setTimeout(() => {
      try {
        window.dispatchEvent(new CustomEvent("globalSearch", { detail: value }));
      } catch (err) {
        // ignore in environments that restrict CustomEvent
      }
    }, 300) as unknown as number;
  };

  useEffect(() => {
    return () => {
      if (searchTimeout.current) window.clearTimeout(searchTimeout.current);
    };
  }, []);

  const handleProfileClick = () => {
    navigate("/profile");
  };

  const displayName =
    user && (user.first_name || user.last_name)
      ? `${user.first_name || ""} ${user.last_name || ""}`.trim()
      : user?.username || "User";

  const initials =
    displayName
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase() || "U";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Search projects, requirements, tests..."
          value={searchQuery}
          onChange={handleSearchChange}
          className="pl-10 bg-muted/50 border-0 focus-visible:ring-1 focus-visible:ring-accent"
        />
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="text-muted-foreground">
          <HelpCircle className="h-5 w-5" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground"
          onClick={() => toggle()}
          aria-label="Toggle theme"
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </Button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative text-muted-foreground">
              <Bell className="h-5 w-5" />
              <span className="absolute right-1.5 top-1.5 flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-accent"></span>
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="flex flex-col items-start gap-1 p-3">
              <p className="text-sm font-medium">Release v2.4.0 Ready for Review</p>
              <p className="text-xs text-muted-foreground">Project Alpha requires your approval</p>
            </DropdownMenuItem>
            <DropdownMenuItem className="flex flex-col items-start gap-1 p-3">
              <p className="text-sm font-medium">3 New Defects Reported</p>
              <p className="text-xs text-muted-foreground">High severity issues in Project Beta</p>
            </DropdownMenuItem>
            <DropdownMenuItem className="flex flex-col items-start gap-1 p-3">
              <p className="text-sm font-medium">AI Analysis Complete</p>
              <p className="text-xs text-muted-foreground">15 requirements reviewed with suggestions</p>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-9 w-9 rounded-full">
              <Avatar className="h-9 w-9">
                <AvatarImage src="/placeholder.svg" alt={displayName} />
                <AvatarFallback className="bg-accent text-accent-foreground">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">{displayName}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleProfileClick}>
              <User className="mr-2 h-4 w-4" />
              My Profile
            </DropdownMenuItem>
            <DropdownMenuItem>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-destructive">
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
