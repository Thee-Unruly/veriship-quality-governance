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
  TrendingUp,
} from "lucide-react";

const mockApprovers = [
  {
    id: "1",
    name: "Sarah Chen",
    role: "QA Lead",
    status: "approved" as const,
    timestamp: "Jan 5, 10:23 AM",
  },
  {
    id: "2",
    name: "Michael Torres",
    role: "Product Manager",
    status: "pending" as const,
  },
  {
    id: "3",
    name: "Jennifer Liu",
    role: "Engineering Lead",
    status: "pending" as const,
  },
];

export default function Index() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch projects from backend
    fetch("http://localhost:8000/api/projects/")
      .then((res) => res.json())
      .then((data) => {
        setProjects(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching projects:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;

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
            Last updated: 2 min ago
          </div>
        </div>

        {/* Top Metrics Row */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Requirements"
            value={projects.length * 5} // 5 requirements per project
            subtitle={`across ${projects.length} projects`}
            trend={{ value: 12, label: "this month" }}
            icon={<FileText className="h-5 w-5 text-muted-foreground" />}
          />
          <MetricCard
            title="Test Cases"
            value={projects.length * 15} // 15 test cases per project
            subtitle="85% automated"
            trend={{ value: 8, label: "this month" }}
            icon={<CheckSquare className="h-5 w-5 text-muted-foreground" />}
          />
          <MetricCard
            title="Open Defects"
            value={projects.length * 10} // 10 defects per project
            subtitle="7 critical"
            trend={{ value: -15, label: "vs last week" }}
            icon={<Bug className="h-5 w-5 text-muted-foreground" />}
            variant="warning"
          />
          <MetricCard
            title="Pending Releases"
            value={projects.length}
            subtitle="2 ready for approval"
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
                  Aggregate risk scores across all active projects
                </p>
              </div>
              <div className="flex items-center justify-around">
                <RiskGauge score={32} label="Overall Risk Index" size="lg" />
                <div className="h-32 w-px bg-border" />
                <div className="grid grid-cols-2 gap-6">
                  <RiskGauge score={28} label="Quality Coverage" size="sm" />
                  <RiskGauge score={42} label="Defect Density" size="sm" />
                  <RiskGauge score={18} label="Compliance" size="sm" />
                  <RiskGauge score={35} label="Release Readiness" size="sm" />
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
                    id={project.id}
                    name={project.name}
                    description={project.description}
                    riskScore={45} // Can add to backend later
                    coveragePercent={85}
                    defectsOpen={12}
                    releaseDate={new Date(
                      project.target_release_date
                    ).toLocaleDateString()}
                    team={3}
                    status={project.status}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Approvals, Activity, AI */}
          <div className="space-y-6">
            {/* Release Approval */}
            <ReleaseApprovalCard
              version="v2.4.0"
              project="Project Alpha"
              releaseDate="Jan 15, 2026"
              riskScore={28}
              status="pending"
              approvers={mockApprovers}
            />

            {/* AI Insights */}
            <AIInsightsPanel />

            {/* Activity Feed */}
            <ActivityFeed />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
