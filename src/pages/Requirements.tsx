import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText } from "lucide-react";

export default function Requirements() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Requirements</h1>
          <p className="text-muted-foreground">Manage and track requirements with AI-powered analysis</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Requirements Governance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">Requirements management features coming soon.</p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
