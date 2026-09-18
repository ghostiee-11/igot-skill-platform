import type { Metadata } from "next";
import CompetencyDomainPage from "@/features/competency/components/CompetencyDomainPage";

export const metadata: Metadata = {
  title: "Competency Domain | iGOT Karmayogi",
  description: "Your level, gaps, and courses for one competency domain of the Official Statistical System.",
};

export default function Page() {
  return <CompetencyDomainPage />;
}
