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

const mockProjects = [
  {
    id: "1",
    name: "Project Alpha",
    description: "Core banking platform modernization with regulatory compliance requirements",
    riskScore: 28,
    coveragePercent: 87,
    defectsOpen: 12,
    releaseDate: "Jan 15, 2026",
    team: 8,
    status: "on-track" as const,
  },
  {
    id: "2",
    name: "Project Beta",
    description: "Customer-facing mobile application with real-time transaction processing",
    riskScore: 54,
    coveragePercent: 72,
    defectsOpen: 24,
    releaseDate: "Feb 28, 2026",
    team: 12,
    status: "at-risk" as const,
  },
  {
    id: "3",
    name: "Project Gamma",
    description: "Internal risk management dashboard and reporting suite",
    riskScore: 15,
    coveragePercent: 94,
    defectsOpen: 3,
    releaseDate: "Jan 8, 2026",
    team: 5,
    status: "on-track" as const,
  },
];

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
            value={342}
            subtitle="across 3 projects"
            trend={{ value: 12, label: "this month" }}
            icon={<FileText className="h-5 w-5 text-muted-foreground" />}
          />
          <MetricCard
            title="Test Cases"
            value={1247}
            subtitle="85% automated"
            trend={{ value: 8, label: "this month" }}
            icon={<CheckSquare className="h-5 w-5 text-muted-foreground" />}
          />
          <MetricCard
            title="Open Defects"
            value={39}
            subtitle="7 critical"
            trend={{ value: -15, label: "vs last week" }}
            icon={<Bug className="h-5 w-5 text-muted-foreground" />}
            variant="warning"
          />
          <MetricCard
            title="Pending Releases"
            value={4}
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
                {mockProjects.map((project) => (
                  <ProjectCard key={project.id} {...project} />
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
