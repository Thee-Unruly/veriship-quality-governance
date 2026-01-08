import { useState } from "react";
import { FormModal } from "@/components/ui/form-modal";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useCrud } from "@/hooks/use-crud";
import { useProjects } from "@/context/ProjectsContext";

interface CreateProjectModalProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

interface ProjectData {
    name: string;
    description: string;
    target_release_date?: string;
}

export function CreateProjectModal({
    isOpen,
    onOpenChange,
    onSuccess,
}: CreateProjectModalProps) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [releaseDate, setReleaseDate] = useState("");

    const { refresh } = useProjects();

    const { create, loading } = useCrud({
        baseUrl: "http://localhost:8000/api/projects",
        onSuccess: async () => {
            setName("");
            setDescription("");
            setReleaseDate("");
            onOpenChange(false);
            onSuccess();
            // refresh global projects list so other pages update
            try { await refresh(); } catch (e) { /* ignore */ }
        },
    });

    const handleSubmit = async () => {
        if (!name.trim()) return;

        const data: ProjectData = {
            name,
            description,
        };

        if (releaseDate) {
            data.target_release_date = new Date(releaseDate).toISOString();
        }

        await create(data as any);
    };

    return (
        <FormModal
            isOpen={isOpen}
            onOpenChange={onOpenChange}
            title="Create New Project"
            description="Add a new project to the platform"
            onSubmit={handleSubmit}
            isLoading={loading}
        >
            <div className="space-y-4">
                <div>
                    <Label htmlFor="name">Project Name *</Label>
                    <Input
                        id="name"
                        placeholder="e.g., Project Alpha"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        disabled={loading}
                    />
                </div>
                <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                        id="description"
                        placeholder="Brief description of the project"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={loading}
                        rows={3}
                    />
                </div>
                <div>
                    <Label htmlFor="releaseDate">Target Release Date</Label>
                    <Input
                        id="releaseDate"
                        type="date"
                        value={releaseDate}
                        onChange={(e) => setReleaseDate(e.target.value)}
                        disabled={loading}
                    />
                </div>
            </div>
        </FormModal>
    );
}
