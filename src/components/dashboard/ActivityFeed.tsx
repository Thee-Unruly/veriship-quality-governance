import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  CheckCircle2,
  FileText,
  Bug,
  Rocket,
  Sparkles,
  AlertTriangle,
} from "lucide-react";

interface Activity {
  id: string | number;
  type: "approval" | "requirement" | "defect" | "release" | "ai" | "alert" | "requirement_created" | "defect_created" | "release_created" | "test_executed";
  user: {
    name: string;
    avatar?: string;
  };
  action: string;
  target: string;
  project: string;
  timestamp: string | Date;
}

interface ActivityFeedProps {
  activities?: Activity[];
}

function getRelativeTime(date: Date): string {
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

const activities: Activity[] = [
  {
    id: "1",
    type: "approval",
    user: { name: "Sarah Chen" },
    action: "approved release",
    target: "v2.4.0",
    project: "Project Alpha",
    timestamp: "5 min ago",
  },
  {
    id: "2",
    type: "ai",
    user: { name: "Quality Copilot" },
    action: "analyzed",
    target: "15 requirements",
    project: "Project Beta",
    timestamp: "12 min ago",
  },
  {
    id: "3",
    type: "defect",
    user: { name: "Mike Johnson" },
    action: "reported critical defect",
    target: "DEF-1234",
    project: "Project Alpha",
    timestamp: "25 min ago",
  },
  {
    id: "4",
    type: "requirement",
    user: { name: "Lisa Park" },
    action: "updated requirement",
    target: "REQ-567",
    project: "Project Gamma",
    timestamp: "1 hour ago",
  },
  {
    id: "5",
    type: "alert",
    user: { name: "System" },
    action: "flagged risk threshold exceeded in",
    target: "Release v1.8.0",
    project: "Project Beta",
    timestamp: "2 hours ago",
  },
];

const getTypeConfig = (type: string) => {
  switch (type) {
    case "approval":
      return { icon: CheckCircle2, class: "bg-success/10 text-success" };
    case "requirement":
    case "requirement_created":
      return { icon: FileText, class: "bg-accent/10 text-accent" };
    case "defect":
    case "defect_created":
      return { icon: Bug, class: "bg-destructive/10 text-destructive" };
    case "release":
    case "release_created":
      return { icon: Rocket, class: "bg-info/10 text-info" };
    case "ai":
      return { icon: Sparkles, class: "bg-chart-5/10 text-chart-5" };
    case "alert":
      return { icon: AlertTriangle, class: "bg-warning/10 text-warning" };
    case "test_executed":
      return { icon: CheckCircle2, class: "bg-success/10 text-success" };
    default:
      return { icon: FileText, class: "bg-muted text-muted-foreground" };
  }
};

export function ActivityFeed({ activities = [] }: ActivityFeedProps) {
  const defaultActivities: Activity[] = [
    {
      id: "1",
      type: "approval",
      user: { name: "Sarah Chen" },
      action: "approved release",
      target: "v2.4.0",
      project: "Project Alpha",
      timestamp: "5 min ago",
    },
    {
      id: "2",
      type: "ai",
      user: { name: "Quality Copilot" },
      action: "analyzed",
      target: "15 requirements",
      project: "Project Beta",
      timestamp: "12 min ago",
    },
    {
      id: "3",
      type: "defect",
      user: { name: "Mike Johnson" },
      action: "reported critical defect",
      target: "DEF-1234",
      project: "Project Alpha",
      timestamp: "25 min ago",
    },
    {
      id: "4",
      type: "requirement",
      user: { name: "Lisa Park" },
      action: "updated requirement",
      target: "REQ-567",
      project: "Project Gamma",
      timestamp: "1 hour ago",
    },
    {
      id: "5",
      type: "alert",
      user: { name: "System" },
      action: "flagged risk threshold exceeded in",
      target: "Release v1.8.0",
      project: "Project Beta",
      timestamp: "2 hours ago",
    },
  ];

  const displayActivities = activities.length > 0 ? activities : defaultActivities;
  return (
    <div className="metric-card">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Recent Activity</h3>
          <p className="text-sm text-muted-foreground">
            Latest updates across all projects
          </p>
        </div>
        <button className="text-sm font-medium text-accent hover:underline">
          View all
        </button>
      </div>

      <div className="space-y-4">
        {displayActivities.map((activity) => {
          const config = getTypeConfig(activity.type);
          const Icon = config.icon;
          const timeStr = typeof activity.timestamp === 'string'
            ? activity.timestamp
            : activity.timestamp instanceof Date
              ? getRelativeTime(activity.timestamp)
              : 'just now';

          return (
            <div key={activity.id} className="flex gap-3">
              <div className={cn("mt-0.5 flex h-8 w-8 items-center justify-center rounded-full", config.class)}>
                <Icon className="h-4 w-4" />
              </div>
              <div className="flex-1 space-y-1">
                <p className="text-sm text-foreground">
                  <span className="font-medium">{activity.user.name}</span>{" "}
                  {activity.action}{" "}
                  <span className="font-medium text-accent">{activity.target}</span>
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{activity.project}</span>
                  <span>•</span>
                  <span>{timeStr}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
