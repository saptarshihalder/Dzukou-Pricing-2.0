import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw, AlertCircle, Wifi, WifiOff } from "lucide-react";

interface LoadingSkeletonProps {
  rows?: number;
  className?: string;
}

export function LoadingSkeleton({ rows = 5, className }: LoadingSkeletonProps) {
  return (
    <div className={className}>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center space-x-4 mb-4">
          <Skeleton className="h-12 w-12 rounded-full" />
          <div className="space-y-2 flex-1">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

interface LoadingCardProps {
  title?: string;
  description?: string;
  rows?: number;
}

export function LoadingCard({ title = "Loading...", description, rows = 3 }: LoadingCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
          {title}
        </CardTitle>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </CardHeader>
      <CardContent>
        <LoadingSkeleton rows={rows} />
      </CardContent>
    </Card>
  );
}

interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}

export function ErrorAlert({ 
  title = "Error", 
  message, 
  onRetry, 
  retryLabel = "Try Again",
  className 
}: ErrorAlertProps) {
  return (
    <Alert variant="destructive" className={className}>
      <AlertCircle className="h-4 w-4" />
      <AlertDescription>
        <div className="flex flex-col space-y-2">
          <div>
            <strong>{title}</strong>
            <p>{message}</p>
          </div>
          {onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry} className="w-fit">
              <RefreshCw className="mr-2 h-4 w-4" />
              {retryLabel}
            </Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  icon?: React.ReactNode;
}

export function EmptyState({ title, description, action, icon }: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      {icon && <div className="mb-4 flex justify-center">{icon}</div>}
      <h3 className="text-lg font-medium text-foreground mb-2">{title}</h3>
      <p className="text-muted-foreground mb-6 max-w-md mx-auto">{description}</p>
      {action && (
        <Button onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}

interface StatusIndicatorProps {
  isHealthy: boolean | null;
  lastCheck?: Date | null;
}

export function ApiStatusIndicator({ isHealthy, lastCheck }: StatusIndicatorProps) {
  const getStatusColor = () => {
    if (isHealthy === null) return "text-muted-foreground";
    return isHealthy ? "text-green-500" : "text-red-500";
  };

  const getStatusIcon = () => {
    if (isHealthy === null) return <RefreshCw className="h-4 w-4 animate-spin" />;
    return isHealthy ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />;
  };

  const getStatusText = () => {
    if (isHealthy === null) return "Checking...";
    return isHealthy ? "API Connected" : "API Offline";
  };

  return (
    <div className={`flex items-center space-x-2 text-sm ${getStatusColor()}`}>
      {getStatusIcon()}
      <span>{getStatusText()}</span>
      {lastCheck && (
        <span className="text-xs text-muted-foreground">
          ({lastCheck.toLocaleTimeString()})
        </span>
      )}
    </div>
  );
}

interface DataTableSkeletonProps {
  columns: number;
  rows?: number;
}

export function DataTableSkeleton({ columns, rows = 5 }: DataTableSkeletonProps) {
  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex space-x-4 mb-4 pb-2 border-b">
        {Array.from({ length: columns }, (_, i) => (
          <Skeleton key={i} className="h-4 w-24" />
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex space-x-4 mb-3">
          {Array.from({ length: columns }, (_, j) => (
            <Skeleton key={j} className="h-6 w-20" />
          ))}
        </div>
      ))}
    </div>
  );
}

interface ProgressIndicatorProps {
  current: number;
  total: number;
  label?: string;
  showPercentage?: boolean;
}

export function ProgressIndicator({ 
  current, 
  total, 
  label, 
  showPercentage = true 
}: ProgressIndicatorProps) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  
  return (
    <div className="space-y-2">
      {(label || showPercentage) && (
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">{label}</span>
          {showPercentage && (
            <span className="font-medium">{current} / {total} ({percentage}%)</span>
          )}
        </div>
      )}
      <div className="w-full bg-muted rounded-full h-2">
        <div 
          className="bg-primary h-2 rounded-full transition-all duration-300" 
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}