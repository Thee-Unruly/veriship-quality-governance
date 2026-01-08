import React, { createContext, useContext, useEffect, useState } from "react";

interface ProjectsContextValue {
    projects: any[];
    loading: boolean;
    refresh: () => Promise<void>;
}

const ProjectsContext = createContext<ProjectsContextValue | undefined>(undefined);

export const ProjectsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [projects, setProjects] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchProjects = async () => {
        setLoading(true);
        try {
            const res = await fetch("http://localhost:8000/api/projects/?_=" + Date.now(), {
                // ensure we don't receive a cached response
                cache: "no-store",
                headers: { "Cache-Control": "no-cache" },
            });
            const data = await res.json();
            // debug log to help trace why UI might show stale projects
            try { console.debug("[ProjectsContext] fetched projects:", data); } catch (e) { }
            setProjects(data || []);
        } catch (err) {
            console.error("Error fetching projects:", err);
            setProjects([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProjects();
    }, []);

    return (
        <ProjectsContext.Provider value={{ projects, loading, refresh: fetchProjects }}>
            {children}
        </ProjectsContext.Provider>
    );
};

export function useProjects() {
    const ctx = useContext(ProjectsContext);
    if (!ctx) throw new Error("useProjects must be used within ProjectsProvider");
    return ctx;
}

export default ProjectsContext;
