import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bug } from "lucide-react";

export default function Defects() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Defects</h1>
          <p className="text-muted-foreground">Track and manage defects across projects</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bug className="h-5 w-5" />
              Defect Management
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">Defect tracking features coming soon.</p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
