import { useEffect, useState } from "react";
import { useProjects } from "@/context/ProjectsContext";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FolderKanban, Plus, Trash2, Edit2 } from "lucide-react";
import { RefreshCw } from "lucide-react";
import { CreateProjectModal } from "@/components/modals/CreateProjectModal";
import { EditProjectModal } from "@/components/modals/EditProjectModal";
import { useCrud } from "@/hooks/use-crud";

export default function Projects() {
  const { projects, loading: loading, refresh } = useProjects();
  const [filteredProjects, setFilteredProjects] = useState<any[]>(projects);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<any>(null);

  const { delete: deleteProject } = useCrud({
    baseUrl: "http://localhost:8000/api/projects",
    onSuccess: async () => {
      try { await refresh(); } catch (e) { /* ignore */ }
    },
  });

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this project?")) {
      await deleteProject(id);
    }
  };

  const handleEdit = (project: any) => {
    setSelectedProject(project);
    setIsEditModalOpen(true);
  };

  useEffect(() => {
    setFilteredProjects(projects);
  }, [projects]);

  useEffect(() => {
    const handler = (e: any) => {
      const q = (e?.detail || "").toString().toLowerCase().trim();
      if (!q) {
        setFilteredProjects(projects);
        return;
      }
      const filtered = projects.filter((p: any) => {
        const name = (p.name || "").toString().toLowerCase();
        const desc = (p.description || "").toString().toLowerCase();
        return name.includes(q) || desc.includes(q);
      });
      setFilteredProjects(filtered);
    };
    window.addEventListener("globalSearch", handler as EventListener);
    return () => window.removeEventListener("globalSearch", handler as EventListener);
  }, [projects]);

  if (loading) return <div className="p-6">Loading projects...</div>;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Projects</h1>
            <p className="text-muted-foreground">Manage your organization's projects</p>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={() => refresh()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={() => setIsCreateModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Project
            </Button>
          </div>
        </div>

        {filteredProjects.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderKanban className="h-5 w-5" />
                No Projects
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">No projects found.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {filteredProjects.map((project: any) => (
              <Card key={project.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{project.name}</CardTitle>
                    <div className="flex gap-2">
                      <Badge
                        variant={
                          project.status === "active" || project.status === "on-track"
                            ? "default"
                            : project.status === "at-risk"
                              ? "destructive"
                              : "secondary"
                        }
                      >
                        {project.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(project)}
                      >
                        <Edit2 className="h-4 w-4 text-blue-500" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(project.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">
                    {project.description}
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Created</p>
                      <p className="font-semibold">
                        {new Date(project.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Release Date</p>
                      <p className="font-semibold">
                        {project.target_release_date
                          ? new Date(project.target_release_date).toLocaleDateString()
                          : "Not set"}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Status</p>
                      <p className="font-semibold capitalize">{project.status}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onOpenChange={setIsCreateModalOpen}
        onSuccess={refresh}
      />
      <EditProjectModal
        isOpen={isEditModalOpen}
        onOpenChange={setIsEditModalOpen}
        project={selectedProject}
        onSuccess={refresh}
      />
    </DashboardLayout>
  );
}