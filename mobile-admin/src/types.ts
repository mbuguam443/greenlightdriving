export interface AdminUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  role: string;
}

export interface DashboardData {
  total_students: number;
  active_students: number;
  total_payments_this_month: string;
  pending_admissions: number;
  pending_lesson_approvals: number;
  unread_messages: number;
  recent_payments: PaymentRecord[];
  recent_admissions: AdmissionRecord[];
}

export interface StudentRecord {
  id: number;
  user: number;
  student_number: string;
  full_name: string;
  email: string;
  phone: string;
  course_name: string;
  category_name: string;
  package_choice: string;
  branch_name: string;
  instructor_name: string | null;
  status: string;
  enrollment_date: string;
  total_fees: string;
  amount_paid: string;
  balance: string;
  lessons_completed: number;
  total_lessons: number;
  progress_percentage: number;
}

export interface PaymentRecord {
  id: number;
  student_name: string;
  student_number: string;
  receipt_number: string;
  amount: string;
  method: string;
  method_display: string;
  reference_number: string;
  status: string;
  status_display: string;
  description: string;
  created_at: string;
}

export interface StudentDetail {
  student: StudentRecord;
  payments: PaymentRecord[];
  lessons: LessonRecord[];
  notifications: NotificationRecord[];
}

export interface LessonRecord {
  id: number;
  student_name: string;
  student_number: string;
  lesson_item_name: string;
  lesson_type: string;
  date: string;
  status: string;
  remarks: string;
  instructor_name: string | null;
  vehicle_registration: string | null;
  is_approved: boolean;
  submitted_by_student: boolean;
  created_at: string;
}

export interface AdmissionRecord {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  course_name: string;
  category_name: string;
  package_choice: string;
  branch_name: string;
  status: string;
  status_display: string;
  submitted_at: string;
  reviewed_at: string | null;
  reviewed_by_name: string | null;
  notes: string;
}

export interface NotificationRecord {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  notification_type_display: string;
  target_audience: string;
  target_audience_display: string;
  recipient_count: number;
  is_read: boolean;
  created_at: string;
}

export interface ChatMessage {
  id: number;
  user: string;
  role: string;
  is_staff: boolean;
  is_me: boolean;
  content: string;
  time: string;
  date: string;
  created_at: string;
}
