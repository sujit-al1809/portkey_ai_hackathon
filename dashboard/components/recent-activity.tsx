import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity, Lightbulb, BarChart3, RefreshCw } from "lucide-react";

interface RecentActivityProps {
  activities?: Array<{
    type: string;
    message: string;
    time: string;
  }>;
}

export function RecentActivity({ activities }: RecentActivityProps) {
  const activityData = activities || [
    {
      type: "analysis",
      message: "Analyzed 5 new prompts across 2 models",
      time: "2 minutes ago",
    },
    {
      type: "recommendation",
      message: "New optimization recommendation available",
      time: "15 minutes ago",
    },
    {
      type: "refresh",
      message: "Dashboard data refreshed",
      time: "30 minutes ago",
    },
    {
      type: "analysis",
      message: "Quality evaluation completed for batch",
      time: "1 hour ago",
    },
  ];

  const getIcon = (type: string) => {
    switch (type) {
      case "analysis":
        return <BarChart3 className="h-4 w-4" />;
      case "recommendation":
        return <Lightbulb className="h-4 w-4" />;
      case "refresh":
        return <RefreshCw className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>
          Latest system events and updates
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px]">
          <div className="space-y-4">
            {activityData.map((activity, index) => (
              <div
                key={index}
                className="flex gap-3 items-start p-3 rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="mt-0.5 p-2 rounded-full bg-primary/10 text-primary">
                  {getIcon(activity.type)}
                </div>
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {activity.message}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {activity.time}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
