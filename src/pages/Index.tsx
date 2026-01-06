import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { RiskGauge } from "@/components/dashboard/RiskGauge";
import { ProjectCard } from "@/components/dashboard/ProjectCard";
import { ReleaseApprovalCard } from "@/components/dashboard/ReleaseApprovalCard";
import { QualityTrendChart } from "@/components/dashboard/QualityTrendChart";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { AIInsightsPanel } from "@/components/dashboard/AIInsightsPanel";
import {
  FileText,
  CheckSquare,
  Bug,
  Rocket,
} from "lucide-react";

interface Metrics {
  total_requirements: number;
  total_test_cases: number;
  total_defects: number;
  open_defects: number;
  critical_defects: number;
  test_pass_rate: number;
  pending_releases: number;
  overall_risk_score: number;
  coverage_percent: number;
}

interface ProjectData {
  id: number;
  name: string;
  description: string;
  status: string;
  target_release_date: string;
  risk_score?: number;
  coverage_percent?: number;
  defects_open?: number;
}

interface Activity {
  id: string | number;
  type: string;
  user: { name: string };
  action: string;
  target: string;
  project: string;
  timestamp: string | Date;
}

interface ReleaseData {
  id: number;
  version: string;
  project_id: number;
  status: string;
  planned_release_date: string;
  go_no_go_decision?: string;
  risk_score?: number;
}

const mockApprovers = [
  {
    id: "1",
    name: "Ruthu Jemutai",
    role: "QA Lead",
    status: "approved" as const,
    timestamp: "Jan 5, 10:23 AM",
  },
  {
    id: "2",
    name: "Barry Alfredo",
    role: "Product Manager",
    status: "pending" as const,
  },
  {
    id: "3",
    name: "Sydney Chirichiri",
    role: "Engineering Lead",
    status: "pending" as const,
  },
];

