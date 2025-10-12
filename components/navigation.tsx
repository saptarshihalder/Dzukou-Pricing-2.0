"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ThemeToggleSimple } from "@/components/theme-toggle";
import { 
  BarChart3, 
  Search, 
  TrendingUp, 
  Target, 
  Home,
  Settings 
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Scraping", href: "/scraping", icon: Search },
  { name: "Competitive Analysis", href: "/competitive-analysis", icon: BarChart3 },
  { name: "Price Recommendations", href: "/pricing-recommendations", icon: Target },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="border-b bg-background shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <TrendingUp className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-foreground">
                Price Optimizer AI
              </span>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navigation.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors",
                      isActive
                        ? "border-primary text-foreground"
                        : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground"
                    )}
                  >
                    <item.icon className="mr-2 h-4 w-4" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <ThemeToggleSimple />
            <Button variant="ghost" size="icon">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
      
      {/* Mobile navigation */}
      <div className="sm:hidden">
        <div className="pt-2 pb-3 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "block pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:bg-muted hover:border-muted-foreground"
                )}
              >
                <div className="flex items-center">
                  <item.icon className="mr-2 h-4 w-4" />
                  {item.name}
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}