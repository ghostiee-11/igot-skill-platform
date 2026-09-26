import type { Metadata } from "next";
import CompetencyOverviewPage from "@/features/competency/components/CompetencyOverviewPage";

export const metadata: Metadata = {
  title: "Competency Profile | iGOT Karmayogi",
  description: "Skill-gap analysis across statistical, technical, digital governance, and behavioural competencies.",
};

export default function Page() {
  return <CompetencyOverviewPage />;
}
