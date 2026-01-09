import { useEffect, useState } from "react";
import { useProjects } from "@/context/ProjectsContext";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckSquare, Plus, Trash2, Edit2, Info } from "lucide-react";
import { CreateTestCaseModal } from "@/components/modals/CreateTestCaseModal";
import { EditTestCaseModal } from "@/components/modals/EditTestCaseModal";
import { useCrud } from "@/hooks/use-crud";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";

export default function TestCases() {
  const [testCases, setTestCases] = useState([]);
  const [filteredTestCases, setFilteredTestCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [requirementsMap, setRequirementsMap] = useState<Record<number, string>>({});
  const [currentTab, setCurrentTab] = useState<"ongoing" | "completed">("ongoing");
  const { projects, loading: projectsLoading, refresh } = useProjects();
  const [selectedProject, setSelectedProject] = useState<number | "">("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedTestCase, setSelectedTestCase] = useState<any>(null);

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 1: return "Critical";
      case 2: return "High";
      case 3: return "Medium";
      case 4: return "Low";
      case 5: return "Lowest";
      default: return "Unknown";
    }
  };

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

  async function fetchRequirements() {
    if (!selectedProject) {
      setRequirementsMap({});
      return;
    }
    try {
      const res = await fetch(`http://localhost:8000/api/requirements/${selectedProject}`);
      const data = await res.json();
      const map: Record<number, string> = {};
      (data || []).forEach((r: any) => { map[r.id] = r.title; });
      setRequirementsMap(map);
    } catch (err) {
      console.error("Error fetching requirements for test cases grouping:", err);
    }
  }

  const { delete: deleteTestCase } = useCrud({
    baseUrl: "http://localhost:8000/api/test-cases",
    onSuccess: fetchTestCases,
  });

  useEffect(() => {
    fetchTestCases();
  }, [selectedProject]);

  useEffect(() => {
    fetchRequirements();
  }, [selectedProject]);

  useEffect(() => {
    setFilteredTestCases(testCases);
  }, [testCases]);

  useEffect(() => {
    const handler = (e: any) => {
      const q = (e?.detail || "").toString().toLowerCase().trim();
      if (!q) {
        setFilteredTestCases(testCases);
        return;
      }
      const filtered = testCases.filter((t: any) => {
        const title = (t.title || "").toString().toLowerCase();
        const desc = (t.description || "").toString().toLowerCase();
        return title.includes(q) || desc.includes(q);
      });
      setFilteredTestCases(filtered);
    };
    window.addEventListener("globalSearch", handler as EventListener);
    return () => window.removeEventListener("globalSearch", handler as EventListener);
  }, [testCases]);
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

  // Group test cases by requirement_id
  const grouped = (filteredTestCases || []).reduce((acc: any, tc: any) => {
    const rid = tc.requirement_id || 0;
    if (!acc[rid]) acc[rid] = [];
    acc[rid].push(tc);
    return acc;
  }, {} as Record<string, any[]>);

  const groups = Object.keys(grouped).map((k) => ({
    requirementId: Number(k),
    title: Number(k) === 0 ? "(No Requirement)" : (requirementsMap[Number(k)] || `Requirement ${k}`),
    testCases: grouped[k],
  }));

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

        {filteredTestCases.length === 0 ? (
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
          <div className="space-y-6">
            <Accordion type="multiple" className="space-y-4">
              {groups.map((g) => (
                <AccordionItem value={`req-${g.requirementId}`} key={String(g.requirementId)}>
                  <AccordionTrigger>
                    <div className="w-full flex items-center justify-between px-4 py-2 bg-background border border-border rounded-lg hover:shadow-sm">
                      <div className="flex items-center gap-3">
                        <div>
                          <div className="text-lg font-semibold text-foreground">{g.title}</div>
                          <div className="text-sm text-muted-foreground flex items-center gap-1">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Info className="h-3 w-3 cursor-help" />
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Click to expand and view test cases tied to this requirement</p>
                              </TooltipContent>
                            </Tooltip>
                            Requirement details
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">{g.testCases.length}</Badge>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="grid gap-4 mt-3">
                      {g.testCases.map((tc: any) => (
                        <div key={tc.id} className="flex items-center justify-between gap-4 p-3 border rounded-md bg-card">
                          <div className="flex-1">
                            <div className="flex items-center gap-3">
                              <CheckSquare className="h-5 w-5 text-primary" />
                              <div>
                                <div className="font-medium text-foreground">{tc.title}</div>
                                <div className="text-sm text-muted-foreground">{tc.description}</div>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="flex flex-col items-end text-sm">
                              <span className="text-muted-foreground">Priority</span>
                              <span className="font-semibold">{getPriorityLabel(tc.priority)}</span>
                            </div>
                            <Badge variant={tc.is_automated ? "default" : "secondary"}>{tc.is_automated ? "Auto" : "Manual"}</Badge>
                            <div className="flex items-center gap-1">
                              <Button variant="ghost" size="sm" onClick={() => handleEdit(tc)}>
                                <Edit2 className="h-4 w-4 text-blue-500" />
                              </Button>
                              {tc.status !== "completed" && (
                                <Button variant="ghost" size="sm" onClick={() => handleMarkComplete(tc.id)}>Done</Button>
                              )}
                              <Button variant="ghost" size="sm" onClick={() => handleDelete(tc.id)}>
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
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