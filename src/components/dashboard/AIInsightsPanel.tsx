import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles, AlertTriangle, Lightbulb, ChevronRight, Info } from "lucide-react";

interface Insight {
  id: string;
  type: "warning" | "suggestion" | "info";
  title: string;
  description: string;
  action?: string;
  project: string;
}

const insights: Insight[] = [
  {
    id: "1",
    type: "warning",
    title: "Ambiguous Requirements Detected",
    description: "5 requirements in Project Alpha contain non-testable language that may lead to implementation gaps.",
    action: "Review Requirements",
    project: "Project Alpha",
  },
  {
    id: "2",
    type: "suggestion",
    title: "Coverage Gap Identified",
    description: "Edge cases for payment processing module have only 42% test coverage. 12 additional test cases recommended.",
    action: "Generate Tests",
    project: "Project Beta",
  },
  {
    id: "3",
    type: "info",
    title: "Release Risk Assessment",
    description: "Based on current defect trends and coverage metrics, v2.4.0 has a 78% confidence score for successful deployment.",
    project: "Project Alpha",
  },
];

const getTypeConfig = (type: string) => {
  switch (type) {
    case "warning":
      return {
        icon: AlertTriangle,
        class: "border-l-warning bg-warning/5",
        iconClass: "text-warning",
      };
    case "suggestion":
      return {
        icon: Lightbulb,
        class: "border-l-accent bg-accent/5",
        iconClass: "text-accent",
      };
    default:
      return {
        icon: Info,
        class: "border-l-info bg-info/5",
        iconClass: "text-info",
      };
  }
};

export function AIInsightsPanel() {
  return (
    <div className="metric-card">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-accent">
            <Sparkles className="h-4 w-4 text-accent-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">AI Insights</h3>
            <p className="text-xs text-muted-foreground">
              Recommendations require human approval
            </p>
          </div>
        </div>
        <Badge variant="outline" className="text-xs">
          3 new
        </Badge>
      </div>

      <div className="space-y-3">
        {insights.map((insight) => {
          const config = getTypeConfig(insight.type);
          const Icon = config.icon;

          return (
            <div
              key={insight.id}
              className={cn(
                "rounded-lg border-l-4 p-4 transition-colors hover:bg-muted/50",
                config.class
              )}
            >
              <div className="flex items-start gap-3">
                <Icon className={cn("mt-0.5 h-5 w-5 flex-shrink-0", config.iconClass)} />
                <div className="flex-1 space-y-2">
                  <div>
                    <h4 className="text-sm font-medium text-foreground">
                      {insight.title}
                    </h4>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {insight.description}
                    </p>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {insight.project}
                    </span>
                    {insight.action && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs text-accent hover:text-accent"
                      >
                        {insight.action}
                        <ChevronRight className="ml-1 h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 rounded-lg bg-muted/50 p-3">
        <p className="text-center text-xs text-muted-foreground">
          <Sparkles className="mr-1 inline h-3 w-3" />
          AI outputs are recommendations only. All actions require explicit human approval.
        </p>
      </div>
    </div>
  );
}
