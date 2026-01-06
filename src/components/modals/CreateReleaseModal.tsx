import { useState } from "react";
import { FormModal } from "@/components/ui/form-modal";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCrud } from "@/hooks/use-crud";

interface CreateReleaseModalProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    projectId: number;
    onSuccess: () => void;
}

export function CreateReleaseModal({
    isOpen,
    onOpenChange,
    projectId,
    onSuccess,
}: CreateReleaseModalProps) {
    const [releaseId, setReleaseId] = useState("");
    const [version, setVersion] = useState("");
    const [releaseDate, setReleaseDate] = useState("");

    const { create, loading } = useCrud({
        baseUrl: "http://localhost:8000/api/releases",
        onSuccess: () => {
            setReleaseId("");
            setVersion("");
            setReleaseDate("");
            onOpenChange(false);
            onSuccess();
        },
    });

    const handleSubmit = async () => {
        if (!releaseId.trim() || !version.trim()) return;

        const data: any = {
            project_id: projectId,
            release_id: releaseId,
            version,
        };

        if (releaseDate) {
            data.planned_release_date = new Date(releaseDate).toISOString();
        }

        await create(data);
    };

    return (
        <FormModal
            isOpen={isOpen}
            onOpenChange={onOpenChange}
            title="Create New Release"
            description="Plan a new release for this project"
            onSubmit={handleSubmit}
            isLoading={loading}
        >
            <div className="space-y-4">
                <div>
                    <Label htmlFor="release-id">Release ID *</Label>
                    <Input
                        id="release-id"
                        placeholder="e.g., REL-001"
                        value={releaseId}
                        onChange={(e) => setReleaseId(e.target.value)}
                        disabled={loading}
                    />
                </div>
                <div>
                    <Label htmlFor="version">Version *</Label>
                    <Input
                        id="version"
                        placeholder="e.g., v2.4.0"
                        value={version}
                        onChange={(e) => setVersion(e.target.value)}
                        disabled={loading}
                    />
                </div>
                <div>
                    <Label htmlFor="release-date">Planned Release Date</Label>
                    <Input
                        id="release-date"
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
