"use client";

import { useEffect } from "react";
import posthog from "posthog-js";
import { PostHogProvider } from "posthog-js/react";

const POSTHOG_ENABLED = process.env.NEXT_PUBLIC_POSTHOG_ENABLED === "true";

export default function Providers({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const alreadyLoaded = (posthog as unknown as { __loaded?: boolean }).__loaded;
    if (!POSTHOG_ENABLED || alreadyLoaded) return;

    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY || "", {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com",
      capture_pageview: true,
      capture_pageleave: true,
      autocapture: false,
    });
  }, []);

  if (!POSTHOG_ENABLED) {
    return <>{children}</>;
  }

  return <PostHogProvider client={posthog}>{children}</PostHogProvider>;
}
