export type UserRole = "learner" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  onboarding_completed: boolean;
}

export interface UserProfileData {
  phone: string;
  bio: string;
  education: string;
  work_experience_years: number;
  prior_training: string;
  designation: string;
  department: string;
  job_role: string;
  current_assignment: string;
  areas_of_interest: string[];
  language_pref: string;
  appearance_pref: string;
  daily_goal_minutes?: number;
  current_streak_days?: number;
  onboarding_completed?: boolean;
}

export interface CoursePreview {
  id: number;
  title: string;
  overview: string;
  instructor: string;
  organization: string;
  duration_hours: number;
  difficulty: "beginner" | "intermediate" | "advanced";
  source: "internal" | "external";
  category: string;
  rating: number;
  enrolled_count: number;
  is_popular?: boolean;
  is_new?: boolean;
  modules_count?: number;
  has_assessment?: boolean;
}

export interface LessonSummary {
  id: number;
  module_id?: number;
  title: string;
  content_type: "video" | "reading" | "lab";
  duration_minutes: number;
  has_activity?: boolean;
  completed?: boolean;
  order: number;
}

export interface ModuleSummary {
  id: number;
  title: string;
  description: string;
  order: number;
  lessons_count?: number;
  completed_lessons?: number;
  total_lessons?: number;
  lessons: LessonSummary[];
}

export interface CourseDetail extends CoursePreview {
  counts: {
    videos: number;
    readings: number;
    labs: number;
    assessments: number;
    modules: number;
  };
  skills_gained: string[];
  modules: ModuleSummary[];
  assessment_id: number | null;
  enrollment?: {
    enrollment_id: number;
    status: "in_progress" | "completed";
    progress_percent: number;
    last_lesson_id: number | null;
  } | null;
}

export interface CurrentLesson {
  id: number;
  module_id: number;
  module_title: string;
  title: string;
  content_type: "video" | "reading" | "lab";
  duration_minutes: number;
  content: string;
  video_url?: string;
  completed: boolean;
  activity?: {
    question: string;
    options: string[];
    has_activity: boolean;
    is_completed: boolean;
  } | null;
  prev_lesson_id: number | null;
  next_lesson_id: number | null;
  is_last_lesson: boolean;
}

export interface AssessmentQuestion {
  id: number;
  text: string;
  options: string[];
  order: number;
}

export interface AssessmentDetail {
  id: number;
  course_id: number;
  course_title: string;
  organization: string;
  title: string;
  description: string;
  time_limit_minutes: number;
  pass_threshold_percent: number;
  total_questions: number;
  questions: AssessmentQuestion[];
  last_attempt?: {
    id: number;
    score_percent: number;
    passed: boolean;
    submitted_at: string;
  } | null;
  total_attempts_count: number;
}

export interface CertificateItem {
  certificate_id: string;
  course_id: number;
  course_title: string;
  organization: string;
  instructor: string;
  recipient_name: string;
  issued_date: string;
  score_percent: number;
  verification_status: string;
  duration_hours: number;
}
