import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckSquare } from "lucide-react";

export default function TestCases() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Test Cases</h1>
          <p className="text-muted-foreground">Design, execute, and manage test cases</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckSquare className="h-5 w-5" />
              Test Case Management
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">Test case management features coming soon.</p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
