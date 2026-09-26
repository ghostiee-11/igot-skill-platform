export interface LabTestCase {
  name: string;
  description?: string;
  test_code: string;
}

export interface LabDetail {
  id: number;
  template_id?: string;
  title: string;
  objective: string;
  language: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  status: string;
  instructions: string;
  starter_code: string;
  constraints?: string[];
  test_cases?: LabTestCase[];
  test_cases_count?: number;
  expected_behavior?: string;
  solution?: {
    id: number;
    reference_code: string;
    explanation?: string;
  };
  latest_validation?: any;
  created_at?: string;
  tags?: string[];
  is_generated?: boolean;
}

export interface NotebookCell {
  id: string;
  type: "code" | "markdown";
  content: string;
  execution_count?: number | null;
  status?: "idle" | "running" | "success" | "error";
  output?: string | null;
  stdout?: string | null;
  stderr?: string | null;
  duration_ms?: number;
}

export interface TestResultItem {
  name: string;
  passed: boolean;
  error?: string | null;
  duration_ms: number;
}

export interface LabExecutionResult {
  lab_id: number;
  all_passed: boolean;
  passed_tests_count: number;
  total_tests_count: number;
  test_results: TestResultItem[];
  execution_time_ms: number;
  stdout?: string | null;
  stderr?: string | null;
  exit_code: number;
  feedback?: string | null;
}

export interface CellExecutionResult {
  success: boolean;
  output?: string | null;
  stdout?: string | null;
  stderr?: string | null;
  execution_time_ms: number;
  exit_code: number;
}
