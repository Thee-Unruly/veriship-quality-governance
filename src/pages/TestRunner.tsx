import { useState, useEffect } from "react";
import { Play, Upload, FileCode, Loader2, CheckCircle2, XCircle, Clock, AlertCircle, Sparkles } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Progress } from "@/components/ui/progress";
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
    const [testCases, setTestCases] = useState<any[]>([]);
    const [selectedTestCaseId, setSelectedTestCaseId] = useState("");
    const [isLoadingTestCases, setIsLoadingTestCases] = useState(false);
    const [isConvertingToJson, setIsConvertingToJson] = useState(false);

    // Load test cases from database
    useEffect(() => {
        const loadTestCases = async () => {
            setIsLoadingTestCases(true);
            try {
                const response = await fetch("http://localhost:8000/api/test-cases");
                const data = await response.json();
                setTestCases(Array.isArray(data) ? data : []);
            } catch (error) {
                console.error("Error loading test cases:", error);
            } finally {
                setIsLoadingTestCases(false);
            }
        };
        loadTestCases();
    }, []);

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
                        Execute test cases without database persistence. Perfect for quick trials and debugging.
                    </p>
                </div>

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
            </div>
        </DashboardLayout>
    );
}
