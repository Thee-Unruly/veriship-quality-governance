import { useState, useEffect } from "react";
import { Play, Upload, FileCode, Loader2, CheckCircle2, XCircle, Clock, AlertCircle, Sparkles, Monitor, Globe, Camera, FileDown, RefreshCw, StopCircle, Settings2 } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

interface TestStep {
    type: "http" | "assert" | "delay";
    description: string;
    method?: string;
    url?: string;
    headers?: Record<string, string>;
    body?: Record<string, any>;
    expected_status?: number;
    expected_contains?: string;
    duration_ms?: number;
}

interface TestCase {
    title: string;
    description: string;
    test_type: string;
    priority: number;
    steps: TestStep[];
    expected_result: string;
}

interface StepResult {
    step_number: number;
    description: string;
    status: "passed" | "failed" | "skipped";
    duration_ms: number;
    details?: string;
    error?: string;
}

interface TestCaseResult {
    title: string;
    status: "passed" | "failed" | "skipped";
    duration_ms: number;
    steps: StepResult[];
    error?: string;
}

interface TrialRunResponse {
    total_cases: number;
    passed: number;
    failed: number;
    skipped: number;
    total_duration_ms: number;
    results: TestCaseResult[];
}

// Playwright Automation Types
interface PlaywrightExecutionConfig {
    browser_type: "chromium" | "firefox" | "webkit";
    headless: boolean;
    viewport: { width: number; height: number };
    timeout: number;
    base_url: string;
    record_trace: boolean;
    record_video: boolean;
    screenshot_on_failure: boolean;
    retry_count: number;
    environment: string;
}

interface PlaywrightStepResult {
    step_number: number;
    action_type: string;
    description: string;
    selector: string | null;
    status: "passed" | "failed" | "skipped";
    duration_ms: number;
    timestamp: string;
    value?: any;
    error?: string;
    screenshot_path?: string;
}

interface PlaywrightExecutionResponse {
    execution_id: number;
    test_case_id: number;
    status: string;
    start_time: string;
    end_time: string | null;
    duration_ms: number;
    steps: PlaywrightStepResult[];
    error_message?: string;
    screenshot_path?: string;
    trace_path?: string;
    network_logs_count: number;
    browser_type: string;
    environment: string;
    defect_id?: number;
}

interface PlaywrightRunnerStatus {
    is_running: boolean;
    browser_type: string | null;
    contexts_count: number;
    active_executions_count: number;
    queued_executions_count: number;
}

const SAMPLE_TEST_CASES = `{
  "target_base_url": "https://api.example.com",
  "test_cases": [
    {
      "title": "API Health Check",
      "description": "Verify API is responding",
      "test_type": "Positive",
      "priority": 1,
      "expected_result": "API returns 200 OK",
      "steps": [
        {
          "type": "http",
          "description": "GET health endpoint",
          "method": "GET",
          "url": "/health",
          "expected_status": 200,
          "expected_contains": "healthy"
        }
      ]
    },
    {
      "title": "Create Resource Test",
      "description": "Test resource creation",
      "test_type": "Positive",
      "priority": 2,
      "expected_result": "Resource created successfully",
      "steps": [
        {
          "type": "http",
          "description": "POST create resource",
          "method": "POST",
          "url": "/api/resources",
          "headers": {
            "Content-Type": "application/json"
          },
          "body": {
            "name": "Test Resource",
            "type": "demo"
          },
          "expected_status": 201
        }
      ]
    }
  ]
}`;

