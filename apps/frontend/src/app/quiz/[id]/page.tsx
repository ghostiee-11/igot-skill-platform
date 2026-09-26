import type { Metadata } from "next";
import QuizTakePage from "@/features/quiz/components/QuizTakePage";

export const metadata: Metadata = {
  title: "Take Quiz | iGOT Karmayogi",
  description: "Answer AI-generated questions and get instant feedback with explanations.",
};

export default function Page() {
  return <QuizTakePage />;
}
