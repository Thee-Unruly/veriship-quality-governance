import { useState } from "react";
import { FormModal } from "@/components/ui/form-modal";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useCrud } from "@/hooks/use-crud";

interface CreateTestCaseModalProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    projectId: number;
    onSuccess: () => void;
}

export function CreateTestCaseModal({
    isOpen,
    onOpenChange,
    projectId,
    onSuccess,
}: CreateTestCaseModalProps) {
    const [testId, setTestId] = useState("");
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [testType, setTestType] = useState("manual");
    const [priority, setPriority] = useState("1");

    const { create, loading } = useCrud({
        baseUrl: "http://localhost:8000/api/test-cases",
        onSuccess: () => {
            setTestId("");
            setTitle("");
            setDescription("");
            setTestType("manual");
            setPriority("1");
            onOpenChange(false);
            onSuccess();
        },
    });

    const handleSubmit = async () => {
        if (!testId.trim() || !title.trim()) return;

        await create({
            project_id: projectId,
            test_case_id: testId,
            title,
            description,
            test_type: testType,
            priority: parseInt(priority),
        } as any);
    };

    return (
        <FormModal
            isOpen={isOpen}
            onOpenChange={onOpenChange}
            title="Create New Test Case"
            description="Add a new test case to this project"
            onSubmit={handleSubmit}
            isLoading={loading}
        >
            <div className="space-y-4">
                <div>
                    <Label htmlFor="test-id">Test Case ID *</Label>
                    <Input
                        id="test-id"
                        placeholder="e.g., TC-001"
                        value={testId}
                        onChange={(e) => setTestId(e.target.value)}
                        disabled={loading}
                    />
                </div>
                <div>
                    <Label htmlFor="title">Title *</Label>
                    <Input
                        id="title"
                        placeholder="Test case title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        disabled={loading}
                    />
                </div>
                <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                        id="description"
                        placeholder="Steps and expected results"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={loading}
                        rows={3}
                    />
                </div>
                <div>
                    <Label htmlFor="test-type">Test Type *</Label>
                    <Select value={testType} onValueChange={setTestType} disabled={loading}>
                        <SelectTrigger id="test-type">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="manual">Manual</SelectItem>
                            <SelectItem value="automated">Automated</SelectItem>
                            <SelectItem value="smoke">Smoke</SelectItem>
                            <SelectItem value="regression">Regression</SelectItem>
                            <SelectItem value="performance">Performance</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <div>
                    <Label htmlFor="priority">Priority</Label>
                    <Input
                        id="priority"
                        type="number"
                        min="1"
                        max="5"
                        value={priority}
                        onChange={(e) => setPriority(e.target.value)}
                        disabled={loading}
                    />
                </div>
            </div>
        </FormModal>
    );
}
