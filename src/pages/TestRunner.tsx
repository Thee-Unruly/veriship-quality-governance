import { useState, useEffect } from "react";
import { Play, Upload, FileCode, Loader2, Sparkles, Monitor, Globe, Camera, FileDown, RefreshCw, StopCircle, Eye, EyeOff, Film, Image, RotateCcw } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    TestRunnerHeader,
    EmptyState,
    ConfigCard,
    ResultsSummary,
    StepResult,
    TestCaseSelector,
    ToggleOption,
    LoadingState,
    ScenarioCard,
} from "@/components/test-runner";

// Types
interface StepResultType {
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
    steps: StepResultType[];
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

    // Playwright State
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
        fetchPlaywrightStatus();
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
                title: data.status === "passed" ? "Test Passed ✓" : "Test Failed",
                description: `Completed in ${(data.duration_ms / 1000).toFixed(1)}s`,
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

    const stopExecution = async () => {
        if (!playwrightResult?.execution_id) return;
        try {
            await fetch(`http://localhost:8000/api/automation/executions/${playwrightResult.execution_id}`, {
                method: "DELETE",
            });
            toast({ title: "Execution stopped", description: "Test was cancelled" });
        } catch (error) {
            console.error("Error stopping execution:", error);
        }
    };

    const downloadTrace = () => {
        if (!playwrightResult?.execution_id) return;
        window.open(
            `http://localhost:8000/api/automation/executions/${playwrightResult.execution_id}/trace?download=true`,
            "_blank"
        );
    };

    const downloadScreenshot = () => {
        if (!playwrightResult?.execution_id) return;
        window.open(
            `http://localhost:8000/api/automation/executions/${playwrightResult.execution_id}/screenshot?download=true`,
            "_blank"
        );
    };

