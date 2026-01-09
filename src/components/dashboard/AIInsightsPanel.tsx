import { useEffect, useState } from "react";
// dialog UI removed — prompts are kept server-side
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles, AlertTriangle, Lightbulb, ChevronRight, Info, Loader } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Insight {
  id: string;
  type: "warning" | "suggestion" | "info";
  title: string;
  description: string;
  action?: string;
  project: string;
}

const DEFAULT_BADGE_COUNT = 3;

export function AIInsightsPanel() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  // prompt modal removed; prompts remain in backend for audit
  const { toast } = useToast();

  useEffect(() => {
    let mounted = true;
    const fetchInsights = async () => {
      setLoading(true);
      try {
        const res = await fetch("http://localhost:8000/api/copilot/insights");
        if (!res.ok) throw new Error("Failed to load insights");
        const data = await res.json();
        if (mounted) setInsights(data || []);
      } catch (e) {
        // fallback to empty list
        if (mounted) setInsights([]);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchInsights();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="metric-card">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-accent">
            <Sparkles className="h-4 w-4 text-accent-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">AI Insights</h3>
            <p className="text-xs text-muted-foreground">Recommendations require human approval</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {loading ? "..." : insights.length || DEFAULT_BADGE_COUNT}
          </Badge>
        </div>
      </div>

      <div className="space-y-3 max-h-72 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-6">
            <Loader className="animate-spin" />
          </div>
        ) : (
          insights.map((insight) => {
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
                      <h4 className="text-sm font-medium text-foreground">{insight.title}</h4>
                      <p className="mt-1 text-xs text-muted-foreground">{insight.description}</p>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">{insight.project}</span>
                      <div className="flex items-center gap-2">
                        {insight.action && (
                          <Button variant="ghost" size="sm" className="h-7 text-xs text-accent hover:text-accent">
                            {insight.action}
                            <ChevronRight className="ml-1 h-3 w-3" />
                          </Button>
                        )}
                        <Button
                          variant="secondary"
                          size="sm"
                          className="h-7 text-xs"
                          onClick={async () => {
                            try {
                              const res = await fetch("http://localhost:8000/api/copilot/apply-insight", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify(insight),
                              });
                              if (!res.ok) throw new Error("Failed to apply insight");
                              const json = await res.json();
                              // remove insight from list
                              setInsights((s) => s.filter((i) => i.id !== insight.id));
                              toast({ title: "Insight applied", description: `Saved as QA insight (#${json.id})` });
                            } catch (e) {
                              toast({ title: "Error", description: e instanceof Error ? e.message : "Failed to apply insight", variant: "destructive" });
                            }
                          }}
                        >
                          Approve
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="mt-4 rounded-lg bg-muted/50 p-3">
        <p className="text-center text-xs text-muted-foreground">
          <Sparkles className="mr-1 inline h-3 w-3" /> AI outputs are recommendations only. All actions require explicit human approval.
        </p>
      </div>
      {/* prompt modal removed; prompts are retained in backend only */}
    </div>
  );
}

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
