import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckSquare, Plus, Trash2 } from "lucide-react";
import { CreateTestCaseModal } from "@/components/modals/CreateTestCaseModal";
import { useCrud } from "@/hooks/use-crud";

export default function TestCases() {
  const [testCases, setTestCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { delete: deleteTestCase } = useCrud({
    baseUrl: "http://localhost:8000/api/test-cases",
    onSuccess: fetchTestCases,
  });

  function fetchTestCases() {
    fetch(`http://localhost:8000/api/test-cases/${selectedProject}`)
      .then((res) => res.json())
      .then((data) => {
        setTestCases(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching test cases:", err);
        setLoading(false);
      });
  }

  useEffect(() => {
    fetchTestCases();
  }, [selectedProject]);

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this test case?")) {
      await deleteTestCase(id);
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
          <Button onClick={() => setIsModalOpen(true)}>
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
            <option value={1}>Project Alpha</option>
            <option value={2}>Project Beta</option>
            <option value={3}>Project Gamma</option>
          </select>
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
            {testCases.map((tc) => (
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
        isOpen={isModalOpen}
        onOpenChange={setIsModalOpen}
        projectId={selectedProject}
        onSuccess={fetchTestCases}
      />
    </DashboardLayout>
  );
}

if (loading) return <div className="p-6">Loading test cases...</div>;

return (
  <DashboardLayout>
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Test Cases</h1>
        <p className="text-muted-foreground">Design, execute, and manage test cases</p>
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
          {testCases.map((tc) => (
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
                  <Badge variant={tc.is_automated ? "default" : "secondary"}>
                    {tc.is_automated ? "Automated" : "Manual"}
                  </Badge>
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
  </DashboardLayout>
);
}