    const handleGenerateAndRunScenarios = async () => {
        if (!selectedTestCaseId) {
            toast({
                title: "Missing selection",
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

            toast({ title: "Generating scenarios...", description: "AI is creating 5 test scenarios" });

            const response = await fetch("http://localhost:8000/api/copilot/generate-scenarios", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ testCase: selectedCase, requirement: selectedReq, count: 5 }),
            });

            if (!response.ok) throw new Error("Scenario generation failed");

            const data = await response.json();
            const generatedScenarios = data.scenarios;
            setScenarios(generatedScenarios);

            toast({ title: "Scenarios ready", description: `${generatedScenarios.length} scenarios generated` });

            for (let i = 0; i < generatedScenarios.length; i++) {
                setCurrentScenario(i + 1);
                const runResponse = await fetch("http://localhost:8000/api/trial/run", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        test_cases: [generatedScenarios[i]],
                        target_base_url: baseUrl,
                    }),
                });
                const runResult = await runResponse.json();
                generatedScenarios[i].result = runResult;
                setScenarios([...generatedScenarios]);
            }

            toast({ title: "All scenarios completed", description: "Check results below" });
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
        toast({ title: "Sample loaded", description: "Example test cases ready to run" });
    };

    const handleLoadFromDatabase = async () => {
        if (!selectedTestCaseId) {
            toast({ title: "No selection", description: "Please select a test case", variant: "destructive" });
            return;
        }

        setIsConvertingToJson(true);
        try {
            const selectedCase = testCases.find(tc => tc.id === parseInt(selectedTestCaseId));
            const response = await fetch("http://localhost:8000/api/copilot/convert-test-to-json", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ testCase: selectedCase }),
            });

            if (!response.ok) throw new Error("Conversion failed");

            const data = await response.json();
            setTestInput(JSON.stringify(data.json_format, null, 2));
            toast({ title: "Test case loaded", description: `${selectedCase.title} converted to JSON` });
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
                setTestInput(e.target?.result as string);
                toast({ title: "File loaded", description: `${file.name} loaded successfully` });
            };
            reader.readAsText(file);
        }
    };

    const runTests = async () => {
        if (!testInput.trim()) {
            toast({ title: "No test cases", description: "Please provide test cases to run", variant: "destructive" });
            return;
        }

        try {
            setIsRunning(true);
            setResults(null);

            const parsed = JSON.parse(testInput);
            const response = await fetch("http://localhost:8000/api/trial/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    test_cases: parsed.test_cases || [],
                    target_base_url: parsed.target_base_url || baseUrl,
                }),
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data: TrialRunResponse = await response.json();
            setResults(data);
            toast({
                title: "Tests completed",
                description: `${data.passed} passed, ${data.failed} failed`,
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

    return (
        <DashboardLayout>
            <div className="space-y-8 p-6 max-w-7xl mx-auto">
                {/* Header */}
                <TestRunnerHeader />

                {/* Tab Navigation */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <div className="inline-flex h-12 items-center rounded-xl bg-muted/50 p-1.5 text-muted-foreground border border-border/50">
                        <button
                            onClick={() => setActiveTab("trial")}
                            className={`inline-flex items-center justify-center gap-2.5 rounded-lg px-6 py-2.5 text-sm font-medium transition-all ${
                                activeTab === "trial"
                                    ? "bg-card text-foreground shadow-sm border border-border/50"
                                    : "hover:text-foreground"
                            }`}
                        >
                            <Globe className="h-4 w-4" />
                            <span>Trial Runner</span>
                        </button>
                        <button
                            onClick={() => setActiveTab("playwright")}
                            className={`inline-flex items-center justify-center gap-2.5 rounded-lg px-6 py-2.5 text-sm font-medium transition-all ${
                                activeTab === "playwright"
                                    ? "bg-card text-foreground shadow-sm border border-border/50"
                                    : "hover:text-foreground"
                            }`}
                        >
                            <Monitor className="h-4 w-4" />
                            <span>Playwright</span>
                        </button>
                    </div>

                    {/* Trial Runner Tab */}
                    <TabsContent value="trial" className="mt-8">
                        <div className="grid gap-8 lg:grid-cols-2">
                            {/* Configuration Card */}
                            <ConfigCard
                                icon={FileCode}
                                title="Test Configuration"
                                description="Configure and run API tests with JSON specifications"
                            >
                                {/* Base URL */}
                                <div className="space-y-2">
                                    <Label className="text-sm font-medium">Target Base URL</Label>
                                    <Input
                                        value={baseUrl}
                                        onChange={(e) => setBaseUrl(e.target.value)}
                                        placeholder="http://localhost:8000"
                                        className="font-mono text-sm h-10 rounded-lg border-border/50 focus:border-accent"
                                    />
                                </div>

                                {/* AI Scenarios Section */}
                                <div className="p-5 rounded-xl bg-gradient-to-br from-violet-500/5 via-purple-500/5 to-fuchsia-500/5 border border-violet-500/20 space-y-4">
                                    <div className="flex items-start gap-3">
                                        <div className="p-2 rounded-lg bg-violet-500/20">
                                            <Sparkles className="h-4 w-4 text-violet-500" />
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-foreground">AI-Powered Scenarios</h4>
                                            <p className="text-sm text-muted-foreground mt-0.5">
                                                Generate and run 5 test scenarios automatically
                                            </p>
                                        </div>
                                    </div>

                                    <TestCaseSelector
                                        projects={projects}
                                        requirements={requirements}
                                        testCases={testCases}
                                        selectedProjectId={selectedProjectId}
                                        selectedRequirementId={selectedRequirementId}
                                        selectedTestCaseId={selectedTestCaseId}
                                        onProjectChange={setSelectedProjectId}
                                        onRequirementChange={setSelectedRequirementId}
                                        onTestCaseChange={setSelectedTestCaseId}
                                    />

                                    <Button
                                        onClick={handleGenerateAndRunScenarios}
                                        disabled={isGeneratingScenarios || !selectedTestCaseId}
                                        className="w-full h-11 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-xl font-medium"
                                    >
                                        {isGeneratingScenarios ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                {currentScenario > 0 ? `Running ${currentScenario}/5...` : "Generating..."}
                                            </>
                                        ) : (
                                            <>
                                                <Sparkles className="mr-2 h-4 w-4" />
                                                Generate & Auto-Run 5 Scenarios
                                            </>
                                        )}
                                    </Button>

                                    {/* Scenario Results */}
                                    {scenarios.length > 0 && (
                                        <div className="space-y-2 pt-2">
                                            {scenarios.map((scenario, idx) => (
                                                <ScenarioCard
                                                    key={idx}
                                                    index={idx}
                                                    title={scenario.title}
                                                    result={scenario.result}
                                                    isRunning={currentScenario === idx + 1}
                                                />
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* Manual JSON Input */}
                                <div className="space-y-3 pt-4 border-t border-border/50">
                                    <Label className="text-sm font-medium">Manual JSON Input</Label>
                                    <div className="flex gap-2 mb-3">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={handleLoadFromDatabase}
                                            disabled={isConvertingToJson || !selectedTestCaseId}
                                            className="rounded-lg"
                                        >
                                            {isConvertingToJson ? (
                                                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                                            ) : (
                                                <Sparkles className="mr-2 h-3.5 w-3.5" />
                                            )}
                                            Convert with AI
                                        </Button>
                                        <Button variant="outline" size="sm" onClick={loadSample} className="rounded-lg">
                                            <FileCode className="mr-2 h-3.5 w-3.5" />
                                            Load Sample
                                        </Button>
                                        <Button variant="outline" size="sm" asChild className="rounded-lg">
                                            <label className="cursor-pointer">
                                                <Upload className="mr-2 h-3.5 w-3.5" />
                                                Upload
                                                <input type="file" accept=".json" className="hidden" onChange={handleFileUpload} />
                                            </label>
                                        </Button>
                                    </div>
                                    <Textarea
                                        value={testInput}
                                        onChange={(e) => setTestInput(e.target.value)}
                                        placeholder='{"test_cases": [...]}'
                                        className="font-mono text-sm min-h-[200px] rounded-xl border-border/50 focus:border-accent bg-muted/30"
                                    />
                                    <Button
                                        onClick={runTests}
                                        disabled={isRunning || !testInput.trim()}
                                        className="w-full h-11 bg-gradient-to-r from-accent to-blue-500 hover:from-accent/90 hover:to-blue-500/90 text-white rounded-xl"
                                    >
                                        {isRunning ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Running Tests...
                                            </>
                                        ) : (
                                            <>
                                                <Play className="mr-2 h-4 w-4" />
                                                Run Tests
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </ConfigCard>

                            {/* Results Card */}
                            <ConfigCard
                                icon={Play}
                                title="Execution Results"
                                description="Real-time test execution feedback and metrics"
                            >
                                {isRunning && (
                                    <LoadingState message="Executing tests..." subMessage="This may take a moment" />
                                )}

                                {!isRunning && !results && (
                                    <EmptyState
                                        icon={Play}
                                        title="Ready to test"
                                        description="Configure your tests on the left and click Run to see results here"
                                    />
                                )}

                                {results && (
                                    <div className="space-y-6">
                                        <ResultsSummary
                                            total={results.total_cases}
                                            passed={results.passed}
                                            failed={results.failed}
                                            skipped={results.skipped}
                                            durationMs={results.total_duration_ms}
                                        />

                                        {/* Test Case Details */}
                                        <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                                            {results.results.map((result, idx) => (
                                                <div key={idx} className="p-4 rounded-xl bg-muted/30 border border-border/50 space-y-3">
                                                    <div className="flex items-center justify-between">
                                                        <h4 className="font-medium text-foreground">{result.title}</h4>
                                                        <Badge className={
                                                            result.status === "passed" ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20" :
                                                            result.status === "failed" ? "bg-rose-500/10 text-rose-600 border-rose-500/20" :
                                                            "bg-amber-500/10 text-amber-600 border-amber-500/20"
                                                        }>
                                                            {result.status}
                                                        </Badge>
                                                    </div>
                                                    <div className="space-y-2">
                                                        {result.steps.map((step) => (
                                                            <StepResult
                                                                key={step.step_number}
                                                                stepNumber={step.step_number}
                                                                description={step.description}
                                                                status={step.status}
                                                                durationMs={step.duration_ms}
                                                                details={step.details}
                                                                error={step.error}
                                                            />
                                                        ))}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </ConfigCard>
                        </div>
                    </TabsContent>

                    {/* Playwright Tab */}
                    <TabsContent value="playwright" className="mt-8">
                        <div className="grid gap-8 lg:grid-cols-2">
                            {/* Configuration */}
                            <ConfigCard
                                icon={Monitor}
                                title="Playwright Configuration"
                                description="Configure browser automation for E2E testing"
                            >
                                {/* Status Badge */}
                                {playwrightStatus && (
                                    <div className="flex items-center justify-between p-4 rounded-xl bg-muted/30 border border-border/50">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-2.5 h-2.5 rounded-full ${playwrightStatus.is_running ? 'bg-emerald-500 animate-pulse' : 'bg-muted-foreground'}`} />
                                            <span className="text-sm font-medium">Runner Status</span>
                                        </div>
                                        <Badge variant={playwrightStatus.is_running ? "default" : "secondary"}>
                                            {playwrightStatus.is_running ? "Active" : "Idle"}
                                        </Badge>
                                    </div>
                                )}

                                {/* Browser Selection */}
                                <div className="space-y-2">
                                    <Label className="text-sm font-medium">Browser</Label>
                                    <Select
                                        value={playwrightConfig.browser_type}
                                        onValueChange={(value: "chromium" | "firefox" | "webkit") =>
                                            setPlaywrightConfig({ ...playwrightConfig, browser_type: value })
                                        }
                                    >
                                        <SelectTrigger className="h-10 rounded-lg border-border/50">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent className="bg-card border-border/50 rounded-xl">
                                            <SelectItem value="chromium">Chromium</SelectItem>
                                            <SelectItem value="firefox">Firefox</SelectItem>
                                            <SelectItem value="webkit">WebKit (Safari)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                {/* Viewport */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label className="text-sm font-medium">Width</Label>
                                        <Input
                                            type="number"
                                            value={playwrightConfig.viewport.width}
                                            onChange={(e) =>
                                                setPlaywrightConfig({
                                                    ...playwrightConfig,
                                                    viewport: { ...playwrightConfig.viewport, width: parseInt(e.target.value) || 1280 },
                                                })
                                            }
                                            className="h-10 rounded-lg border-border/50"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="text-sm font-medium">Height</Label>
                                        <Input
                                            type="number"
                                            value={playwrightConfig.viewport.height}
                                            onChange={(e) =>
                                                setPlaywrightConfig({
                                                    ...playwrightConfig,
                                                    viewport: { ...playwrightConfig.viewport, height: parseInt(e.target.value) || 720 },
                                                })
                                            }
                                            className="h-10 rounded-lg border-border/50"
                                        />
                                    </div>
                                </div>

                                {/* Base URL & Timeout */}
                                <div className="space-y-2">
                                    <Label className="text-sm font-medium">Base URL</Label>
                                    <Input
                                        value={playwrightConfig.base_url}
                                        onChange={(e) => setPlaywrightConfig({ ...playwrightConfig, base_url: e.target.value })}
                                        placeholder="http://localhost:3000"
                                        className="h-10 rounded-lg border-border/50 font-mono text-sm"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-sm font-medium">Timeout (ms)</Label>
                                    <Input
                                        type="number"
                                        value={playwrightConfig.timeout}
                                        onChange={(e) =>
                                            setPlaywrightConfig({ ...playwrightConfig, timeout: parseInt(e.target.value) || 30000 })
                                        }
                                        className="h-10 rounded-lg border-border/50"
                                    />
                                </div>

                                {/* Environment */}
                                <div className="space-y-2">
                                    <Label className="text-sm font-medium">Environment</Label>
                                    <Select
                                        value={playwrightConfig.environment}
                                        onValueChange={(value) => setPlaywrightConfig({ ...playwrightConfig, environment: value })}
                                    >
                                        <SelectTrigger className="h-10 rounded-lg border-border/50">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent className="bg-card border-border/50 rounded-xl">
                                            <SelectItem value="development">Development</SelectItem>
                                            <SelectItem value="staging">Staging</SelectItem>
                                            <SelectItem value="production">Production</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                {/* Toggle Options */}
                                <div className="space-y-2 pt-4 border-t border-border/50">
                                    <ToggleOption
                                        id="headless"
                                        label="Headless Mode"
                                        description="Run without visible browser window"
                                        checked={playwrightConfig.headless}
                                        onCheckedChange={(checked) => setPlaywrightConfig({ ...playwrightConfig, headless: checked })}
                                        icon={playwrightConfig.headless ? EyeOff : Eye}
                                    />
                                    <ToggleOption
                                        id="trace"
                                        label="Record Trace"
                                        description="Capture detailed execution trace"
                                        checked={playwrightConfig.record_trace}
                                        onCheckedChange={(checked) => setPlaywrightConfig({ ...playwrightConfig, record_trace: checked })}
                                        icon={FileDown}
                                    />
                                    <ToggleOption
                                        id="video"
                                        label="Record Video"
                                        description="Capture video of test execution"
                                        checked={playwrightConfig.record_video}
                                        onCheckedChange={(checked) => setPlaywrightConfig({ ...playwrightConfig, record_video: checked })}
                                        icon={Film}
                                    />
                                    <ToggleOption
                                        id="screenshot"
                                        label="Screenshot on Failure"
                                        description="Capture screenshot when test fails"
                                        checked={playwrightConfig.screenshot_on_failure}
                                        onCheckedChange={(checked) => setPlaywrightConfig({ ...playwrightConfig, screenshot_on_failure: checked })}
                                        icon={Image}
                                    />
                                </div>

                                {/* Test Case Selection */}
                                <div className="pt-4 border-t border-border/50 space-y-4">
                                    <Label className="text-base font-semibold">Select Test Case</Label>
                                    <TestCaseSelector
                                        projects={projects}
                                        requirements={requirements}
                                        testCases={testCases}
                                        selectedProjectId={selectedProjectId}
                                        selectedRequirementId={selectedRequirementId}
                                        selectedTestCaseId={selectedTestCaseId}
                                        onProjectChange={setSelectedProjectId}
                                        onRequirementChange={setSelectedRequirementId}
                                        onTestCaseChange={setSelectedTestCaseId}
                                        compact
                                    />
                                </div>

                                {/* Execute Button */}
                                <div className="flex gap-3 pt-4">
                                    <Button
                                        onClick={executeWithPlaywright}
                                        disabled={isPlaywrightRunning || !selectedTestCaseId}
                                        className="flex-1 h-11 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-xl"
                                    >
                                        {isPlaywrightRunning ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Running...
                                            </>
                                        ) : (
                                            <>
                                                <Play className="mr-2 h-4 w-4" />
                                                Execute Test
                                            </>
                                        )}
                                    </Button>
                                    {isPlaywrightRunning && (
                                        <Button variant="destructive" onClick={stopExecution} className="h-11 px-4 rounded-xl">
                                            <StopCircle className="h-4 w-4" />
                                        </Button>
                                    )}
                                </div>
                            </ConfigCard>

                            {/* Results */}
                            <ConfigCard
                                icon={Monitor}
                                title="Execution Results"
                                description="Browser automation results with traces and screenshots"
                            >
                                {isPlaywrightRunning && (
                                    <LoadingState
                                        icon={Monitor}
                                        message="Running browser automation..."
                                        subMessage="Executing test steps in the browser"
                                    />
                                )}

                                {!isPlaywrightRunning && !playwrightResult && (
                                    <EmptyState
                                        icon={Monitor}
                                        title="No results yet"
                                        description="Select a test case and click Execute to run browser automation"
                                    />
                                )}

                                {playwrightResult && (
                                    <div className="space-y-6">
                                        {/* Status Header */}
                                        <div className={`flex items-center justify-between p-5 rounded-xl border ${
                                            playwrightResult.status === "passed"
                                                ? "bg-emerald-500/5 border-emerald-500/20"
                                                : "bg-rose-500/5 border-rose-500/20"
                                        }`}>
                                            <div className="flex items-center gap-4">
                                                <div className={`p-3 rounded-xl ${
                                                    playwrightResult.status === "passed"
                                                        ? "bg-emerald-500/20"
                                                        : "bg-rose-500/20"
                                                }`}>
                                                    {playwrightResult.status === "passed" ? (
                                                        <Play className="h-6 w-6 text-emerald-500" />
                                                    ) : (
                                                        <StopCircle className="h-6 w-6 text-rose-500" />
                                                    )}
                                                </div>
                                                <div>
                                                    <div className={`font-semibold text-lg ${
                                                        playwrightResult.status === "passed" ? "text-emerald-600" : "text-rose-600"
                                                    }`}>
                                                        {playwrightResult.status === "passed" ? "Test Passed" : "Test Failed"}
                                                    </div>
                                                    <div className="text-sm text-muted-foreground">
                                                        Execution #{playwrightResult.execution_id}
                                                    </div>
                                                </div>
                                            </div>
                                            <Badge variant="outline" className="text-xs">
                                                {playwrightResult.browser_type}
                                            </Badge>
                                        </div>

                                        {/* Metrics */}
                                        <div className="grid grid-cols-3 gap-3">
                                            <div className="p-4 rounded-xl bg-muted/30 border border-border/50 text-center">
                                                <div className="text-xl font-bold text-foreground">
                                                    {(playwrightResult.duration_ms / 1000).toFixed(1)}s
                                                </div>
                                                <div className="text-xs text-muted-foreground mt-1">Duration</div>
                                            </div>
                                            <div className="p-4 rounded-xl bg-muted/30 border border-border/50 text-center">
                                                <div className="text-xl font-bold text-foreground">
                                                    {playwrightResult.steps.length}
                                                </div>
                                                <div className="text-xs text-muted-foreground mt-1">Steps</div>
                                            </div>
                                            <div className="p-4 rounded-xl bg-muted/30 border border-border/50 text-center">
                                                <div className="text-xl font-bold text-foreground">
                                                    {playwrightResult.network_logs_count}
                                                </div>
                                                <div className="text-xs text-muted-foreground mt-1">Requests</div>
                                            </div>
                                        </div>

                                        {/* Actions */}
                                        <div className="flex gap-2 flex-wrap">
                                            {playwrightResult.trace_path && (
                                                <Button variant="outline" size="sm" onClick={downloadTrace} className="rounded-lg">
                                                    <FileDown className="mr-2 h-4 w-4" />
                                                    Download Trace
                                                </Button>
                                            )}
                                            {playwrightResult.screenshot_path && (
                                                <Button variant="outline" size="sm" onClick={downloadScreenshot} className="rounded-lg">
                                                    <Camera className="mr-2 h-4 w-4" />
                                                    View Screenshot
                                                </Button>
                                            )}
                                            <Button variant="outline" size="sm" onClick={fetchPlaywrightStatus} className="rounded-lg">
                                                <RefreshCw className="mr-2 h-4 w-4" />
                                                Refresh
                                            </Button>
                                        </div>

                                        {/* Error */}
                                        {playwrightResult.error_message && (
                                            <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/20">
                                                <div className="text-sm font-medium text-rose-600">Error</div>
                                                <div className="text-sm text-rose-500 mt-1 font-mono">
                                                    {playwrightResult.error_message}
                                                </div>
                                            </div>
                                        )}

                                        {/* Defect */}
                                        {playwrightResult.defect_id && (
                                            <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20">
                                                <div className="text-sm font-medium text-amber-600">
                                                    Defect Created: DEF-{playwrightResult.defect_id}
                                                </div>
                                            </div>
                                        )}

                                        {/* Steps */}
                                        <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                                            <Label className="text-sm font-medium">Execution Steps</Label>
                                            {playwrightResult.steps.map((step) => (
                                                <StepResult
                                                    key={step.step_number}
                                                    stepNumber={step.step_number}
                                                    description={step.description}
                                                    status={step.status}
                                                    durationMs={step.duration_ms}
                                                    actionType={step.action_type}
                                                    selector={step.selector || undefined}
                                                    error={step.error}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </ConfigCard>
                        </div>
                    </TabsContent>
                </Tabs>
            </div>
        </DashboardLayout>
    );
}
