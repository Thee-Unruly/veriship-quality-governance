import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Bug, Plus, Trash2 } from "lucide-react";
import { CreateDefectModal } from "@/components/modals/CreateDefectModal";
import { useCrud } from "@/hooks/use-crud";

export default function Defects() {
  const [defects, setDefects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { delete: deleteDefect } = useCrud({
    baseUrl: "http://localhost:8000/api/defects",
    onSuccess: fetchDefects,
  });

  function fetchDefects() {
    fetch(`http://localhost:8000/api/defects/${selectedProject}`)
      .then((res) => res.json())
      .then((data) => {
        setDefects(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching defects:", err);
        setLoading(false);
      });
  }

  useEffect(() => {
    fetchDefects();
  }, [selectedProject]);

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this defect?")) {
      await deleteDefect(id);
    }
  };

  if (loading) return <div className="p-6">Loading defects...</div>;

  const getSeverityColor = (severity) => {
    switch (severity) {
      case "CRITICAL":
        return "destructive";
      case "HIGH":
        return "destructive";
      case "MEDIUM":
        return "secondary";
      case "LOW":
        return "outline";
      default:
        return "default";
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Defects</h1>
            <p className="text-muted-foreground">Track and manage defects across projects</p>
          </div>
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Defect
          </Button>
        </div>

        <div className="mb-4">
          <label className="text-sm font-medium">Filter by Project:</label>
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(Number(e.target.value))}
            className="mt-2 rounded border border-input bg-background px-3 py-2"
          >
            <option value={1}>Project Alpha</option>
            <option value={2}>Project Beta</option>
            <option value={3}>Project Gamma</option>
          </select>
        </div>

        {defects.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bug className="h-5 w-5" />
                No Defects
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">No defects found for this project.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {defects.map((defect) => (
              <Card key={defect.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Bug className="h-5 w-5" />
                        {defect.title}
                      </CardTitle>
                      <p className="mt-2 text-sm text-muted-foreground">
                        {defect.description}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant={getSeverityColor(defect.severity)}>
                        {defect.severity}
                      </Badge>
                      <Badge variant="outline">{defect.status}</Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(defect.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">ID</p>
                      <p className="font-semibold">{defect.defect_id}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Risk Score</p>
                      <p className="font-semibold">
                        {defect.release_risk_score?.toFixed(1) || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Found By</p>
                      <p className="font-semibold">{defect.found_by || "Unknown"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Recurrence Risk</p>
                      <p className="font-semibold">
                        {defect.likely_to_recur ? "High" : "Low"}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <CreateDefectModal
        isOpen={isModalOpen}
        onOpenChange={setIsModalOpen}
        projectId={selectedProject}
        onSuccess={fetchDefects}
      />
    </DashboardLayout>
  );
}
