import type { Metadata } from "next";
import QuizHubPage from "@/features/quiz/components/QuizHubPage";

export const metadata: Metadata = {
  title: "AI Quiz Generator | iGOT Karmayogi",
  description: "Generate multiple-choice quizzes with explanations from uploaded learning materials.",
};

export default function Page() {
  return <QuizHubPage />;
}
