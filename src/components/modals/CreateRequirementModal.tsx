import { useState } from "react";
import { FormModal } from "@/components/ui/form-modal";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useCrud } from "@/hooks/use-crud";

interface CreateRequirementModalProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    projectId: number;
    onSuccess: () => void;
}

export function CreateRequirementModal({
    isOpen,
    onOpenChange,
    projectId,
    onSuccess,
}: CreateRequirementModalProps) {
    const [reqId, setReqId] = useState("");
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [priority, setPriority] = useState("1");

    const { create, loading } = useCrud({
        baseUrl: "http://localhost:8000/api/requirements",
        onSuccess: () => {
            setReqId("");
            setTitle("");
            setDescription("");
            setPriority("1");
            onOpenChange(false);
            onSuccess();
        },
    });

    const handleSubmit = async () => {
        if (!reqId.trim() || !title.trim()) return;

        await create({
            project_id: projectId,
            requirement_id: reqId,
            title,
            description,
            priority: parseInt(priority),
            acceptance_criteria: [],
        } as any);
    };

    return (
        <FormModal
            isOpen={isOpen}
            onOpenChange={onOpenChange}
            title="Create New Requirement"
            description="Add a new requirement to this project"
            onSubmit={handleSubmit}
            isLoading={loading}
        >
            <div className="space-y-4">
                <div>
                    <Label htmlFor="req-id">Requirement ID *</Label>
                    <Input
                        id="req-id"
                        placeholder="e.g., REQ-001"
                        value={reqId}
                        onChange={(e) => setReqId(e.target.value)}
                        disabled={loading}
                    />
                </div>
                <div>
                    <Label htmlFor="title">Title *</Label>
                    <Input
                        id="title"
                        placeholder="Requirement title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        disabled={loading}
                    />
                </div>
                <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                        id="description"
                        placeholder="Detailed requirement description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={loading}
                        rows={3}
                    />
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
