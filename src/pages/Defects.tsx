import { useEffect, useState } from "react";
import { useProjects } from "@/context/ProjectsContext";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Bug, Plus, Trash2, Edit2 } from "lucide-react";
import { CreateDefectModal } from "@/components/modals/CreateDefectModal";
import { EditDefectModal } from "@/components/modals/EditDefectModal";
import { useCrud } from "@/hooks/use-crud";

export default function Defects() {
  const [defects, setDefects] = useState([]);
  const [filteredDefects, setFilteredDefects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { projects, loading: projectsLoading, refresh } = useProjects();
  const [selectedProject, setSelectedProject] = useState<number | "">("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedDefect, setSelectedDefect] = useState<any>(null);

  const { delete: deleteDefect } = useCrud({
    baseUrl: "http://localhost:8000/api/defects",
    onSuccess: fetchDefects,
  });

  function fetchDefects() {
    if (!selectedProject) {
      setDefects([]);
      setLoading(false);
      return;
    }

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

  useEffect(() => {
    setFilteredDefects(defects);
  }, [defects]);

  useEffect(() => {
    const handler = (e: any) => {
      const q = (e?.detail || "").toString().toLowerCase().trim();
      if (!q) {
        setFilteredDefects(defects);
        return;
      }
      const filtered = defects.filter((d: any) => {
        const title = (d.title || "").toString().toLowerCase();
        const desc = (d.description || "").toString().toLowerCase();
        return title.includes(q) || desc.includes(q);
      });
      setFilteredDefects(filtered);
    };
    window.addEventListener("globalSearch", handler as EventListener);
    return () => window.removeEventListener("globalSearch", handler as EventListener);
  }, [defects]);

  // Sync selected project when projects list changes
  useEffect(() => {
    if (!projects || projects.length === 0) {
      setSelectedProject("");
      return;
    }
    if (!projects.find((p: any) => p.id === selectedProject)) {
      setSelectedProject(projects[0].id);
    }
  }, [projects]);

  // Ensure projects are fresh when this page mounts
  useEffect(() => {
    try {
      console.debug("[Defects] calling refresh on mount");
      refresh();
    } catch (e) {
      // ignore
    }
  }, []);

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this defect?")) {
      await deleteDefect(id);
    }
  };

  const handleEdit = (defect: any) => {
    setSelectedDefect(defect);
    setIsEditModalOpen(true);
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
          <Button onClick={() => setIsCreateModalOpen(true)}>
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
            {projects.length === 0 ? (
              <option value="">No projects</option>
            ) : (
              projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))
            )}
          </select>
        </div>

        {filteredDefects.length === 0 ? (
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
            {filteredDefects.map((defect) => (
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
                        onClick={() => handleEdit(defect)}
                      >
                        <Edit2 className="h-4 w-4 text-blue-500" />
                      </Button>
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
        isOpen={isCreateModalOpen}
        onOpenChange={setIsCreateModalOpen}
        projectId={selectedProject}
        onSuccess={fetchDefects}
      />
      <EditDefectModal
        isOpen={isEditModalOpen}
        onOpenChange={setIsEditModalOpen}
        defect={selectedDefect}
        onSuccess={fetchDefects}
      />
    </DashboardLayout>
  );
}
