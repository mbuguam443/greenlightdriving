from datetime import date

from django.contrib.auth import authenticate
from django.db import models as dj_models
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

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


def _get_student(request):
    try:
        return Student.objects.select_related('user', 'course', 'category', 'branch', 'instructor').get(
            user=request.user
        )
    except Student.DoesNotExist:
        return None


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
        student = _get_student(request)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'},
                            status=status.HTTP_404_NOT_FOUND)
        notifications = Notification.objects.filter(student=student)
        return Response(NotificationSerializer(notifications, many=True).data)

    def post(self, request, pk=None):
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
