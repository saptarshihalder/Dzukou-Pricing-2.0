"use client";

import * as React from "react";
import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon">
        <Sun className="h-4 w-4" />
        <span className="sr-only">Toggle theme</span>
      </Button>
    );
  }

  return (
    <Select value={theme} onValueChange={setTheme}>
      <SelectTrigger className="w-auto border-0 bg-transparent hover:bg-accent">
        <div className="flex items-center">
          {theme === "light" && <Sun className="h-4 w-4" />}
          {theme === "dark" && <Moon className="h-4 w-4" />}
          {theme === "system" && <Monitor className="h-4 w-4" />}
          <span className="sr-only">Toggle theme</span>
        </div>
      </SelectTrigger>
      <SelectContent align="end">
        <SelectItem value="light">
          <div className="flex items-center">
            <Sun className="h-4 w-4 mr-2" />
            Light
          </div>
        </SelectItem>
        <SelectItem value="dark">
          <div className="flex items-center">
            <Moon className="h-4 w-4 mr-2" />
            Dark
          </div>
        </SelectItem>
        <SelectItem value="system">
          <div className="flex items-center">
            <Monitor className="h-4 w-4 mr-2" />
            System
          </div>
        </SelectItem>
      </SelectContent>
    </Select>
  );
}

export function ThemeToggleSimple() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon">
        <Sun className="h-4 w-4" />
        <span className="sr-only">Toggle theme</span>
      </Button>
    );
  }

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  return (
    <Button variant="ghost" size="icon" onClick={toggleTheme}>
      {theme === "dark" ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}