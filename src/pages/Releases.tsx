import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Rocket, Plus, Trash2 } from "lucide-react";
import { CreateReleaseModal } from "@/components/modals/CreateReleaseModal";
import { useCrud } from "@/hooks/use-crud";

export default function Releases() {
  const [releases, setReleases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { delete: deleteRelease } = useCrud({
    baseUrl: "http://localhost:8000/api/releases",
    onSuccess: fetchReleases,
  });

  function fetchReleases() {
    fetch(`http://localhost:8000/api/releases/${selectedProject}`)
      .then((res) => res.json())
      .then((data) => {
        setReleases(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching releases:", err);
        setLoading(false);
      });
  }

  useEffect(() => {
    fetchReleases();
  }, [selectedProject]);

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this release?")) {
      await deleteRelease(id);
    }
  };

  if (loading) return <div className="p-6">Loading releases...</div>;

  const getStatusColor = (status) => {
    switch (status) {
      case "released":
        return "default";
      case "approved":
        return "secondary";
      case "in-testing":
        return "outline";
      default:
        return "outline";
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Releases</h1>
            <p className="text-muted-foreground">Manage release governance and approvals</p>
          </div>
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Release
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

        {releases.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Rocket className="h-5 w-5" />
                No Releases
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">No releases found for this project.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {releases.map((release) => (
              <Card key={release.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Rocket className="h-5 w-5" />
                        {release.version}
                      </CardTitle>
                      <p className="mt-2 text-sm text-muted-foreground">
                        {release.release_id}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant={getStatusColor(release.status)}>
                        {release.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(release.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Status</p>
                      <p className="font-semibold capitalize">{release.status}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Risk Score</p>
                      <p className="font-semibold">{release.risk_score?.toFixed(1) || 0}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Decision</p>
                      <p className="font-semibold">
                        {release.go_no_go_decision || "Pending"}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Planned Date</p>
                      <p className="font-semibold">
                        {release.planned_release_date
                          ? new Date(release.planned_release_date).toLocaleDateString()
                          : "Not set"}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <CreateReleaseModal
        isOpen={isModalOpen}
        onOpenChange={setIsModalOpen}
        projectId={selectedProject}
        onSuccess={fetchReleases}
      />
    </DashboardLayout>
  );

  return null;
}
