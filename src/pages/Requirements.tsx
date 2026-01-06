import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, Plus, Trash2 } from "lucide-react";
import { CreateRequirementModal } from "@/components/modals/CreateRequirementModal";
import { useCrud } from "@/hooks/use-crud";

export default function Requirements() {
  const [requirements, setRequirements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Define fetch function
  const fetchRequirements = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/requirements/${selectedProject}`);
      const data = await res.json();
      setRequirements(data);
    } catch (err) {
      console.error("Error fetching requirements:", err);
    } finally {
      setLoading(false);
    }
  };

  const { delete: deleteRequirement } = useCrud({
    baseUrl: "http://localhost:8000/api/requirements",
    onSuccess: fetchRequirements,
  });

  useEffect(() => {
    fetchRequirements();
  }, [selectedProject]);

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this requirement?")) {
      await deleteRequirement(id);
    }
  };

  if (loading) return <div className="p-6">Loading requirements...</div>;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Requirements</h1>
            <p className="text-muted-foreground">Manage and track requirements with AI-powered analysis</p>
          </div>
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Requirement
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

        {requirements.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                No Requirements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">No requirements found for this project.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {requirements.map((req: any) => (
              <Card key={req.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5" />
                        {req.title}
                      </CardTitle>
                      <p className="mt-2 text-sm text-muted-foreground">{req.description}</p>
                    </div>
                    <div className="flex gap-2">
                      <Badge
                        variant={
                          req.status === "approved"
                            ? "default"
                            : req.status === "review"
                              ? "secondary"
                              : "outline"
                        }
                      >
                        {req.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(req.id)}
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
                      <p className="font-semibold">{req.requirement_id}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Clarity Score</p>
                      <p className="font-semibold">{req.clarity_score?.toFixed(1) || 0}%</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Testable</p>
                      <p className="font-semibold">{req.is_testable ? "✓ Yes" : "✗ No"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Priority</p>
                      <p className="font-semibold">P{req.priority}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <CreateRequirementModal
        isOpen={isModalOpen}
        onOpenChange={setIsModalOpen}
        projectId={selectedProject}
        onSuccess={fetchRequirements}
      />
    </DashboardLayout>
  );
}