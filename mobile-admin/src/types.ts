export interface Payment {
  id: number;
  receipt_number: string;
  amount: string;
  method: string;
  method_display: string;
  reference_number: string;
  status: string;
  status_display: string;
  description: string;
  student_name: string;
  student_number: string;
  created_at: string;
}

export interface MpesaTransaction {
  id: number;
  phone_number: string;
  amount: string;
  account_reference: string;
  checkout_request_id: string;
  mpesa_receipt: string | null;
  status: string;
  created_at: string;
}

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  notification_type_display: string;
  is_read: boolean;
  reply: string;
  replied_at: string | null;
  created_at: string;
  student_name: string;
  student_number: string;
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

export interface AdminStudent {
  id: number;
  student_number: string;
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    full_name: string;
    phone: string;
  };
  course_name: string;
  category_name: string;
  package_choice: string;
  branch_name: string;
  instructor_name: string | null;
  vehicle_registration: string | null;
  status: string;
  enrollment_date: string;
  expected_graduation: string | null;
  payment_reminder: boolean;
  lessons_completed: number;
  total_lessons: number;
  progress_percentage: number;
  total_fees: string;
  amount_paid: string;
  balance: string;
}

export interface PracticalLesson {
  id: number;
  lesson_item_name: string;
  lesson_type: string;
  date: string;
  status: string;
  remarks: string;
  attended: boolean;
  submitted_by_student: boolean;
  is_approved: boolean;
  instructor_name: string | null;
  vehicle_registration: string | null;
}

export interface TheoryLesson {
  id: number;
  lesson_item_name: string | null;
  topic: string;
  date: string;
  time_start: string | null;
  time_end: string | null;
  status: string;
  notes: string;
  attended: boolean;
  instructor_name: string | null;
}

export interface AdmissionItem {
  id: number;
  admission_number: string;
  full_name: string;
  email: string;
  phone: string;
  gender: string;
  national_id: string;
  address: string;
  date_of_birth: string;
  category_name: string;
  course_name: string;
  package_choice: string;
  branch_name: string;
  preferred_schedule: string;
  status: string;
  created_at: string;
}

export interface DashboardData {
  active_students: number;
  pending_admissions: number;
  pending_approvals_count: number;
  unread_replies_count: number;
  today_lessons_count: number;
  month_revenue: string;
  outstanding_balance: string;
  today_practical: PracticalLesson[];
  today_theory: TheoryLesson[];
  pending_approvals: PracticalLesson[];
  unread_replies: NotificationItem[];
}

export interface StudentsData {
  count: number;
  students: AdminStudent[];
}

export interface StudentDetailData {
  student: AdminStudent;
  payments: Payment[];
  practical_lessons: PracticalLesson[];
  theory_lessons: TheoryLesson[];
  notifications: NotificationItem[];
}

export interface PaymentsData {
  total_completed: string;
  payments: Payment[];
  mpesa_transactions: MpesaTransaction[];
}

export interface AdmissionsData {
  count: number;
  admissions: AdmissionItem[];
}
