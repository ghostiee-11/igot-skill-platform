export type DomainCode = "statistical" | "technical" | "digital_governance" | "behavioural";

export interface DomainGap {
  domain_code: DomainCode;
  domain_name: string;
  target_level: number;
  current_level: number;
  gap: number;
  generated_at: string;
}

export interface CompetencyRecentEvidence {
  title: string;
  type: string;
  score_pct: number;
  date: string;
}

export interface DomainCompetency {
  id?: number;
  code: string;
  name: string;
  level: number;
  mastery_percent?: number;
  target_level?: number;
  gap?: number;
  status?: "Strong" | "Developing" | "Gap";
  status_color?: "emerald" | "amber" | "rose";
  evidence_source: string | null;
  evidence_count?: number;
  recent_evidence?: CompetencyRecentEvidence[];
}

export interface DomainCourse {
  id: number;
  title: string;
  overview: string;
  difficulty: string;
  duration_hours: number;
  category: string;
  recommended: boolean;
  reason: string | null;
}

export interface DomainDetail {
  domain: { code: DomainCode; name: string; description: string | null };
  target_level: number | null;
  current_level: number | null;
  gap: number | null;
  analyzed_at: string | null;
  competencies: DomainCompetency[];
  courses: DomainCourse[];
  is_default_framework: boolean;
}

export type RecommendationStatus = "pending" | "enrolled" | "dismissed";

export interface Recommendation {
  id: number;
  course_id: number | null;
  course_title: string | null;
  reason: string;
  score: number;
  status: RecommendationStatus;
  generated_at: string;
  type?: "course" | "lab" | "cyber_sandbox" | "adaptive_exam" | "ai_interview" | "quiz" | "revision";
  category?: string;
  difficulty?: string;
  duration?: string;
  target_competency?: string;
  href?: string;
}

export interface QuizQuestion {
  id: number;
  order: number;
  question: string;
  options: string[];
  concept: string | null;
  correct_index?: number;
  explanation?: string;
}

export interface Quiz {
  id: number;
  title: string;
  source_name: string;
  source_type: string;
  difficulty: string;
  generator: string;
  created_at: string | null;
  creator_name: string | null;
  can_manage: boolean;
  question_count: number;
  questions: QuizQuestion[];
}

export type QuizSummary = Omit<Quiz, "questions"> & { best_score: number | null };

export interface QuizResultItem {
  question_id: number;
  selected_index: number | null;
  correct_index: number;
  is_correct: boolean;
  explanation: string | null;
  concept: string | null;
}

export interface QuizResult {
  attempt_id: number;
  score_percent: number;
  correct_count: number;
  total_questions: number;
  band: string;
  feedback: string;
  concepts_to_review: string[];
  results: QuizResultItem[];
}
