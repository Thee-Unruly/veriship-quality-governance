import { useEffect, useState } from "react";
import { useProjects } from "@/context/ProjectsContext";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckSquare, Plus, Trash2, Edit2 } from "lucide-react";
import { CreateTestCaseModal } from "@/components/modals/CreateTestCaseModal";
import { EditTestCaseModal } from "@/components/modals/EditTestCaseModal";
import { useCrud } from "@/hooks/use-crud";

export default function TestCases() {
  const [testCases, setTestCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentTab, setCurrentTab] = useState<"ongoing" | "completed">("ongoing");
  const { projects, loading: projectsLoading, refresh } = useProjects();
  const [selectedProject, setSelectedProject] = useState<number | "">("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedTestCase, setSelectedTestCase] = useState<any>(null);

  // Define fetch function first so it can be used in useCrud and useEffect
  async function fetchTestCases() {
    if (!selectedProject) {
      setTestCases([]);
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`http://localhost:8000/api/test-cases/${selectedProject}?status=${currentTab}`);
      const data = await res.json();
      setTestCases(data);
    } catch (err) {
      console.error("Error fetching test cases:", err);
    } finally {
      setLoading(false);
    }
  }

  const { delete: deleteTestCase } = useCrud({
    baseUrl: "http://localhost:8000/api/test-cases",
    onSuccess: fetchTestCases,
  });

  useEffect(() => {
    fetchTestCases();
  }, [selectedProject]);
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
      console.debug("[TestCases] calling refresh on mount");
      refresh();
    } catch (e) {
      // ignore
    }
  }, []);

  useEffect(() => {
    // refetch when tab changes
    setLoading(true);
    fetchTestCases();
  }, [currentTab]);

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this test case?")) {
      await deleteTestCase(id);
    }
  };

  const handleEdit = (testCase: any) => {
    setSelectedTestCase(testCase);
    setIsEditModalOpen(true);
  };

  const handleMarkComplete = async (id: number) => {
    try {
      await fetch(`http://localhost:8000/api/test-cases/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "completed" }),
      });
      fetchTestCases();
    } catch (err) {
      console.error("Failed to mark complete", err);
    }
  };

  if (loading) return <div className="p-6">Loading test cases...</div>;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Test Cases</h1>
            <p className="text-muted-foreground">Design, execute, and manage test cases</p>
          </div>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Test Case
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

        <div className="mb-4 flex gap-2">
          <button
            className={`px-3 py-1 rounded ${currentTab === "ongoing" ? "bg-accent text-accent-foreground" : "bg-muted"}`}
            onClick={() => setCurrentTab("ongoing")}
          >
            Ongoing
          </button>
          <button
            className={`px-3 py-1 rounded ${currentTab === "completed" ? "bg-accent text-accent-foreground" : "bg-muted"}`}
            onClick={() => setCurrentTab("completed")}
          >
            Completed
          </button>
        </div>

        {testCases.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckSquare className="h-5 w-5" />
                No Test Cases
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">No test cases found for this project.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {testCases.map((tc: any) => (
              <Card key={tc.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <CheckSquare className="h-5 w-5" />
                        {tc.title}
                      </CardTitle>
                      <p className="mt-2 text-sm text-muted-foreground">{tc.description}</p>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant={tc.is_automated ? "default" : "secondary"}>
                        {tc.is_automated ? "Automated" : "Manual"}
                      </Badge>
                      <Badge variant={tc.status === "completed" ? "outline" : "default"}>
                        {tc.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(tc)}
                      >
                        <Edit2 className="h-4 w-4 text-blue-500" />
                      </Button>
                      {tc.status !== "completed" && (
                        <Button variant="ghost" size="sm" onClick={() => handleMarkComplete(tc.id)}>
                          Mark Complete
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(tc.id)}
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
                      <p className="font-semibold">{tc.test_case_id}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Type</p>
                      <p className="font-semibold capitalize">{tc.test_type}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Coverage</p>
                      <p className="font-semibold">{tc.coverage_status?.toFixed(1) || 0}%</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Priority</p>
                      <p className="font-semibold">P{tc.priority}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <CreateTestCaseModal
        isOpen={isCreateModalOpen}
        onOpenChange={setIsCreateModalOpen}
        projectId={selectedProject}
        onSuccess={fetchTestCases}
      />
      <EditTestCaseModal
        isOpen={isEditModalOpen}
        onOpenChange={setIsEditModalOpen}
        testCase={selectedTestCase}
        onSuccess={fetchTestCases}
      />
    </DashboardLayout>
  );
}