export default function TestRunner() {
    const { toast } = useToast();
    const [testInput, setTestInput] = useState("");
    const [baseUrl, setBaseUrl] = useState("http://localhost:8000");
    const [isRunning, setIsRunning] = useState(false);
    const [results, setResults] = useState<TrialRunResponse | null>(null);

    // Cascading dropdowns
    const [projects, setProjects] = useState<any[]>([]);
    const [requirements, setRequirements] = useState<any[]>([]);
    const [testCases, setTestCases] = useState<any[]>([]);
    const [selectedProjectId, setSelectedProjectId] = useState("");
    const [selectedRequirementId, setSelectedRequirementId] = useState("");
    const [selectedTestCaseId, setSelectedTestCaseId] = useState("");

    const [isGeneratingScenarios, setIsGeneratingScenarios] = useState(false);
    const [scenarios, setScenarios] = useState<any[]>([]);
    const [currentScenario, setCurrentScenario] = useState(0);
    const [isConvertingToJson, setIsConvertingToJson] = useState(false);

    // Playwright Automation State
    const [activeTab, setActiveTab] = useState("trial");
    const [playwrightConfig, setPlaywrightConfig] = useState<PlaywrightExecutionConfig>({
        browser_type: "chromium",
        headless: true,
        viewport: { width: 1280, height: 720 },
        timeout: 30000,
        base_url: "http://localhost:8000",
        record_trace: true,
        record_video: false,
        screenshot_on_failure: true,
        retry_count: 0,
        environment: "development",
    });
    const [playwrightResult, setPlaywrightResult] = useState<PlaywrightExecutionResponse | null>(null);
    const [playwrightStatus, setPlaywrightStatus] = useState<PlaywrightRunnerStatus | null>(null);
    const [isPlaywrightRunning, setIsPlaywrightRunning] = useState(false);
    const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

    // Load projects
    useEffect(() => {
        const loadProjects = async () => {
            try {
                const response = await fetch("http://localhost:8000/api/projects");
                const data = await response.json();
                setProjects(Array.isArray(data) ? data : []);
            } catch (error) {
                console.error("Error loading projects:", error);
            }
        };
        loadProjects();
    }, []);

    // Load requirements when project changes
    useEffect(() => {
        if (!selectedProjectId) {
            setRequirements([]);
            setSelectedRequirementId("");
            return;
        }
        const loadRequirements = async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/requirements/${selectedProjectId}`);
                const data = await response.json();
                setRequirements(Array.isArray(data) ? data : []);
            } catch (error) {
                console.error("Error loading requirements:", error);
            }
        };
        loadRequirements();
    }, [selectedProjectId]);

    // Load test cases when requirement changes
    useEffect(() => {
        if (!selectedRequirementId) {
            setTestCases([]);
            setSelectedTestCaseId("");
            return;
        }
        const loadTestCases = async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/test-cases/${selectedProjectId}`);
                const data = await response.json();
                const filtered = data.filter((tc: any) => tc.requirement_id === parseInt(selectedRequirementId));
                setTestCases(filtered);
            } catch (error) {
                console.error("Error loading test cases:", error);
            }
        };
        loadTestCases();
    }, [selectedRequirementId, selectedProjectId]);

    // Fetch Playwright runner status
    const fetchPlaywrightStatus = async () => {
        try {
            const response = await fetch("http://localhost:8000/api/automation/status");
            if (response.ok) {
                const data = await response.json();
                setPlaywrightStatus(data);
            }
        } catch (error) {
            console.error("Error fetching Playwright status:", error);
        }
    };

    // Poll for execution status
    const pollExecutionStatus = async (executionId: number) => {
        try {
            const response = await fetch(`http://localhost:8000/api/automation/executions/${executionId}/status`);
            if (response.ok) {
                const data = await response.json();
                if (!data.is_running) {
                    // Execution completed, stop polling
                    if (pollingInterval) {
                        clearInterval(pollingInterval);
                        setPollingInterval(null);
                    }
                    // Fetch full results
                    const resultResponse = await fetch(`http://localhost:8000/api/automation/executions/${executionId}`);
                    if (resultResponse.ok) {
                        const resultData = await resultResponse.json();
                        setPlaywrightResult(resultData);
                    }
                    setIsPlaywrightRunning(false);
                }
            }
        } catch (error) {
            console.error("Error polling execution status:", error);
        }
    };

    // Execute test case with Playwright
    const executeWithPlaywright = async () => {
        if (!selectedTestCaseId) {
            toast({
                title: "No test case selected",
                description: "Please select a test case to execute",
                variant: "destructive",
            });
            return;
        }

        setIsPlaywrightRunning(true);
        setPlaywrightResult(null);

        try {
            const response = await fetch(
                `http://localhost:8000/api/automation/execute/test-case/${selectedTestCaseId}?executed_by=manual`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(playwrightConfig),
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Execution failed");
            }

            const data: PlaywrightExecutionResponse = await response.json();
            setPlaywrightResult(data);

            toast({
                title: data.status === "passed" ? "Test Passed" : "Test Failed",
                description: `Execution completed in ${data.duration_ms.toFixed(0)}ms`,
                variant: data.status === "passed" ? "default" : "destructive",
            });
        } catch (error: any) {
            toast({
                title: "Execution Error",
                description: error.message || "Failed to execute test",
                variant: "destructive",
            });
        } finally {
            setIsPlaywrightRunning(false);
            fetchPlaywrightStatus();
        }
    };

    // Stop running execution
    const stopExecution = async () => {
        if (!playwrightResult?.execution_id) return;

        try {
            await fetch(`http://localhost:8000/api/automation/executions/${playwrightResult.execution_id}`, {
                method: "DELETE",
            });
            toast({
                title: "Execution stopped",
                description: "Test execution was cancelled",
            });
        } catch (error) {
            console.error("Error stopping execution:", error);
        }
    };

    // Download trace file
    const downloadTrace = async () => {
        if (!playwrightResult?.execution_id) return;

        window.open(
            `http://localhost:8000/api/automation/executions/${playwrightResult.execution_id}/trace?download=true`,
            "_blank"
        );
    };

    // Download screenshot
    const downloadScreenshot = async () => {
        if (!playwrightResult?.execution_id) return;

        window.open(
            `http://localhost:8000/api/automation/executions/${playwrightResult.execution_id}/screenshot?download=true`,
            "_blank"
        );
    };

    // Load Playwright status on mount
    useEffect(() => {
        fetchPlaywrightStatus();
    }, []);

    const handleGenerateAndRunScenarios = async () => {
        if (!selectedTestCaseId) {
            toast({
                title: "No selection",
                description: "Please select project, requirement, and test case",
                variant: "destructive",
            });
            return;
        }

        setIsGeneratingScenarios(true);
        setScenarios([]);
        setCurrentScenario(0);

        try {
            const selectedCase = testCases.find(tc => tc.id === parseInt(selectedTestCaseId));
            const selectedReq = requirements.find(r => r.id === parseInt(selectedRequirementId));

            toast({
                title: "Generating scenarios",
                description: "AI is creating 5 test scenarios...",
            });

            // Step 1: AI generates 5 scenarios
            const response = await fetch("http://localhost:8000/api/copilot/generate-scenarios", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    testCase: selectedCase,
                    requirement: selectedReq,
                    count: 5
                }),
            });

            if (!response.ok) throw new Error("Scenario generation failed");

            const data = await response.json();
            const generatedScenarios = data.scenarios;
            setScenarios(generatedScenarios);

            toast({
                title: "Scenarios generated",
                description: `${generatedScenarios.length} scenarios ready. Running automatically...`,
            });

            // Step 2: Run each scenario one by one
            for (let i = 0; i < generatedScenarios.length; i++) {
                setCurrentScenario(i + 1);

                const scenarioPayload = {
                    test_cases: [generatedScenarios[i]],
                    target_base_url: baseUrl,
                };

                const runResponse = await fetch("http://localhost:8000/api/trial/run", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(scenarioPayload),
                });

                const runResult = await runResponse.json();

                // Update scenario with result
                generatedScenarios[i].result = runResult;
                setScenarios([...generatedScenarios]);
            }

            toast({
                title: "All scenarios completed",
                description: "Check results below",
            });

        } catch (error: any) {
            toast({
                title: "Error",
                description: error.message || "Failed to generate/run scenarios",
                variant: "destructive",
            });
        } finally {
            setIsGeneratingScenarios(false);
            setCurrentScenario(0);
        }
    };

    const loadSample = () => {
        setTestInput(SAMPLE_TEST_CASES);
        toast({
            title: "Sample loaded",
            description: "Example test cases loaded. Modify as needed.",
        });
    };

    const handleLoadFromDatabase = async () => {
        if (!selectedTestCaseId) {
            toast({
                title: "No selection",
                description: "Please select a test case",
                variant: "destructive",
            });
            return;
        }

        setIsConvertingToJson(true);
        try {
            const selectedCase = testCases.find(tc => tc.id === parseInt(selectedTestCaseId));

            // Call AI to convert test case to JSON
            const response = await fetch("http://localhost:8000/api/copilot/convert-test-to-json", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ testCase: selectedCase }),
            });

            if (!response.ok) throw new Error("Conversion failed");

            const data = await response.json();
            setTestInput(JSON.stringify(data.json_format, null, 2));

            toast({
                title: "Test case loaded",
                description: `${selectedCase.title} converted to JSON and ready to run`,
            });
        } catch (error: any) {
            toast({
                title: "Error",
                description: error.message || "Failed to convert test case",
                variant: "destructive",
            });
        } finally {
            setIsConvertingToJson(false);
        }
    };

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const content = e.target?.result as string;
                setTestInput(content);
                toast({
                    title: "File loaded",
                    description: `${file.name} loaded successfully`,
                });
            };
            reader.readAsText(file);
        }
    };

    const runTests = async () => {
        if (!testInput.trim()) {
            toast({
                title: "No test cases",
                description: "Please provide test cases to run",
                variant: "destructive",
            });
            return;
        }

        try {
            setIsRunning(true);
            setResults(null);

            // Parse input
            const parsed = JSON.parse(testInput);
            const payload = {
                test_cases: parsed.test_cases || [],
                target_base_url: parsed.target_base_url || baseUrl,
            };

            // Call backend
            const response = await fetch("http://localhost:8000/api/trial/run", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data: TrialRunResponse = await response.json();
            setResults(data);

            toast({
                title: "Tests completed",
                description: `${data.passed} passed, ${data.failed} failed out of ${data.total_cases} cases`,
            });
        } catch (error: any) {
            toast({
                title: "Execution failed",
                description: error.message || "Failed to run tests",
                variant: "destructive",
            });
        } finally {
            setIsRunning(false);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "passed":
                return <CheckCircle2 className="h-5 w-5 text-green-500" />;
            case "failed":
                return <XCircle className="h-5 w-5 text-red-500" />;
            case "skipped":
                return <AlertCircle className="h-5 w-5 text-yellow-500" />;
            default:
                return <Clock className="h-5 w-5 text-gray-500" />;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case "passed":
                return "bg-green-500/10 text-green-500 border-green-500/20";
            case "failed":
                return "bg-red-500/10 text-red-500 border-red-500/20";
            case "skipped":
                return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
            default:
                return "bg-gray-500/10 text-gray-500 border-gray-500/20";
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6 p-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
                        Test Runner
                    </h1>
                    <p className="text-muted-foreground mt-2">
                        Execute test cases with Trial Runner (API tests) or Playwright Automation (browser tests).
                    </p>
                </div>

                {/* Tabs for Trial Runner vs Playwright */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
                        <TabsTrigger value="trial" className="flex items-center gap-2">
                            <Globe className="h-4 w-4" />
                            Trial Runner
                        </TabsTrigger>
                        <TabsTrigger value="playwright" className="flex items-center gap-2">
                            <Monitor className="h-4 w-4" />
                            Playwright
                        </TabsTrigger>
                    </TabsList>

                    {/* Trial Runner Tab Content */}
                    <TabsContent value="trial" className="mt-6">
                        <div className="grid gap-6 lg:grid-cols-2">
                            {/* Input Section */}
                            <Card className="border-2">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <FileCode className="h-5 w-5" />
                                        Test Configuration
                                    </CardTitle>
                                    <CardDescription>
                                        Provide test cases in JSON format or upload a file
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {/* Base URL */}
                                    <div className="space-y-2">
                                        <Label htmlFor="baseUrl">Target Base URL (Optional)</Label>
                                        <Input
                                            id="baseUrl"
                                            value={baseUrl}
                                            onChange={(e) => setBaseUrl(e.target.value)}
                                            placeholder="http://localhost:8000"
                                            className="font-mono text-sm"
                                        />
                                    </div>

                                    {/* Load from Database Section */}
                                    <div className="border-t pt-4 space-y-3">
                                        <Label>Load Test Case from Database</Label>
                                        <Select value={selectedTestCaseId} onValueChange={setSelectedTestCaseId}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select a test case..." />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {testCases.map((tc) => (
                                                    <SelectItem key={tc.id} value={tc.id.toString()}>
                                                        {tc.title}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        <Button
                                            onClick={handleLoadFromDatabase}
                                            disabled={isConvertingToJson || !selectedTestCaseId}
                                            variant="outline"
                                            className="w-full"
                                        >
                                            {isConvertingToJson ? (
                                                <>
                                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                    Converting...
                                                </>
                                            ) : (
                                                <>
                                                    <Sparkles className="mr-2 h-4 w-4" />
                                                    Load & Convert with AI
                                                </>
                                            )}
                                        </Button>
                                    </div>

                                    {/* AI-Driven Test Generation */}
                                    <div className="border-t pt-4 space-y-3">
                                        <Label className="text-lg font-semibold flex items-center gap-2">
                                            <Sparkles className="h-5 w-5 text-purple-500" />
                                            AI-Driven Test Scenarios
                                        </Label>
                                        <p className="text-sm text-muted-foreground">
                                            Select a test case, AI will generate 5 scenarios and run them automatically
                                        </p>

                                        {/* Project Selection */}
                                        <div className="space-y-2">
                                            <Label>1. Select Project</Label>
                                            <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Choose project..." />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {projects.map((p) => (
                                                        <SelectItem key={p.id} value={p.id.toString()}>
                                                            {p.name}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>

                                        {/* Requirement Selection */}
                                        <div className="space-y-2">
                                            <Label>2. Select Requirement</Label>
                                            <Select
                                                value={selectedRequirementId}
                                                onValueChange={setSelectedRequirementId}
                                                disabled={!selectedProjectId}
                                            >
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Choose requirement..." />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {requirements.map((r) => (
                                                        <SelectItem key={r.id} value={r.id.toString()}>
                                                            {r.title}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>

                                        {/* Test Case Selection */}
                                        <div className="space-y-2">
                                            <Label>3. Select Test Case</Label>
                                            <Select
                                                value={selectedTestCaseId}
                                                onValueChange={setSelectedTestCaseId}
                                                disabled={!selectedRequirementId}
                                            >
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Choose test case..." />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {testCases.map((tc) => (
                                                        <SelectItem key={tc.id} value={tc.id.toString()}>
                                                            {tc.title}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>

                                        {/* Generate & Run Button */}
                                        <Button
                                            onClick={handleGenerateAndRunScenarios}
                                            disabled={isGeneratingScenarios || !selectedTestCaseId}
                                            className="w-full bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700"
                                            size="lg"
                                        >
                                            {isGeneratingScenarios ? (
                                                <>
                                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                                    {currentScenario > 0 ? `Running Scenario ${currentScenario}/5...` : "Generating Scenarios..."}
                                                </>
                                            ) : (
                                                <>
                                                    <Sparkles className="mr-2 h-5 w-5" />
                                                    Generate 5 Scenarios & Auto-Run
                                                </>
                                            )}
                                        </Button>

                                        {/* Scenario Progress */}
                                        {scenarios.length > 0 && (
                                            <div className="mt-4 space-y-2">
                                                <Label>Scenario Results</Label>
                                                <div className="space-y-2">
                                                    {scenarios.map((scenario, idx) => (
                                                        <Card key={idx} className="p-3">
                                                            <div className="flex items-center justify-between">
                                                                <span className="text-sm font-medium">
                                                                    Scenario {idx + 1}: {scenario.title}
                                                                </span>
                                                                {scenario.result ? (
                                                                    scenario.result.passed > 0 ? (
                                                                        <Badge className="bg-green-500">✓ Passed</Badge>
                                                                    ) : (
                                                                        <Badge variant="destructive">✗ Failed</Badge>
                                                                    )
                                                                ) : (
                                                                    <Badge variant="outline">Pending</Badge>
                                                                )}
                                                            </div>
                                                        </Card>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Test Cases Input */}
                                    <div className="space-y-2">
                                        <Label htmlFor="testInput">Test Cases JSON</Label>
                                        <Textarea
                                            id="testInput"
                                            value={testInput}
                                            onChange={(e) => setTestInput(e.target.value)}
                                            placeholder="Paste your test cases JSON here..."
                                            className="font-mono text-sm min-h-[400px]"
                                        />
                                    </div>

                                    {/* Action Buttons */}
                                    <div className="flex gap-2 flex-wrap">
                                        <Button
                                            onClick={runTests}
                                            disabled={isRunning}
                                            className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90"
                                        >
                                            {isRunning ? (
                                                <>
                                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                    Running...
                                                </>
                                            ) : (
                                                <>
                                                    <Play className="mr-2 h-4 w-4" />
                                                    Run Tests
                                                </>
                                            )}
                                        </Button>

                                        <Button variant="outline" onClick={loadSample}>
                                            <FileCode className="mr-2 h-4 w-4" />
                                            Load Sample
                                        </Button>

                                        <Button variant="outline" asChild>
                                            <label htmlFor="fileUpload" className="cursor-pointer">
                                                <Upload className="mr-2 h-4 w-4" />
                                                Upload File
                                                <input
                                                    id="fileUpload"
                                                    type="file"
                                                    accept=".json"
                                                    className="hidden"
                                                    onChange={handleFileUpload}
                                                />
                                            </label>
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Results Section */}
                            <Card className="border-2">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <CheckCircle2 className="h-5 w-5" />
                                        Execution Results
                                    </CardTitle>
                                    <CardDescription>
                                        Real-time test execution results and metrics
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {isRunning && (
                                        <div className="flex flex-col items-center justify-center py-12 space-y-4">
                                            <Loader2 className="h-12 w-12 animate-spin text-primary" />
                                            <p className="text-sm text-muted-foreground">Executing tests...</p>
                                        </div>
                                    )}

                                    {!isRunning && !results && (
                                        <div className="flex flex-col items-center justify-center py-12 space-y-4 text-center">
                                            <div className="rounded-full bg-muted p-4">
                                                <Play className="h-8 w-8 text-muted-foreground" />
                                            </div>
                                            <div>
                                                <p className="font-medium">No results yet</p>
                                                <p className="text-sm text-muted-foreground">
                                                    Configure and run tests to see results here
                                                </p>
                                            </div>
                                        </div>
                                    )}

                                    {results && (
                                        <div className="space-y-6">
                                            {/* Summary Stats */}
                                            <div className="grid grid-cols-4 gap-4">
                                                <div className="text-center p-3 rounded-lg bg-muted">
                                                    <div className="text-2xl font-bold">{results.total_cases}</div>
                                                    <div className="text-xs text-muted-foreground">Total</div>
                                                </div>
                                                <div className="text-center p-3 rounded-lg bg-green-500/10">
                                                    <div className="text-2xl font-bold text-green-600">{results.passed}</div>
                                                    <div className="text-xs text-muted-foreground">Passed</div>
                                                </div>
                                                <div className="text-center p-3 rounded-lg bg-red-500/10">
                                                    <div className="text-2xl font-bold text-red-600">{results.failed}</div>
                                                    <div className="text-xs text-muted-foreground">Failed</div>
                                                </div>
                                                <div className="text-center p-3 rounded-lg bg-yellow-500/10">
                                                    <div className="text-2xl font-bold text-yellow-600">{results.skipped}</div>
                                                    <div className="text-xs text-muted-foreground">Skipped</div>
                                                </div>
                                            </div>

                                            {/* Progress Bar */}
                                            <div className="space-y-2">
                                                <div className="flex justify-between text-sm">
                                                    <span className="text-muted-foreground">Success Rate</span>
                                                    <span className="font-medium">
                                                        {Math.round((results.passed / results.total_cases) * 100)}%
                                                    </span>
                                                </div>
                                                <Progress
                                                    value={(results.passed / results.total_cases) * 100}
                                                    className="h-2"
                                                />
                                            </div>

                                            {/* Duration */}
                                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                <Clock className="h-4 w-4" />
                                                <span>Total duration: {results.total_duration_ms}ms</span>
                                            </div>

                                            {/* Test Case Results */}
                                            <div className="space-y-3 max-h-[600px] overflow-y-auto">
                                                {results.results.map((result, idx) => (
                                                    <Card key={idx} className="border">
                                                        <CardHeader className="pb-3">
                                                            <div className="flex items-start justify-between">
                                                                <div className="space-y-1 flex-1">
                                                                    <div className="flex items-center gap-2">
                                                                        {getStatusIcon(result.status)}
                                                                        <CardTitle className="text-sm">{result.title}</CardTitle>
                                                                    </div>
                                                                    <CardDescription className="text-xs">
                                                                        {result.duration_ms}ms
                                                                    </CardDescription>
                                                                </div>
                                                                <Badge
                                                                    variant="outline"
                                                                    className={getStatusColor(result.status)}
                                                                >
                                                                    {result.status}
                                                                </Badge>
                                                            </div>
                                                        </CardHeader>
                                                        <CardContent className="pt-0">
                                                            <div className="space-y-2">
                                                                {result.steps.map((step) => (
                                                                    <div
                                                                        key={step.step_number}
                                                                        className="flex items-start gap-2 text-sm p-2 rounded-md bg-muted/50"
                                                                    >
                                                                        <div className="flex-shrink-0 mt-0.5">
                                                                            {getStatusIcon(step.status)}
                                                                        </div>
                                                                        <div className="flex-1 min-w-0">
                                                                            <div className="font-medium text-xs">
                                                                                Step {step.step_number}: {step.description}
                                                                            </div>
                                                                            {step.details && (
                                                                                <div className="text-xs text-muted-foreground mt-1">
                                                                                    {step.details}
                                                                                </div>
                                                                            )}
                                                                            {step.error && (
                                                                                <div className="text-xs text-red-500 mt-1">
                                                                                    {step.error}
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                        <div className="text-xs text-muted-foreground flex-shrink-0">
                                                                            {step.duration_ms}ms
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </CardContent>
                                                    </Card>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </TabsContent>

                    {/* Playwright Automation Tab Content */}
                    <TabsContent value="playwright" className="mt-6">
                        <div className="grid gap-6 lg:grid-cols-2">
                            {/* Playwright Configuration */}
                            <Card className="border-2">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Settings2 className="h-5 w-5" />
                                        Playwright Configuration
                                    </CardTitle>
                                    <CardDescription>
                                        Configure browser automation settings for test execution
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {/* Runner Status */}
                                    {playwrightStatus && (
                                        <div className="p-3 rounded-lg bg-muted/50 space-y-2">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-medium">Runner Status</span>
                                                <Badge variant={playwrightStatus.is_running ? "default" : "secondary"}>
                                                    {playwrightStatus.is_running ? "Running" : "Stopped"}
                                                </Badge>
                                            </div>
                                            {playwrightStatus.is_running && (
                                                <>
                                                    <div className="text-xs text-muted-foreground">
                                                        Browser: {playwrightStatus.browser_type}
                                                    </div>
                                                    <div className="text-xs text-muted-foreground">
                                                        Active Contexts: {playwrightStatus.contexts_count}
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    )}

                                    {/* Browser Type */}
                                    <div className="space-y-2">
                                        <Label>Browser Type</Label>
                                        <Select
                                            value={playwrightConfig.browser_type}
                                            onValueChange={(value: "chromium" | "firefox" | "webkit") =>
                                                setPlaywrightConfig({ ...playwrightConfig, browser_type: value })
                                            }
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="chromium">Chromium</SelectItem>
                                                <SelectItem value="firefox">Firefox</SelectItem>
                                                <SelectItem value="webkit">WebKit (Safari)</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    {/* Viewport */}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>Viewport Width</Label>
                                            <Input
                                                type="number"
                                                value={playwrightConfig.viewport.width}
                                                onChange={(e) =>
                                                    setPlaywrightConfig({
                                                        ...playwrightConfig,
                                                        viewport: { ...playwrightConfig.viewport, width: parseInt(e.target.value) },
                                                    })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Viewport Height</Label>
                                            <Input
                                                type="number"
                                                value={playwrightConfig.viewport.height}
                                                onChange={(e) =>
                                                    setPlaywrightConfig({
                                                        ...playwrightConfig,
                                                        viewport: { ...playwrightConfig.viewport, height: parseInt(e.target.value) },
                                                    })
                                                }
                                            />
                                        </div>
                                    </div>

                                    {/* Base URL */}
                                    <div className="space-y-2">
                                        <Label>Base URL</Label>
                                        <Input
                                            value={playwrightConfig.base_url}
                                            onChange={(e) =>
                                                setPlaywrightConfig({ ...playwrightConfig, base_url: e.target.value })
                                            }
                                            placeholder="http://localhost:3000"
                                        />
                                    </div>

                                    {/* Timeout */}
                                    <div className="space-y-2">
                                        <Label>Timeout (ms)</Label>
                                        <Input
                                            type="number"
                                            value={playwrightConfig.timeout}
                                            onChange={(e) =>
                                                setPlaywrightConfig({ ...playwrightConfig, timeout: parseInt(e.target.value) })
                                            }
                                        />
                                    </div>

                                    {/* Environment */}
                                    <div className="space-y-2">
                                        <Label>Environment</Label>
                                        <Select
                                            value={playwrightConfig.environment}
                                            onValueChange={(value) =>
                                                setPlaywrightConfig({ ...playwrightConfig, environment: value })
                                            }
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="development">Development</SelectItem>
                                                <SelectItem value="staging">Staging</SelectItem>
                                                <SelectItem value="production">Production</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    {/* Toggle Options */}
                                    <div className="space-y-3 border-t pt-4">
                                        <div className="flex items-center justify-between">
                                            <Label htmlFor="headless" className="cursor-pointer">Headless Mode</Label>
                                            <Switch
                                                id="headless"
                                                checked={playwrightConfig.headless}
                                                onCheckedChange={(checked) =>
                                                    setPlaywrightConfig({ ...playwrightConfig, headless: checked })
                                                }
                                            />
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <Label htmlFor="trace" className="cursor-pointer">Record Trace</Label>
                                            <Switch
                                                id="trace"
                                                checked={playwrightConfig.record_trace}
                                                onCheckedChange={(checked) =>
                                                    setPlaywrightConfig({ ...playwrightConfig, record_trace: checked })
                                                }
                                            />
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <Label htmlFor="video" className="cursor-pointer">Record Video</Label>
                                            <Switch
                                                id="video"
                                                checked={playwrightConfig.record_video}
                                                onCheckedChange={(checked) =>
                                                    setPlaywrightConfig({ ...playwrightConfig, record_video: checked })
                                                }
                                            />
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <Label htmlFor="screenshot" className="cursor-pointer">Screenshot on Failure</Label>
                                            <Switch
                                                id="screenshot"
                                                checked={playwrightConfig.screenshot_on_failure}
                                                onCheckedChange={(checked) =>
                                                    setPlaywrightConfig({ ...playwrightConfig, screenshot_on_failure: checked })
                                                }
                                            />
                                        </div>
                                    </div>

                                    {/* Test Case Selection */}
                                    <div className="border-t pt-4 space-y-3">
                                        <Label className="text-base font-semibold">Select Test Case</Label>
                                        <div className="space-y-2">
                                            <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select project..." />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {projects.map((p) => (
                                                        <SelectItem key={p.id} value={p.id.toString()}>
                                                            {p.name}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="space-y-2">
                                            <Select
                                                value={selectedRequirementId}
                                                onValueChange={setSelectedRequirementId}
                                                disabled={!selectedProjectId}
                                            >
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select requirement..." />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {requirements.map((r) => (
                                                        <SelectItem key={r.id} value={r.id.toString()}>
                                                            {r.title}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="space-y-2">
                                            <Select
                                                value={selectedTestCaseId}
                                                onValueChange={setSelectedTestCaseId}
                                                disabled={!selectedRequirementId}
                                            >
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select test case..." />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {testCases.map((tc) => (
                                                        <SelectItem key={tc.id} value={tc.id.toString()}>
                                                            {tc.title}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </div>

                                    {/* Execute Button */}
                                    <div className="flex gap-2">
                                        <Button
                                            onClick={executeWithPlaywright}
                                            disabled={isPlaywrightRunning || !selectedTestCaseId}
                                            className="flex-1 bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700"
                                        >
                                            {isPlaywrightRunning ? (
                                                <>
                                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                    Executing...
                                                </>
                                            ) : (
                                                <>
                                                    <Play className="mr-2 h-4 w-4" />
                                                    Execute with Playwright
                                                </>
                                            )}
                                        </Button>
                                        {isPlaywrightRunning && (
                                            <Button variant="destructive" onClick={stopExecution}>
                                                <StopCircle className="h-4 w-4" />
                                            </Button>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Playwright Results */}
                            <Card className="border-2">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Monitor className="h-5 w-5" />
                                        Playwright Execution Results
                                    </CardTitle>
                                    <CardDescription>
                                        Browser automation test results with traces and screenshots
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {isPlaywrightRunning && (
                                        <div className="flex flex-col items-center justify-center py-12 space-y-4">
                                            <div className="relative">
                                                <Loader2 className="h-12 w-12 animate-spin text-blue-500" />
                                                <Monitor className="h-6 w-6 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-blue-500" />
                                            </div>
                                            <p className="text-sm text-muted-foreground">
                                                Running browser automation...
                                            </p>
                                        </div>
                                    )}

                                    {!isPlaywrightRunning && !playwrightResult && (
                                        <div className="flex flex-col items-center justify-center py-12 space-y-4 text-center">
                                            <div className="rounded-full bg-muted p-4">
                                                <Monitor className="h-8 w-8 text-muted-foreground" />
                                            </div>
                                            <div>
                                                <p className="font-medium">No execution results</p>
                                                <p className="text-sm text-muted-foreground">
                                                    Select a test case and click Execute to run browser automation
                                                </p>
                                            </div>
                                        </div>
                                    )}

                                    {playwrightResult && (
                                        <div className="space-y-6">
                                            {/* Status Header */}
                                            <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                                                <div className="flex items-center gap-3">
                                                    {playwrightResult.status === "passed" ? (
                                                        <CheckCircle2 className="h-8 w-8 text-green-500" />
                                                    ) : (
                                                        <XCircle className="h-8 w-8 text-red-500" />
                                                    )}
                                                    <div>
                                                        <div className="font-semibold text-lg">
                                                            {playwrightResult.status === "passed" ? "Test Passed" : "Test Failed"}
                                                        </div>
                                                        <div className="text-sm text-muted-foreground">
                                                            Execution #{playwrightResult.execution_id}
                                                        </div>
                                                    </div>
                                                </div>
                                                <Badge
                                                    variant="outline"
                                                    className={
                                                        playwrightResult.status === "passed"
                                                            ? "bg-green-500/10 text-green-500 border-green-500/20"
                                                            : "bg-red-500/10 text-red-500 border-red-500/20"
                                                    }
                                                >
                                                    {playwrightResult.browser_type}
                                                </Badge>
                                            </div>

                                            {/* Metrics */}
                                            <div className="grid grid-cols-3 gap-4">
                                                <div className="text-center p-3 rounded-lg bg-muted">
                                                    <div className="text-xl font-bold">{playwrightResult.duration_ms.toFixed(0)}ms</div>
                                                    <div className="text-xs text-muted-foreground">Duration</div>
                                                </div>
                                                <div className="text-center p-3 rounded-lg bg-muted">
                                                    <div className="text-xl font-bold">{playwrightResult.steps.length}</div>
                                                    <div className="text-xs text-muted-foreground">Steps</div>
                                                </div>
                                                <div className="text-center p-3 rounded-lg bg-muted">
                                                    <div className="text-xl font-bold">{playwrightResult.network_logs_count}</div>
                                                    <div className="text-xs text-muted-foreground">Network Requests</div>
                                                </div>
                                            </div>

                                            {/* Action Buttons */}
                                            <div className="flex gap-2 flex-wrap">
                                                {playwrightResult.trace_path && (
                                                    <Button variant="outline" size="sm" onClick={downloadTrace}>
                                                        <FileDown className="mr-2 h-4 w-4" />
                                                        Download Trace
                                                    </Button>
                                                )}
                                                {playwrightResult.screenshot_path && (
                                                    <Button variant="outline" size="sm" onClick={downloadScreenshot}>
                                                        <Camera className="mr-2 h-4 w-4" />
                                                        View Screenshot
                                                    </Button>
                                                )}
                                                <Button variant="outline" size="sm" onClick={fetchPlaywrightStatus}>
                                                    <RefreshCw className="mr-2 h-4 w-4" />
                                                    Refresh Status
                                                </Button>
                                            </div>

                                            {/* Error Message */}
                                            {playwrightResult.error_message && (
                                                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                                    <div className="text-sm font-medium text-red-500">Error</div>
                                                    <div className="text-sm text-red-400 mt-1">
                                                        {playwrightResult.error_message}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Defect Created */}
                                            {playwrightResult.defect_id && (
                                                <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                                                    <div className="text-sm font-medium text-yellow-600">
                                                        Defect Created: DEF-{playwrightResult.defect_id}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Steps */}
                                            <div className="space-y-3 max-h-[400px] overflow-y-auto">
                                                <Label>Execution Steps</Label>
                                                {playwrightResult.steps.map((step) => (
                                                    <div
                                                        key={step.step_number}
                                                        className="flex items-start gap-2 text-sm p-3 rounded-md bg-muted/50 border"
                                                    >
                                                        <div className="flex-shrink-0 mt-0.5">
                                                            {getStatusIcon(step.status)}
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <div className="font-medium">
                                                                Step {step.step_number}: {step.action_type}
                                                            </div>
                                                            <div className="text-xs text-muted-foreground">
                                                                {step.description}
                                                            </div>
                                                            {step.selector && (
                                                                <div className="text-xs text-muted-foreground font-mono mt-1">
                                                                    Selector: {step.selector}
                                                                </div>
                                                            )}
                                                            {step.error && (
                                                                <div className="text-xs text-red-500 mt-1">
                                                                    {step.error}
                                                                </div>
                                                            )}
                                                        </div>
                                                        <div className="text-xs text-muted-foreground flex-shrink-0">
                                                            {step.duration_ms.toFixed(0)}ms
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </TabsContent>
                </Tabs>
            </div>
        </DashboardLayout>
    );
}