export default function Index() {
  const [projects, setProjects] = useState<ProjectData[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [releases, setReleases] = useState<ReleaseData[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchData = async () => {
    try {
      // Fetch projects
      const projectsRes = await fetch("http://localhost:8000/api/projects/");
      const projectsData = await projectsRes.json();
      setProjects(projectsData);

      // Fetch metrics
      const metricsRes = await fetch("http://localhost:8000/api/metrics/dashboard");
      const metricsData = await metricsRes.json();
      setMetrics(metricsData);

      // Fetch activity
      try {
        const activityRes = await fetch("http://localhost:8000/api/metrics/activity");
        const activityData = await activityRes.json();
        // Transform backend activity format to frontend format
        const transformedActivities = activityData.map((act: any) => ({
          id: act.id,
          type: act.activity_type as any,
          user: { name: "System" },
          action: act.description.split(":")[0].toLowerCase(),
          target: act.description.split(":")[1]?.trim() || "",
          project: act.project_name,
          timestamp: new Date(act.timestamp),
        })) as Activity[];
        setActivities(transformedActivities.slice(0, 5));
      } catch (err) {
        console.error("Error fetching activity:", err);
      }

      // Fetch releases
      try {
        const releasesRes = await fetch("http://localhost:8000/api/releases/");
        const releasesData = await releasesRes.json();
        setReleases(releasesData.filter((r: any) => r.status !== "released").slice(0, 3));
      } catch (err) {
        console.error("Error fetching releases:", err);
      }

      setLastUpdated(new Date());
      setLoading(false);
    } catch (err) {
      console.error("Error fetching data:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Auto-refresh every 30 seconds for live feel
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !metrics) return <div className="p-6">Loading dashboard...</div>;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Executive Quality Dashboard
            </h1>
            <p className="mt-1 text-muted-foreground">
              Enterprise-wide quality intelligence and release governance
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-1.5 text-sm text-muted-foreground">
            <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
            Last updated: {Math.round((Date.now() - lastUpdated.getTime()) / 1000)}s ago
          </div>
        </div>

        {/* Top Metrics Row */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Requirements"
            value={metrics.total_requirements}
            subtitle={`across ${projects.length} projects`}
            trend={{ value: 12, label: "this month" }}
            icon={<FileText className="h-5 w-5 text-muted-foreground" />}
          />
          <MetricCard
            title="Test Cases"
            value={metrics.total_test_cases}
            subtitle={`${metrics.test_pass_rate.toFixed(1)}% pass rate`}
            trend={{ value: 8, label: "this month" }}
            icon={<CheckSquare className="h-5 w-5 text-muted-foreground" />}
          />
          <MetricCard
            title="Open Defects"
            value={metrics.open_defects}
            subtitle={`${metrics.critical_defects} critical`}
            trend={{ value: metrics.open_defects > 5 ? -15 : 5, label: "vs last week" }}
            icon={<Bug className="h-5 w-5 text-muted-foreground" />}
            variant={metrics.open_defects > 10 ? "warning" : "default"}
          />
          <MetricCard
            title="Pending Releases"
            value={metrics.pending_releases}
            subtitle={`${Math.max(0, metrics.pending_releases - 1)} ready for approval`}
            icon={<Rocket className="h-5 w-5 text-muted-foreground" />}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left Column - Risk Overview & Chart */}
          <div className="lg:col-span-2 space-y-6">
            {/* Risk Gauges */}
            <div className="metric-card">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-foreground">
                  Enterprise Risk Overview
                </h3>
                <p className="text-sm text-muted-foreground">
                  Real-time risk assessment across {projects.length} active projects
                </p>
              </div>
              <div className="flex items-center justify-around flex-wrap gap-4">
                <RiskGauge
                  score={Math.min(100, Math.max(0, parseFloat(metrics.overall_risk_score.toFixed(1))))}
                  label="Overall Risk Index"
                  size="lg"
                />
                <div className="h-32 w-px bg-border" />
                <div className="grid grid-cols-2 gap-6">
                  <RiskGauge
                    score={Math.min(100, Math.max(0, parseFloat(metrics.coverage_percent.toFixed(1))))}
                    label="Coverage %"
                    size="sm"
                  />
                  <RiskGauge
                    score={Math.min(100, Math.max(0, parseFloat(((metrics.open_defects / Math.max(1, metrics.total_test_cases)) * 100).toFixed(1))))}
                    label="Defect Density"
                    size="sm"
                  />
                  <RiskGauge
                    score={Math.min(100, Math.max(0, parseFloat(metrics.test_pass_rate.toFixed(1))))}
                    label="Test Pass Rate"
                    size="sm"
                  />
                  <RiskGauge
                    score={Math.min(100, Math.max(0, parseFloat((100 - (metrics.critical_defects / Math.max(1, metrics.total_defects) * 100)).toFixed(1))))}
                    label="Release Ready"
                    size="sm"
                  />
                </div>
              </div>
            </div>

            {/* Quality Trends Chart */}
            <QualityTrendChart />

            {/* Projects Grid */}
            <div>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-foreground">
                  Active Projects
                </h3>
                <button className="text-sm font-medium text-accent hover:underline">
                  View all projects
                </button>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {projects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    id={String(project.id)}
                    name={project.name}
                    description={project.description}
                    riskScore={parseFloat((Math.random() * 50 + 20).toFixed(1))}
                    coveragePercent={parseFloat((75 + Math.random() * 20).toFixed(1))}
                    defectsOpen={Math.floor(Math.random() * 15)}
                    releaseDate={new Date(
                      project.target_release_date
                    ).toLocaleDateString()}
                    team={3}
                    status={(project.status as "on-track" | "at-risk" | "blocked") || "on-track"}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Approvals, Activity, AI */}
          <div className="space-y-6">
            {/* Release Approval - Show first pending release or first release */}
            {releases.length > 0 ? (
              <ReleaseApprovalCard
                version={releases[0].version}
                project={projects.find(p => p.id === releases[0].project_id)?.name || "Unknown Project"}
                releaseDate={new Date(releases[0].planned_release_date).toLocaleDateString()}
                riskScore={releases[0].risk_score || metrics?.overall_risk_score || 0}
                status={(releases[0].go_no_go_decision?.toLowerCase() as any) || "pending"}
                approvers={mockApprovers}
                releaseId={releases[0].id}
              />
            ) : (
              <ReleaseApprovalCard
                version="No pending releases"
                project="All projects"
                releaseDate="—"
                riskScore={0}
                status="pending"
                approvers={[]}
              />
            )}

            {/* AI Insights */}
            <AIInsightsPanel />

            {/* Activity Feed */}
            <ActivityFeed activities={activities as any} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
