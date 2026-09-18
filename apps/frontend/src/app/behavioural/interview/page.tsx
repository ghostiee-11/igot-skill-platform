import { Metadata } from "next";
import LiveInterviewPage from "@/features/behavioural/components/LiveInterviewPage";

export const metadata: Metadata = {
  title: "AI Live Oral Interview Board | iGot Karmayogi",
  description: "Live video feed competency interview evaluating course mastery and the 6 civil service behavioral competencies with 25-35 minute pacing."
};

export default function InterviewRoute() {
  return <LiveInterviewPage />;
}
