import type { Metadata } from "next";

import ReportClient from "./report-client";

export const metadata: Metadata = {
  title: "Match Report — JobFit AI",
  description:
    "Review an explainable resume-to-job match report with evidence rows, ATS gaps, and truth-guarded optimization suggestions.",
};

export default function ReportPage({ params }: { params: { id: string } }) {
  return <ReportClient reportId={params.id} />;
}
