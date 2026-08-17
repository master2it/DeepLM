"use client";

import * as React from "react";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "@/lib/utils";

const Tabs = TabsPrimitive.Root;

const TabsList = React.forwardRef<
  React.ComponentRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "grid h-auto w-full grid-cols-4 gap-0 rounded-none bg-zinc-900 p-0 text-zinc-400 sm:inline-flex sm:h-11 sm:w-auto sm:flex-wrap sm:items-center sm:justify-center sm:gap-1 sm:rounded-lg sm:bg-zinc-800 sm:p-1",
      className
    )}
    {...props}
  />
));
TabsList.displayName = TabsPrimitive.List.displayName;

const TabsTrigger = React.forwardRef<
  React.ComponentRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      "inline-flex min-h-12 w-full flex-col items-center justify-center gap-0.5 rounded-none px-1 py-1.5 text-center text-[10px] font-semibold leading-tight ring-offset-zinc-950 transition-all focus-visible:outline-none data-[state=active]:bg-transparent data-[state=active]:text-zinc-50 sm:min-h-10 sm:w-auto sm:flex-row sm:whitespace-nowrap sm:rounded-md sm:px-4 sm:py-1.5 sm:text-sm sm:data-[state=active]:bg-zinc-700",
      className
    )}
    {...props}
  />
));
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

const TabsContent = React.forwardRef<
  React.ComponentRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn("mt-4 focus-visible:outline-none", className)}
    {...props}
  />
));
TabsContent.displayName = TabsPrimitive.Content.displayName;

export { Tabs, TabsList, TabsTrigger, TabsContent };
