import type { Metadata } from "next";
import { IBM_Plex_Mono } from "next/font/google";
import { QueryProvider } from "@/components/providers/query-provider";
import "./globals.css";

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
});

export const metadata: Metadata = {
  title: "AgentProbe",
  description: "ReAct Agent Observatory",
};

/**
 * Root layout for the AgentProbe application.
 * Applies dark theme, IBM Plex Mono font, and wraps children in QueryProvider.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${ibmPlexMono.variable} dark min-h-screen flex flex-col font-mono antialiased`}
      >
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
