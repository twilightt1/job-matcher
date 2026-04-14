import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JobFit AI — AI Job Match & Resume Optimizer",
  description:
    "Portfolio-grade AI/ML application for resume-job matching, explainable scoring, and truth-guarded resume optimization.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
