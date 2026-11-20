export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "student" | "faculty" | "admin";
  phone?: string;
  avatar_url?: string;
}

export interface StudentProfile {
  id: number;
  roll_number: string;
  full_name: string;
  email: string;
  department: string;
  department_code: string;
  course: string;
  current_semester: number;
  section: string;
  batch: string;
  cgpa: number;
}

export interface SubjectAttendance {
  subject_id: number;
  subject_code: string;
  subject_name: string;
  total_classes: number;
  attended_classes: number;
  percentage: number;
  is_eligible: boolean;
  status_indicator: "Good" | "Warning" | "Critical";
}

export interface AttendanceSummary {
  student_id: number;
  roll_number: string;
  overall_total_classes: number;
  overall_attended_classes: number;
  overall_percentage: number;
  overall_eligible: boolean;
  subjects: SubjectAttendance[];
}

export interface AttendanceTargetResult {
  subject_id?: number;
  subject_name?: string;
  current_attended: number;
  current_total: number;
  current_percentage: number;
  target_percentage: number;
  classes_needed: number;
  can_miss_classes: number;
  message: string;
}

export interface TimetableEntry {
  id: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
  subject_code: string;
  subject_name: string;
  faculty_name: string;
  room_number: string;
}

export interface ExamResultItem {
  subject_code: string;
  subject_name: string;
  credits: number;
  internal_marks: number;
  external_marks: number;
  total_marks: number;
  grade: string;
  grade_points: number;
}

export interface SemesterResult {
  semester: number;
  sgpa: number;
  total_credits: number;
  results: ExamResultItem[];
}

export interface FeeItem {
  id: number;
  fee_type: string;
  academic_year: string;
  semester: number;
  total_amount: number;
  paid_amount: number;
  due_amount: number;
  due_date: string;
  status: "paid" | "partial" | "pending";
}

export interface ToolCall {
  tool_name: string;
  tool_input: any;
  tool_output?: any;
  status: string;
  execution_time_ms?: number;
}

export interface Citation {
  document_title: string;
  page_number: number;
  snippet: string;
  similarity_score?: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  tools_executed?: ToolCall[];
  citations?: Citation[];
  detected_language?: string;
}

export interface CorrectionRequestItem {
  id: number;
  subject_code: string;
  subject_name: string;
  attendance_date: string;
  period_number: number;
  current_status: string;
  requested_status: string;
  reason: string;
  review_status: string;
  faculty_notes?: string;
  created_at: string;
}
