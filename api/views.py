from datetime import date

from django.contrib.auth import authenticate
from django.db import models as dj_models
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from admissions.models import Admission
from core.models import Branch, SiteSettings
from lessons.models import LessonItem, PracticalLesson, TheoryLesson
from ntsa.models import NTSARecord
from payments.models import MpesaTransaction, Payment
from student_portal.models import ChatMessage, Event, Notification, StudentDocument
from students.models import Student
from website.models import BlogPost, ContactMessage, Course, CourseCategory, FAQ, GalleryImage, Testimonial

from .serializers import (
    AdmissionSerializer,
    AdminAdmissionRecordSerializer,
    AdminLessonRecordSerializer,
    AdminNotificationRecordSerializer,
    AdminPaymentRecordSerializer,
    AdminStudentSerializer,
    BlogPostSerializer,
    BranchSerializer,
    ContactMessageSerializer,
    CourseCategorySerializer,
    CourseSerializer,
    EventSerializer,
    FAQSerializer,
    GalleryImageSerializer,
    MpesaTransactionSerializer,
    NTSASerializer,
    NotificationSerializer,
    PaymentSerializer,
    PracticalLessonSerializer,
    RegisterSerializer,
    SiteInfoSerializer,
    StudentDocumentSerializer,
    StudentSerializer,
    TestimonialSerializer,
    TheoryLessonSerializer,
    UserSerializer,
)


class IsStudent(IsAuthenticated):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'STUDENT'
        )


STAFF_ROLES = ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST', 'ACCOUNTANT', 'INSTRUCTOR', 'READ_ONLY_ADMIN')


class IsStaff(IsAuthenticated):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in STAFF_ROLES
        )


def _get_student(request):
    try:
        return Student.objects.select_related('user', 'course', 'category', 'branch', 'instructor').get(
            user=request.user
        )
    except Student.DoesNotExist:
        return None


ADMITTED_STATUSES = ('APPROVED', 'ENROLLED')


def _get_my_admission(user):
    """The most recent admission belonging to this user (by link or email)."""
    from django.db.models import Q
    return (
        Admission.objects.filter(Q(submitted_by=user) | Q(email=user.email))
        .order_by('-created_at')
        .first()
    )


def _access_state(user):
    """Describe a student's access level.

    Returns a dict:
      {
        'level': 'granted' | 'pending' | 'rejected' | 'none',
        'admission': Admission | None,
        'student': Student | None,
      }

    'granted'  -> the student has an enrolled Student profile and their
                  admission (if any) is APPROVED or ENROLLED. Full access.
    'pending'  -> an admission exists but is PENDING. Most services blocked.
    'rejected' -> an admission exists but was REJECTED.
    'none'     -> no admission on record. Can submit one.
    """
    student = None
    try:
        student = Student.objects.filter(user=user).first()
    except Student.DoesNotExist:
        student = None

    admission = None
    if student and student.admission_id:
        admission = student.admission
    if admission is None:
        admission = _get_my_admission(user)

    if admission is None:
        return {'level': 'none', 'admission': None, 'student': student}

    if admission.status in ADMITTED_STATUSES:
        return {'level': 'granted', 'admission': admission, 'student': student}

    if admission.status == 'REJECTED':
        return {'level': 'rejected', 'admission': admission, 'student': student}

    return {'level': 'pending', 'admission': admission, 'student': student}


def _blocked_response(state):
    """Response returned to students whose admission is not granted."""
    from rest_framework import status as drf_status
    if state['level'] == 'none':
        return Response({
            'detail': 'You have not submitted your admission application yet. '
                      'Please submit one to unlock your student services.',
            'code': 'ADMISSION_REQUIRED',
            'admission_status': None,
        }, status=drf_status.HTTP_403_FORBIDDEN)
    if state['level'] == 'rejected':
        return Response({
            'detail': 'Your admission application was not approved. Contact the school for more information.',
            'code': 'ADMISSION_REJECTED',
            'admission_status': 'REJECTED',
        }, status=drf_status.HTTP_403_FORBIDDEN)
    return Response({
        'detail': 'Your admission is still under review. Most services are locked until it is approved.',
        'code': 'ADMISSION_PENDING',
        'admission_status': 'PENDING',
    }, status=drf_status.HTTP_403_FORBIDDEN)


