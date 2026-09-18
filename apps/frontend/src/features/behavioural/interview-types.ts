export interface BehaviouralCourse {
  course_id: number;
  title: string;
  organization?: string | null;
  category?: string | null;
  overview?: string | null;
}

export interface InterviewStartResponse {
  session_id: string;
  course_id: number;
  course_title: string;
  officer_name: string;
  target_duration_minutes: number;
  initial_ai_question: string;
  current_phase: string;
  primary_competency: string;
}

export interface InterviewTurnResponse {
  turn_number: number;
  ai_question: string;
  phase_name: string;
  phase_target_competency: string;
  elapsed_seconds: number;
  target_duration_minutes: number;
  turns_completed: number;
  is_final_turn: boolean;
  pacing_advice?: string | null;
  acknowledgement_note?: string | null;
  detected_competencies: string[];
  delivery_feedback?: string | null;
}

export interface CompetencyScore {
  competency_name: string;
  score_percent: number;
  rating_band: string;
  key_evidence: string;
  growth_opportunity: string;
}

export interface TranscriptEntry {
  speaker: string;
  content: string;
  timestamp_seconds: number;
  behavioral_tags: string[];
}

export interface InterviewReportData {
  session_id: string;
  course_id: number;
  course_title: string;
  officer_name: string;
  total_duration_formatted: string;
  total_turns: number;
  overall_score_percent: number;
  overall_rating_band: string;
  overall_assessment: string;
  course_understanding: string;
  communication_assessment: string;
  decision_making_assessment: string;
  executive_summary: string;
  competency_scores: Record<string, CompetencyScore>;
  core_strengths: string[];
  areas_for_improvement: string[];
  recommended_upskilling: string[];
  conversation_analysis: string;
  video_behavioural_observations: {
    posture_stability: string;
    posture_stability_score: number | null;
    head_movement_observed: string;
    gaze_alignment_percent: number | null;
    face_presence_percent?: number | null;
    excessive_movement_fidgeting: string;
    observable_summary: string;
  };
  speech_analysis: {
    average_wpm: number | null;
    pace_assessment: string;
    pauses_frequency: string;
    filler_word_count: number | null;
    clarity_rating: string;
    coherence_assessment: string;
    delivery_cadence: string;
  };
  transcript: TranscriptEntry[];
  observable_signals_disclaimer?: string | null;
  evaluation_method?: string | null;
}
