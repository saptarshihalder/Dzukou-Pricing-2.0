"use client";

import { Navigation } from "@/components/navigation";
import { ApiStatusIndicator } from "@/components/ui-helpers";
import { useApiHealth } from "@/lib/hooks";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { isHealthy, lastCheck } = useApiHealth();

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      {/* API Status Bar */}
      <div className="bg-card border-b px-4 py-2">
        <div className="max-w-7xl mx-auto flex justify-end">
          <ApiStatusIndicator isHealthy={isHealthy} lastCheck={lastCheck} />
        </div>
      </div>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-card border-t">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="text-sm text-muted-foreground">
              © 2025 Price Optimizer AI. Built for eco-conscious brands.
            </div>
            <div className="text-sm text-muted-foreground">
              Powered by competitive intelligence and AI optimization
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}