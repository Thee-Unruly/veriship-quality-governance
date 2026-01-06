import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Sparkles, Loader, Copy, CheckCircle2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface GenerateTestCasesModalProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    requirementId: number;
    requirementTitle: string;
}

interface GeneratedTestCase {
    title: string;
    description?: string;
    test_type: string;
    priority: number;
    test_steps: string[];
    expected_result: string;
}

interface GenerationResult {
    generated_test_cases: GeneratedTestCase[];
}

const priorityLabels: Record<number, string> = {
    1: "High",
    2: "High-Medium",
    3: "Medium",
    4: "Medium-Low",
    5: "Low",
};

const testTypeColors: Record<string, string> = {
    Positive: "bg-green-100 text-green-800",
    Negative: "bg-red-100 text-red-800",
    "Edge Case": "bg-orange-100 text-orange-800",
    Performance: "bg-blue-100 text-blue-800",
    Security: "bg-purple-100 text-purple-800",
};

export function GenerateTestCasesModal({
    isOpen,
    onOpenChange,
    requirementId,
    requirementTitle,
}: GenerateTestCasesModalProps) {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<GenerationResult | null>(null);
    const [copied, setCopied] = useState<number | null>(null);
    const { toast } = useToast();

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/api/copilot/generate-test-cases/${requirementId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
            });

            if (!response.ok) {
                throw new Error("Failed to generate test cases");
            }

            const data = await response.json();
            setResult(data);
            toast({ title: "Generation Complete", description: `${data.generated_test_cases.length} test cases generated.` });
        } catch (error) {
            toast({
                title: "Error",
                description: error instanceof Error ? error.message : "Failed to generate test cases",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = (idx: number, testCase: GeneratedTestCase) => {
        const text = `
Title: ${testCase.title}
Description: ${testCase.description || "N/A"}
Type: ${testCase.test_type}
Priority: ${priorityLabels[testCase.priority]}

Test Steps:
${testCase.test_steps.map((step, i) => `${i + 1}. ${step}`).join("\n")}

Expected Result:
${testCase.expected_result}
    `.trim();

        navigator.clipboard.writeText(text);
        setCopied(idx);
        setTimeout(() => setCopied(null), 2000);
        toast({ title: "Copied", description: "Test case copied to clipboard" });
    };

    const handleClose = () => {
        setResult(null);
        onOpenChange(false);
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-accent" />
                        Generate Test Cases
                    </DialogTitle>
                    <DialogDescription>{requirementTitle}</DialogDescription>
                </DialogHeader>

                {!result ? (
                    <div className="space-y-4 py-4">
                        <p className="text-sm text-muted-foreground">
                            The AI will generate test case suggestions covering positive cases, negative cases, edge cases, and more.
                        </p>
                        <Button onClick={handleGenerate} disabled={loading} className="w-full">
                            {loading ? (
                                <>
                                    <Loader className="mr-2 h-4 w-4 animate-spin" />
                                    Generating...
                                </>
                            ) : (
                                "Generate Test Cases"
                            )}
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-4 py-4">
                        <div className="flex items-center justify-between">
                            <h3 className="font-semibold">Suggested Test Cases ({result.generated_test_cases.length})</h3>
                            <Badge variant="outline">{result.generated_test_cases.length} cases</Badge>
                        </div>

                        <div className="space-y-3">
                            {result.generated_test_cases.map((testCase, idx) => (
                                <Card key={idx} className="p-4">
                                    <div className="space-y-3">
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex-1">
                                                <h4 className="font-semibold text-sm">{testCase.title}</h4>
                                                {testCase.description && (
                                                    <p className="text-xs text-muted-foreground mt-1">{testCase.description}</p>
                                                )}
                                            </div>
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={() => handleCopy(idx, testCase)}
                                                className="flex-shrink-0"
                                            >
                                                {copied === idx ? (
                                                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                                                ) : (
                                                    <Copy className="h-4 w-4" />
                                                )}
                                            </Button>
                                        </div>

                                        <div className="flex gap-2">
                                            <Badge
                                                className={testTypeColors[testCase.test_type] || "bg-gray-100 text-gray-800"}
                                            >
                                                {testCase.test_type}
                                            </Badge>
                                            <Badge variant="outline">Priority: {priorityLabels[testCase.priority]}</Badge>
                                        </div>

                                        <div className="text-sm">
                                            <p className="font-semibold text-xs text-muted-foreground mb-2">Test Steps:</p>
                                            <ol className="list-decimal list-inside space-y-1 ml-2">
                                                {testCase.test_steps.map((step, stepIdx) => (
                                                    <li key={stepIdx} className="text-xs text-muted-foreground">
                                                        {step}
                                                    </li>
                                                ))}
                                            </ol>
                                        </div>

                                        <div className="text-sm">
                                            <p className="font-semibold text-xs text-muted-foreground mb-2">Expected Result:</p>
                                            <p className="text-xs text-muted-foreground bg-muted p-2 rounded">{testCase.expected_result}</p>
                                        </div>
                                    </div>
                                </Card>
                            ))}
                        </div>

                        <Button onClick={handleClose} className="w-full">
                            Close
                        </Button>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
}