def _require_admission(request):
    """Return (None, None) if access granted, else (state, blocked_response)."""
    state = _access_state(request.user)
    if state['level'] == 'granted':
        return None, None
    return state, _blocked_response(state)


# ============================== AUTH ==============================


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''
        if not email or not password:
            return Response({'detail': 'Email and password are required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({'detail': 'Invalid email or password.'},
                            status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({'detail': 'Your account is inactive. Contact the school.'},
                            status=status.HTTP_403_FORBIDDEN)
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user, context={'request': request}).data,
        })


# ============================== PUBLIC ==============================


class SiteInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        settings = SiteSettings.load()
        return Response(SiteInfoSerializer(settings, context={'request': request}).data)


class CourseListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        courses = Course.objects.filter(is_active=True).select_related('category')
        category = request.GET.get('category')
        if category:
            courses = courses.filter(category__slug=category)
        return Response(CourseSerializer(courses, many=True, context={'request': request}).data)


class CourseCategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = CourseCategory.objects.prefetch_related('courses').all()
        return Response(CourseCategorySerializer(categories, many=True).data)


class BranchListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        branches = Branch.objects.filter(is_active=True)
        return Response(BranchSerializer(branches, many=True, context={'request': request}).data)


class TestimonialListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        testimonials = Testimonial.objects.filter(is_active=True).select_related('course')
        return Response(TestimonialSerializer(testimonials, many=True, context={'request': request}).data)


class FAQListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        faqs = FAQ.objects.filter(is_active=True)
        return Response(FAQSerializer(faqs, many=True).data)


class BlogPostListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        posts = BlogPost.objects.filter(is_published=True).select_related('author')[:10]
        return Response(BlogPostSerializer(posts, many=True, context={'request': request}).data)


class GalleryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        images = GalleryImage.objects.filter(is_active=True)
        return Response(GalleryImageSerializer(images, many=True, context={'request': request}).data)


class PublicEventListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        events = Event.objects.filter(is_active=True, event_date__gte=timezone.now().date())
        return Response(EventSerializer(events, many=True).data)


class ContactView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'detail': 'Message sent. We will get back to you soon.'},
                        status=status.HTTP_201_CREATED)


# ============================== STUDENT ==============================


class StudentDashboardView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)

        admission = Admission.objects.filter(email=request.user.email).order_by('-created_at').first()
        ntsa = NTSARecord.objects.filter(student=student).first()
        upcoming_practical = PracticalLesson.objects.filter(
            student=student, date__gte=timezone.now().date()
        ).select_related('lesson_item', 'instructor__user', 'vehicle').order_by('date')[:5]
        recent_payments = Payment.objects.filter(student=student, status='COMPLETED')[:5]
        unread_notifications = Notification.objects.filter(student=student, is_read=False)
        today_lessons = PracticalLesson.objects.filter(student=student, date=timezone.now().date())

        return Response({
            'student': StudentSerializer(student, context={'request': request}).data,
            'admission': AdmissionSerializer(admission, context={'request': request}).data if admission else None,
            'ntsa': NTSASerializer(ntsa).data if ntsa else None,
            'upcoming_lessons': PracticalLessonSerializer(upcoming_practical, many=True).data,
            'today_lessons': PracticalLessonSerializer(today_lessons, many=True).data,
            'recent_payments': PaymentSerializer(recent_payments, many=True).data,
            'unread_notifications_count': unread_notifications.count(),
            'progress_percentage': student.progress_percentage,
            'lessons_completed': student.lessons_completed,
            'total_lessons': student.total_lessons,
            'balance': str(student.balance),
            'total_fees': str(student.total_fees),
            'amount_paid': str(student.amount_paid),
        })


