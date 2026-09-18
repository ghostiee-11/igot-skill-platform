import { Metadata } from "next";
import CarryforwardAssessmentPage from "@/features/behavioural/components/CarryforwardAssessmentPage";

export const metadata: Metadata = {
  title: "Case-Based Carryforward MCQs | iGot Karmayogi",
  description: "Official administrative case scenarios with branching carryforward MCQs derived from government notices, forms, and proceedings."
};

export default function CasesRoute() {
  return <CarryforwardAssessmentPage />;
}
