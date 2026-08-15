export interface Student {
  id: number;
  student_number: string;
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
  enrollments: StudentEnrollment[];
}

export interface StudentEnrollment {
  id: number;
  course_name: string;
  category_name: string;
  package_choice: string;
  branch_name: string;
  status: string;
  enrollment_date: string;
  expected_graduation: string | null;
  total_fees: string;
  amount_paid: string;
  balance: string;
}

export interface PracticalLesson {
  id: number;
  lesson_item: number;
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
  lesson_item: number | null;
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
  created_at: string;
}

export interface NTSARecord {
  id: number;
  pdl_status: string;
  pdl_status_display: string;
  pdl_date: string | null;
  pdl_number: string;
  theory_exam_status: string;
  theory_exam_status_display: string;
  theory_exam_date: string | null;
  theory_exam_score: number | null;
  practical_exam_status: string;
  practical_exam_status_display: string;
  practical_exam_date: string | null;
  driving_test_status: string;
  driving_test_status_display: string;
  driving_test_date: string | null;
  licence_issued: boolean;
  licence_number: string;
  licence_issue_date: string | null;
  licence_expiry_date: string | null;
  overall_progress: number;
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
}

export interface EventItem {
  id: number;
  title: string;
  description: string;
  category: string;
  event_date: string;
  event_time: string | null;
  end_date: string | null;
  branch_name: string | null;
  location: string;
  is_important: boolean;
}

export interface StudentDocument {
  id: number;
  title: string;
  description: string;
  file: string | null;
  file_extension: string;
  file_size_display: string;
  category: string;
  uploaded_at: string;
}

export interface DashboardData {
  student: Student | null;
  admission: unknown;
  ntsa: NTSARecord | null;
  upcoming_lessons: PracticalLesson[];
  today_lessons: PracticalLesson[];
  recent_payments: Payment[];
  unread_notifications_count: number;
  progress_percentage: number;
  lessons_completed: number;
  total_lessons: number;
  balance: string;
  total_fees: string;
  amount_paid: string;
}

export interface LessonItemOption {
  id: number;
  name: string;
  lesson_type: 'PRACTICAL' | 'THEORY';
}

export interface LessonsData {
  practical_lessons: PracticalLesson[];
  theory_lessons: TheoryLesson[];
  lesson_items: LessonItemOption[];
  summary: {
    completed: number;
    total: number;
    progress_percentage: number;
  };
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

export interface PaymentsData {
  payments: Payment[];
  mpesa_transactions: MpesaTransaction[];
  summary: {
    total_fees: string;
    amount_paid: string;
    balance: string;
  };
}

export interface SiteInfo {
  site_name: string;
  tagline: string;
  phone_primary: string;
  email: string;
  address: string;
  exam_fee: string;
  logo: string | null;
}

export interface Course {
  id: number;
  name: string;
  slug: string;
  category: number;
  category_name: string;
  short_description: string;
  description: string;
  duration: string;
  full_course_price: string;
  half_course_price: string;
  test_only_price: string;
  feature_list: string[];
  image: string | null;
}