class StudentLessonsView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        practical = PracticalLesson.objects.filter(student=student).select_related(
            'lesson_item', 'instructor__user', 'vehicle'
        )
        theory = TheoryLesson.objects.filter(student=student).select_related('lesson_item', 'instructor__user')
        lesson_items = LessonItem.objects.filter(is_active=True)
        return Response({
            'practical_lessons': PracticalLessonSerializer(practical, many=True).data,
            'theory_lessons': TheoryLessonSerializer(theory, many=True).data,
            'lesson_items': [{'id': i.id, 'name': i.name, 'lesson_type': i.lesson_type} for i in lesson_items],
            'summary': {
                'completed': student.lessons_completed,
                'total': student.total_lessons,
                'progress_percentage': student.progress_percentage,
            },
        })

    def post(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        item_id = request.data.get('lesson_item')
        if not item_id:
            return Response({'detail': 'Please select a lesson.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = LessonItem.objects.get(pk=item_id, is_active=True)
        except LessonItem.DoesNotExist:
            return Response({'detail': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)

        lesson_date = request.data.get('lesson_date') or timezone.now().date()

        if item.lesson_type == 'PRACTICAL':
            if PracticalLesson.objects.filter(student=student, lesson_item=item).exists():
                return Response({'detail': 'This practical lesson already exists.'},
                                status=status.HTTP_400_BAD_REQUEST)
            lesson = PracticalLesson.objects.create(
                student=student, lesson_item=item, date=lesson_date,
                status='NOT_STARTED', submitted_by_student=True, is_approved=False,
            )
        else:
            if TheoryLesson.objects.filter(student=student, lesson_item=item).exists():
                return Response({'detail': 'This theory lesson already exists.'},
                                status=status.HTTP_400_BAD_REQUEST)
            lesson = TheoryLesson.objects.create(
                student=student, lesson_item=item, topic=item.name, date=lesson_date,
                time_start='08:00', time_end='09:00', status='NOT_STARTED',
            )

        return Response({'detail': f'"{item.name}" submitted for approval.', 'id': lesson.id},
                        status=status.HTTP_201_CREATED)


class StudentAttendanceView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        attendance_date = request.data.get('attendance_date', '').strip()
        try:
            selected_date = date.fromisoformat(attendance_date)
        except (TypeError, ValueError):
            return Response({'detail': 'Please select a valid attendance date.'},
                            status=status.HTTP_400_BAD_REQUEST)

        lesson = PracticalLesson.objects.filter(pk=pk, student=student).first()
        is_practical = lesson is not None
        if lesson:
            lesson.attended = True
            lesson.is_approved = False
            lesson.date = selected_date
            lesson.save(update_fields=['attended', 'is_approved', 'date'])
        else:
            lesson = TheoryLesson.objects.filter(pk=pk, student=student).first()
            if not lesson:
                return Response({'detail': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)
            lesson.attended = True
            lesson.date = selected_date
            lesson.save(update_fields=['attended', 'date'])

        return Response({'detail': 'Attendance submitted.', 'is_practical': is_practical})


class StudentPaymentsView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        payments = Payment.objects.filter(student=student).select_related('student')
        mpesa_txns = MpesaTransaction.objects.filter(student=student)
        return Response({
            'payments': PaymentSerializer(payments, many=True).data,
            'mpesa_transactions': MpesaTransactionSerializer(mpesa_txns, many=True).data,
            'summary': {
                'total_fees': str(student.total_fees),
                'amount_paid': str(student.amount_paid),
                'balance': str(student.balance),
            },
        })


class StudentMpesaInitiateView(APIView):
    """Initiate an M-Pesa STK push from the app."""

    permission_classes = [IsStudent]

    def post(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        phone = (request.data.get('phone_number') or '').strip()
        amount = request.data.get('amount')
        if not phone or not amount:
            return Response({'detail': 'Phone number and amount are required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return Response({'detail': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)
        if amount <= 0:
            return Response({'detail': 'Amount must be greater than zero.'},
                            status=status.HTTP_400_BAD_REQUEST)

        from payments.mpesa_utils import initiate_stk_push
        from payments.models import MpesaTransaction
        from payments.mpesa_utils import format_phone
        transaction = MpesaTransaction.objects.create(
            student=student,
            phone_number=format_phone(phone),
            amount=amount,
            account_reference=student.student_number[:12],
            status='PENDING',
        )
        try:
            response = initiate_stk_push(
                phone, amount,
                account_reference=student.student_number,
                transaction_desc='School Fees Payment',
            )
        except Exception as exc:
            transaction.status = 'FAILED'
            transaction.result_desc = str(exc)
            transaction.save(update_fields=['status', 'result_desc', 'updated_at'])
            return Response({'detail': f'Unable to reach M-Pesa: {exc}'},
                            status=status.HTTP_502_BAD_GATEWAY)

        if not response.get('success'):
            transaction.status = 'FAILED'
            transaction.result_desc = response.get('message', 'M-Pesa request failed.')
            transaction.save(update_fields=['status', 'result_desc', 'updated_at'])
            return Response({'detail': response.get('message', 'M-Pesa request failed.')},
                            status=status.HTTP_502_BAD_GATEWAY)

        transaction.checkout_request_id = response.get('checkout_request_id', '')
        transaction.merchant_request_id = response.get('merchant_request_id', '')
        transaction.save(update_fields=['checkout_request_id', 'merchant_request_id', 'updated_at'])
        return Response({'detail': response.get('message', 'STK push sent. Check your phone.'),
                         'transaction_id': transaction.id,
                         'response': response})


class StudentNotificationsView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        notifications = Notification.objects.filter(student=student)
        return Response(NotificationSerializer(notifications, many=True).data)

    def post(self, request, pk=None):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        try:
            notification = Notification.objects.get(pk=pk, student=student)
        except Notification.DoesNotExist:
            return Response({'detail': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action', 'read')
        if action == 'reply':
            reply = (request.data.get('reply') or '').strip()
            if not reply:
                return Response({'detail': 'Reply cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
            notification.reply = reply
            notification.replied_at = timezone.now()
            notification.is_read = True
            notification.save(update_fields=['reply', 'replied_at', 'is_read'])
        else:
            notification.is_read = True
            notification.save(update_fields=['is_read'])

        return Response(NotificationSerializer(notification).data)


class StudentPushTokenView(APIView):
    permission_classes = [IsStudent]

    def post(self, request):
        # Push token registration must always be allowed (e.g. a pending student
        # still needs to receive admission-status notifications), so it is not gated.
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        token = (request.data.get('push_token') or '').strip()
        if not token:
            return Response({'detail': 'push_token is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        student.push_token = token[:300]
        student.save(update_fields=['push_token'])
        return Response({'detail': 'Push token saved.'})


class StudentEventsView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        upcoming = Event.objects.filter(is_active=True, event_date__gte=timezone.now().date())
        past = Event.objects.filter(is_active=True, event_date__lt=timezone.now().date())
        return Response({
            'upcoming_events': EventSerializer(upcoming, many=True).data,
            'past_events': EventSerializer(past, many=True).data,
        })


class StudentDocumentsView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        docs = StudentDocument.objects.filter(is_active=True).filter(
            dj_models.Q(student__isnull=True) | dj_models.Q(student=student)
        )
        return Response(StudentDocumentSerializer(docs, many=True, context={'request': request}).data)


class StudentNTSAView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        ntsa = NTSARecord.objects.filter(student=student).first()
        if not ntsa:
            return Response(None)
        return Response(NTSASerializer(ntsa).data)


class StudentProfileView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        admission = student.admission
        token = getattr(student, 'push_token', '') or ''
        return Response({
            'user': UserSerializer(request.user, context={'request': request}).data,
            'student': StudentSerializer(student, context={'request': request}).data,
            'admission': AdmissionSerializer(admission, context={'request': request}).data if admission else None,
            'push_notifications': {
                'registered': bool(token),
                'token': token,
            },
        })

    def put(self, request):
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.phone = request.data.get('phone', user.phone)
        user.save(update_fields=['first_name', 'last_name', 'phone'])

        national_id = request.data.get('national_id', '')
        address = request.data.get('address', '')
        dob = request.data.get('date_of_birth') or None
        gender = request.data.get('gender', '')

        admission = student.admission
        if national_id or address or dob or gender:
            if not admission:
                admission = Admission(
                    first_name=user.first_name, last_name=user.last_name,
                    email=user.email, phone=user.phone or '',
                    date_of_birth=dob or '2000-01-01',
                    gender=gender or 'M',
                    national_id=national_id, address=address,
                    category=student.category, course=student.course,
                    branch=student.branch, status='ENROLLED',
                )
            else:
                admission.national_id = national_id or admission.national_id
                admission.address = address or admission.address
                admission.date_of_birth = dob or admission.date_of_birth
                admission.gender = gender or admission.gender
            admission.save()
            student.admission = admission
            student.save(update_fields=['admission'])

        return Response({
            'detail': 'Profile updated.',
            'user': UserSerializer(user, context={'request': request}).data,
        })


class StudentChatView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        messages = ChatMessage.objects.select_related('user').order_by('-created_at')[:200]
        data = []
        for m in reversed(list(messages)):
            u = m.user
            data.append({
                'id': m.id,
                'user': u.get_full_name() or u.username,
                'role': u.get_role_display(),
                'is_staff': u.role != 'STUDENT',
                'is_me': u.id == request.user.id,
                'content': m.content,
                'time': timezone.localtime(m.created_at).strftime('%H:%M'),
                'date': timezone.localtime(m.created_at).strftime('%a %d %b'),
                'created_at': m.created_at.isoformat(),
            })
        return Response({'messages': data})

    def post(self, request):
        _state, blocked = _require_admission(request)
        if blocked:
            return blocked
        content = (request.data.get('content') or '').strip()
        if not content:
            return Response({'detail': 'Message cannot be empty.'},
                            status=status.HTTP_400_BAD_REQUEST)
        msg = ChatMessage.objects.create(
            user=request.user,
            content=content[:2000],
        )
        u = msg.user
        return Response({
            'id': msg.id,
            'user': u.get_full_name() or u.username,
            'role': u.get_role_display(),
            'is_staff': u.role != 'STUDENT',
            'is_me': True,
            'content': msg.content,
            'time': timezone.localtime(msg.created_at).strftime('%H:%M'),
            'date': timezone.localtime(msg.created_at).strftime('%a %d %b'),
            'created_at': msg.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


# ============================== STUDENT ADMISSION ==============================


class StudentAccessView(APIView):
    """Returns the student's current access level and admission status.

    The app uses this at startup to decide which screens to show.
    """
    permission_classes = [IsStudent]

    def get(self, request):
        state = _access_state(request.user)
        student = state['student']
        admission = state['admission']
        admitted = state['level'] == 'granted'
        from .serializers import StudentSerializer, AdmissionSerializer
        return Response({
            'access_level': state['level'],
            'admitted': admitted,
            'student': StudentSerializer(student, context={'request': request}).data if student else None,
            'admission': AdmissionSerializer(admission, context={'request': request}).data if admission else None,
            'status': admission.status if admission else None,
        })


class StudentAdmissionView(APIView):
    """View and submit the current user's admission application from the app."""
    permission_classes = [IsStudent]

    def get(self, request):
        admission = _get_my_admission(request.user)
        from .serializers import AdmissionSerializer
        return Response({
            'admission': AdmissionSerializer(admission, context={'request': request}).data if admission else None,
        })

    def post(self, request):
        if _get_my_admission(request.user) is not None:
            return Response({'detail': 'You already have an admission application on file.'},
                            status=status.HTTP_400_BAD_REQUEST)

        from website.models import Course, CourseCategory
        from core.models import Branch
        from admissions.models import Admission as AdmissionModel

        category_id = request.data.get('category')
        course_id = request.data.get('course')
        branch_id = request.data.get('branch')
        package_choice = (request.data.get('package_choice') or 'FULL').strip().upper()
        gender = (request.data.get('gender') or 'M').strip().upper()
        preferred_schedule = (request.data.get('preferred_schedule') or 'MORNING').strip().upper()
        date_of_birth = request.data.get('date_of_birth') or None
        national_id = (request.data.get('national_id') or '').strip()
        address = (request.data.get('address') or '').strip()

        if not category_id or not course_id or not branch_id:
            return Response({'detail': 'Course category, course and branch are required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not national_id or not address:
            return Response({'detail': 'National ID and address are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        category = CourseCategory.objects.filter(pk=category_id).first()
        course = Course.objects.filter(pk=course_id, category=category, is_active=True).first() if category else None
        branch = Branch.objects.filter(pk=branch_id, is_active=True).first()
        if not category or not course or not branch:
            return Response({'detail': 'Invalid category, course or branch selected.'},
                            status=status.HTTP_400_BAD_REQUEST)

        admission = AdmissionModel.objects.create(
            submitted_by=request.user,
            first_name=request.user.first_name or request.user.email,
            last_name=request.user.last_name or '',
            email=request.user.email,
            phone=request.user.phone or '',
            date_of_birth=date_of_birth or '2000-01-01',
            gender=gender if gender in ('M', 'F', 'OTHER') else 'M',
            national_id=national_id,
            address=address,
            category=category,
            course=course,
            package_choice=package_choice if package_choice in AdmissionModel.PACKAGE_CHOICES else 'FULL',
            branch=branch,
            preferred_schedule=preferred_schedule if preferred_schedule in dict(AdmissionModel.SCHEDULE_CHOICES) else 'MORNING',
            status='PENDING',
        )
        # passport_photo and national_id_image are optional for app submissions.

        from core.models import DailyLog
        DailyLog.objects.create(
            title=f'New Admission: {admission.full_name}',
            description=f'Course: {course.name}. Phone: {admission.phone}. Submitted via mobile app.',
            log_date=timezone.now().date(),
            created_by=request.user,
        )

        from .serializers import AdmissionSerializer
        return Response({
            'detail': 'Admission submitted successfully. You will be contacted once it is reviewed.',
            'admission': AdmissionSerializer(admission, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


# ============================== ADMIN ==============================


class AdminDashboardView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        from django.db.models import Sum
        today = timezone.now().date()
        total_students = Student.objects.count()
        active_students = Student.objects.filter(status='ACTIVE').count()
        pending_admissions = Admission.objects.filter(status='PENDING').count()
        pending_lesson_approvals = PracticalLesson.objects.filter(
            submitted_by_student=True, is_approved=False
        ).count()
        unread_messages = Notification.objects.filter(
            is_read=True, reply__gt='', reply_read=False
        ).count()

        month_start = today.replace(day=1)
        month_revenue = Payment.objects.filter(
            status='COMPLETED', created_at__date__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        recent_payments = Payment.objects.select_related('student__user')[:10]
        recent_admissions = Admission.objects.select_related('course', 'branch')[:10]

        return Response({
            'total_students': total_students,
            'active_students': active_students,
            'total_payments_this_month': str(month_revenue),
            'pending_admissions': pending_admissions,
            'pending_lesson_approvals': pending_lesson_approvals,
            'unread_messages': unread_messages,
            'recent_payments': AdminPaymentRecordSerializer(recent_payments, many=True).data,
            'recent_admissions': AdminAdmissionRecordSerializer(recent_admissions, many=True).data,
        })


class AdminStudentsView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        qs = Student.objects.select_related('user', 'course', 'branch').all()
        q = (request.GET.get('q') or '').strip()
        status_f = (request.GET.get('status') or '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(student_number__icontains=q)
                | Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(user__email__icontains=q)
                | Q(user__phone__icontains=q)
            )
        if status_f:
            qs = qs.filter(status=status_f)
        students = qs[:100]
        return Response(AdminStudentSerializer(students, many=True).data)


class AdminStudentDetailView(APIView):
    permission_classes = [IsStaff]

    def get(self, request, pk):
        try:
            student = Student.objects.select_related(
                'user', 'course', 'branch', 'instructor__user'
            ).get(pk=pk)
        except Student.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminStudentSerializer(student).data)


class AdminPaymentsView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        qs = Payment.objects.select_related('student__user').all()
        status_f = (request.GET.get('status') or '').strip()
        method_f = (request.GET.get('method') or '').strip()
        if status_f:
            qs = qs.filter(status=status_f)
        if method_f:
            qs = qs.filter(method=method_f)
        return Response(AdminPaymentRecordSerializer(qs[:100], many=True).data)

    def post(self, request):
        student_id = request.data.get('student')
        amount = request.data.get('amount')
        method = (request.data.get('method') or '').strip().upper()
        status_v = (request.data.get('status') or 'COMPLETED').strip().upper()
        reference = (request.data.get('reference_number') or '').strip()
        description = (request.data.get('description') or '').strip()
        if not student_id or not amount or not method:
            return Response({'detail': 'Student, amount and method are required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return Response({'detail': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)
        if amount <= 0:
            return Response({'detail': 'Amount must be greater than zero.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            last = Payment.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            payment = Payment.objects.create(
                student=student,
                receipt_number=f'GLS-RCP-{num:05d}',
                amount=amount,
                method=method,
                reference_number=reference,
                status=status_v,
                description=description or 'Fee payment',
            )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class AdminNotificationsView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        notifications = Notification.objects.select_related('student__user').order_by('-created_at')[:100]
        return Response(AdminNotificationRecordSerializer(notifications, many=True).data)

    def post(self, request):
        from student_portal.push import send_push
        title = (request.data.get('title') or '').strip()
        message = (request.data.get('message') or '').strip()
        ntype = (request.data.get('notification_type') or 'general').strip()
        target_audience = (request.data.get('target_audience') or '').strip().upper()
        send_to_all = request.data.get('send_to_all') in (True, 'true', 'True', 1, '1')
        student_ids = request.data.get('student_ids') or []

        if not title or not message:
            return Response({'detail': 'Title and message are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if send_to_all or target_audience == 'ALL':
            students = Student.objects.filter(status='ACTIVE')
        elif student_ids:
            students = Student.objects.filter(pk__in=student_ids)
        else:
            student_id = request.data.get('student')
            if not student_id:
                return Response({'detail': 'Select a student or send to all.'},
                                status=status.HTTP_400_BAD_REQUEST)
            students = Student.objects.filter(pk=student_id)
            if not students.exists():
                return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        count = 0
        for s in students:
            Notification.objects.create(student=s, title=title, message=message, notification_type=ntype)
            send_push(s, title, message)
            count += 1
        return Response({'detail': f'Notification sent to {count} student(s).'},
                        status=status.HTTP_201_CREATED)


class AdminMarkReplyReadView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return Response({'detail': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
        notification.reply_read = True
        notification.save(update_fields=['reply_read'])
        return Response({'detail': 'Reply marked as read.'})


class AdminChatView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        messages = ChatMessage.objects.select_related('user').order_by('-created_at')[:200]
        data = []
        for m in reversed(list(messages)):
            u = m.user
            data.append({
                'id': m.id,
                'user': u.get_full_name() or u.username,
                'role': u.get_role_display(),
                'is_staff': u.role != 'STUDENT',
                'is_me': u.id == request.user.id,
                'content': m.content,
                'time': timezone.localtime(m.created_at).strftime('%H:%M'),
                'date': timezone.localtime(m.created_at).strftime('%a %d %b'),
                'created_at': m.created_at.isoformat(),
            })
        return Response(data)

    def post(self, request):
        content = (request.data.get('content') or '').strip()
        if not content:
            return Response({'detail': 'Message cannot be empty.'},
                            status=status.HTTP_400_BAD_REQUEST)
        msg = ChatMessage.objects.create(user=request.user, content=content[:2000])
        u = msg.user
        return Response({
            'id': msg.id,
            'user': u.get_full_name() or u.username,
            'role': u.get_role_display(),
            'is_staff': u.role != 'STUDENT',
            'is_me': True,
            'content': msg.content,
            'time': timezone.localtime(msg.created_at).strftime('%H:%M'),
            'date': timezone.localtime(msg.created_at).strftime('%a %d %b'),
            'created_at': msg.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class AdminLessonsView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        qs = PracticalLesson.objects.select_related(
            'student__user', 'lesson_item', 'instructor__user', 'vehicle'
        )
        status_f = (request.GET.get('status') or '').strip()
        if status_f:
            qs = qs.filter(status=status_f)
        lessons = qs[:200]
        return Response(AdminLessonRecordSerializer(lessons, many=True).data)


class AdminLessonApproveView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, pk, action=None):
        action = (action or request.data.get('action') or 'approve').strip().lower()
        try:
            lesson = PracticalLesson.objects.select_related('student__user').get(pk=pk)
        except PracticalLesson.DoesNotExist:
            return Response({'detail': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'approve':
            lesson.is_approved = True
            lesson.submitted_by_student = False
            lesson.save(update_fields=['is_approved', 'submitted_by_student'])
            Notification.objects.create(
                student=lesson.student,
                title='Lesson approved',
                message=f'Your lesson "{lesson.lesson_item.name}" has been approved.',
                notification_type='lesson',
            )
            from student_portal.push import send_push
            send_push(lesson.student, 'Lesson approved',
                      f'Your lesson "{lesson.lesson_item.name}" has been approved.')
            return Response({'detail': 'Lesson approved.'})
        elif action == 'reject':
            lesson.delete()
            return Response({'detail': 'Lesson submission rejected and removed.'})
        return Response({'detail': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)


class AdminAdmissionsView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        qs = Admission.objects.select_related('course', 'branch', 'category')
        status_f = (request.GET.get('status') or '').strip()
        if status_f:
            qs = qs.filter(status=status_f)
        return Response(AdminAdmissionRecordSerializer(qs[:100], many=True).data)


class AdminAdmissionActionView(APIView):
    """Approve / reject / enroll an admission (mobile-admin friendly)."""

    permission_classes = [IsStaff]

    def post(self, request, pk, action):
        action = (action or '').strip().lower()
        try:
            admission = Admission.objects.select_related('course', 'branch', 'category').get(pk=pk)
        except Admission.DoesNotExist:
            return Response({'detail': 'Admission not found.'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'approve':
            admission.status = 'APPROVED'
            admission.save(update_fields=['status'])
            return Response({'detail': 'Admission approved.', 'status': admission.status})
        if action == 'reject':
            admission.status = 'REJECTED'
            admission.save(update_fields=['status'])
            return Response({'detail': 'Admission rejected.', 'status': admission.status})
        if action == 'enroll':
            admission.status = 'ENROLLED'
            admission.save(update_fields=['status'])
            if not Student.objects.filter(admission=admission).exists():
                user, created = User.objects.get_or_create(
                    email=admission.email,
                    defaults={
                        'username': admission.email,
                        'first_name': admission.first_name,
                        'last_name': admission.last_name,
                        'phone': admission.phone,
                        'role': 'STUDENT',
                        'is_active': True,
                        'is_verified': True,
                    },
                )
                if created:
                    user.set_unusable_password()
                    user.save()
                last = Student.objects.order_by('-id').first()
                num = (last.id + 1) if last else 1
                Student.objects.create(
                    user=user,
                    admission=admission,
                    student_number=f'GLS-STU-{num:05d}',
                    category=admission.category,
                    course=admission.course,
                    branch=admission.branch,
                    package_choice=admission.package_choice or 'FULL',
                    status='ACTIVE',
                )
            return Response({'detail': 'Admission enrolled as student.', 'status': admission.status})
        return Response({'detail': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)


class AdminProfileView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        return Response({
            'user': UserSerializer(request.user, context={'request': request}).data,
        })

    def put(self, request):
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.phone = request.data.get('phone', user.phone)
        user.save(update_fields=['first_name', 'last_name', 'phone'])
        return Response({
            'detail': 'Profile updated.',
            'user': UserSerializer(user, context={'request': request}).data,
        })
