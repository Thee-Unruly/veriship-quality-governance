import { useState } from "react";
import { toast } from "sonner";

interface UseCrudOptions {
    baseUrl: string;
    onSuccess?: () => void;
}

export function useCrud<T extends { id?: number }>(options: UseCrudOptions) {
    const { baseUrl, onSuccess } = options;
    const [loading, setLoading] = useState(false);

    const create = async (data: Omit<T, "id">) => {
        setLoading(true);
        try {
            const response = await fetch(`${baseUrl}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            toast.success("Created successfully!");
            onSuccess?.();
            return result;
        } catch (err) {
            toast.error(`Error: ${err instanceof Error ? err.message : "Failed to create"}`);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const update = async (id: number, data: Partial<T>) => {
        setLoading(true);
        try {
            const response = await fetch(`${baseUrl}/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            toast.success("Updated successfully!");
            onSuccess?.();
            return result;
        } catch (err) {
            toast.error(`Error: ${err instanceof Error ? err.message : "Failed to update"}`);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const delete_ = async (id: number) => {
        setLoading(true);
        try {
            const response = await fetch(`${baseUrl}/${id}`, {
                method: "DELETE",
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            toast.success("Deleted successfully!");
            onSuccess?.();
        } catch (err) {
            toast.error(`Error: ${err instanceof Error ? err.message : "Failed to delete"}`);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    return { create, update, delete: delete_, loading };
}
