import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, Plus, Trash2, Edit2, Sparkles, Loader2, Beaker } from "lucide-react";
import { CreateRequirementModal } from "@/components/modals/CreateRequirementModal";
import { EditRequirementModal } from "@/components/modals/EditRequirementModal";
import { GeneratedTestsModal } from "@/components/modals/GeneratedTestsModal";
import { AnalyzeRequirementModal } from "@/components/copilot/AnalyzeRequirementModal";
import { GenerateTestCasesModal } from "@/components/copilot/GenerateTestCasesModal";
import { useCrud } from "@/hooks/use-crud";
import { useToast } from "@/components/ui/use-toast";

export default function Requirements() {
  const [requirements, setRequirements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(1);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedRequirement, setSelectedRequirement] = useState<any>(null);
  const [isAnalyzeModalOpen, setIsAnalyzeModalOpen] = useState(false);
  const [isGenerateTestsModalOpen, setIsGenerateTestsModalOpen] = useState(false);

  const [analysisLoading, setAnalysisLoading] = useState<{ [key: number]: boolean }>({});
  const [generatedTests, setGeneratedTests] = useState([]);

  const { toast } = useToast();

  const fetchRequirements = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/requirements/${selectedProject}`);
      const data = await response.json();
      setRequirements(data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching requirements:", error);
      toast({ title: "Error", description: "Failed to fetch requirements", variant: "destructive" });
      setLoading(false);
    }
  };

  const { delete: deleteRequirement } = useCrud({
    baseUrl: "http://localhost:8000/api/requirements",
    onSuccess: () => {
      fetchRequirements();
      toast({ title: "Requirement deleted successfully." });
    },
  });

  useEffect(() => {
    fetchRequirements();
  }, [selectedProject]);

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this requirement?")) {
      await deleteRequirement(id);
    }
  };

  const handleEdit = (requirement: any) => {
    setSelectedRequirement(requirement);
    setIsEditModalOpen(true);
  };

  const handleAnalyzeClarity = async (requirement: any) => {
    setSelectedRequirement(requirement);
    setIsAnalyzeModalOpen(true);
  };

  const handleGenerateTests = async (requirement: any) => {
    setSelectedRequirement(requirement);
    setIsGenerateTestsModalOpen(true);
  };

  if (loading) return <div className="p-6">Loading requirements...</div>;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Requirements</h1>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> New Requirement
          </Button>
        </div>

        {/* Project filter dropdown */}
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

        {/* Requirements List */}
        <div className="grid gap-4">
          {requirements.map((req: any) => (
            <Card key={req.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>{req.title}</CardTitle>
                    <p className="text-sm text-muted-foreground">{req.description}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <Badge variant={req.status === "approved" ? "default" : "secondary"}>
                      {req.status}
                    </Badge>
                    <Button variant="ghost" size="sm" onClick={() => handleAnalyzeClarity(req)} disabled={analysisLoading[req.id]}>
                      {analysisLoading[req.id] ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4 text-purple-500" />}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleGenerateTests(req)} disabled={analysisLoading[req.id]}>
                      {analysisLoading[req.id] ? <Loader2 className="h-4 w-4 animate-spin" /> : <Beaker className="h-4 w-4 text-green-500" />}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(req)}>
                      <Edit2 className="h-4 w-4 text-blue-500" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(req.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Priority</p>
                    <p className="font-semibold">{req.priority}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Clarity Score</p>
                    <p className="font-semibold">{req.clarity_score?.toFixed(1) || "N/A"}%</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Testable</p>
                    <p className="font-semibold">{req.is_testable ? "Yes" : "No"}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Modals */}
      <CreateRequirementModal isOpen={isCreateModalOpen} onOpenChange={setIsCreateModalOpen} projectId={selectedProject} onSuccess={fetchRequirements} />
      <EditRequirementModal isOpen={isEditModalOpen} onOpenChange={setIsEditModalOpen} requirement={selectedRequirement} onSuccess={fetchRequirements} />
      {selectedRequirement && (
        <>
          <AnalyzeRequirementModal
            isOpen={isAnalyzeModalOpen}
            onOpenChange={setIsAnalyzeModalOpen}
            requirementId={selectedRequirement.id}
            requirementTitle={selectedRequirement.title}
          />
          <GenerateTestCasesModal
            isOpen={isGenerateTestsModalOpen}
            onOpenChange={setIsGenerateTestsModalOpen}
            requirementId={selectedRequirement.id}
            requirementTitle={selectedRequirement.title}
          />
        </>
      )}
    </DashboardLayout>
  );
}