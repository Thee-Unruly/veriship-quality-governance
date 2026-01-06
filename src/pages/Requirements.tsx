import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";

export default function Requirements() {
  const [requirements, setRequirements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(1);

  useEffect(() => {
    fetch(`http://localhost:8000/api/requirements/${selectedProject}`)
      .then((res) => res.json())
      .then((data) => {
        setRequirements(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching requirements:", err);
        setLoading(false);
      });
  }, [selectedProject]);

  if (loading) return <div className="p-6">Loading requirements...</div>;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Requirements</h1>
          <p className="text-muted-foreground">Manage and track requirements with AI-powered analysis</p>
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
            {requirements.map((req) => (
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
    </DashboardLayout>
  );
}
