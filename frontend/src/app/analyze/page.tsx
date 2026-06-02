import type { Metadata } from "next";

import AnalyzeClient from "./analyze-client";

export const metadata: Metadata = {
  title: "Analyze CV and Job Description — JobFit AI",
  description:
    "Upload a resume PDF, DOCX, or TXT file and provide a job description by text, URL, or document to generate an explainable AI match report.",
};

export default function AnalyzePage() {
  return <AnalyzeClient />;
}
