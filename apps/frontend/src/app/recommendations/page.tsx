import type { Metadata } from "next";
import RecommendationsPage from "@/features/recommendations/components/RecommendationsPage";

export const metadata: Metadata = {
  title: "Recommended Courses | iGOT Karmayogi",
  description: "Personalised iGOT Karmayogi course recommendations ranked against your competency gaps.",
};

export default function Page() {
  return <RecommendationsPage />;
}
