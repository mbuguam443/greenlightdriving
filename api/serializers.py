from rest_framework import serializers

from accounts.models import User
from admissions.models import Admission
from core.models import Branch, SiteSettings
from instructors.models import Instructor
from lessons.models import LessonItem, PracticalLesson, TheoryLesson
from ntsa.models import NTSARecord
from payments.models import Payment, MpesaTransaction
from student_portal.models import Event, Notification, StudentDocument
from students.models import Student, StudentEnrollment
from vehicles.models import Vehicle
from website.models import BlogPost, ContactMessage, Course, CourseCategory, FAQ, GalleryImage, Testimonial


def _absolute(request, url):
    if not url:
        return None
    if request is None:
        return url
    return request.build_absolute_uri(url)


# ============================== AUTH ==============================


class RegisterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'password']

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            role='STUDENT',
            is_active=True,
            is_verified=True,
        )
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    passport_photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'phone',
                  'role', 'gender', 'date_of_birth', 'national_id', 'address',
                  'passport_photo', 'is_verified']

    def get_passport_photo(self, obj):
        return _absolute(self.context.get('request'), obj.passport_photo.url if obj.passport_photo else None)


# ============================== PUBLIC ==============================


class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'slug', 'description']


class CourseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    feature_list = serializers.ListField(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'slug', 'category', 'category_name', 'short_description',
                  'description', 'duration', 'full_course_price', 'half_course_price',
                  'test_only_price', 'feature_list', 'image']

    def get_image(self, obj):
        return _absolute(self.context.get('request'), obj.image.url if obj.image else None)


class BranchSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = ['id', 'name', 'slug', 'address', 'town', 'phone', 'email',
                  'latitude', 'longitude', 'image']

    def get_image(self, obj):
        return _absolute(self.context.get('request'), obj.image.url if obj.image else None)


class TestimonialSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True, default=None)
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Testimonial
        fields = ['id', 'name', 'course_name', 'rating', 'comment', 'photo']

    def get_photo(self, obj):
        return _absolute(self.context.get('request'), obj.photo.url if obj.photo else None)


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category']


class BlogPostSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'slug', 'excerpt', 'content', 'featured_image',
                  'author_name', 'views_count', 'created_at']

    def get_author_name(self, obj):
        return obj.author.full_name if obj.author else 'Green Light Team'

    def get_featured_image(self, obj):
        return _absolute(self.context.get('request'), obj.featured_image.url if obj.featured_image else None)


class GalleryImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = GalleryImage
        fields = ['id', 'title', 'image', 'category', 'description']

    def get_image(self, obj):
        return _absolute(self.context.get('request'), obj.image.url if obj.image else None)


class SiteInfoSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = SiteSettings
        fields = ['site_name', 'tagline', 'phone_primary', 'phone_secondary', 'email',
                  'address', 'facebook', 'instagram', 'twitter', 'youtube',
                  'working_hours', 'exam_fee', 'logo']

    def get_logo(self, obj):
        return _absolute(self.context.get('request'), obj.logo.url if obj.logo else None)


class EventSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True, default=None)

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'category', 'event_date', 'event_time',
                  'end_date', 'branch_name', 'location', 'is_important']


# ============================== INSTRUCTOR / VEHICLE ==============================


class InstructorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    photo = serializers.SerializerMethodField()
    assigned_students_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Instructor
        fields = ['id', 'full_name', 'phone', 'license_number', 'license_class',
                  'license_expiry', 'experience_years', 'specialization', 'photo',
                  'assigned_students_count']

    def get_photo(self, obj):
        return _absolute(self.context.get('request'), obj.photo.url if obj.photo else None)


class VehicleSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = ['id', 'registration_number', 'category', 'make', 'model_name', 'year',
                  'color', 'is_available', 'image', 'is_insurance_valid', 'is_service_due']

    def get_image(self, obj):
        return _absolute(self.context.get('request'), obj.image.url if obj.image else None)


# ============================== LESSONS ==============================


class LessonItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonItem
        fields = ['id', 'name', 'order', 'lesson_type']


class PracticalLessonSerializer(serializers.ModelSerializer):
    lesson_item_name = serializers.CharField(source='lesson_item.name', read_only=True)
    lesson_type = serializers.CharField(source='lesson_item.lesson_type', read_only=True)
    instructor_name = serializers.CharField(source='instructor.user.full_name', read_only=True, default=None)
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True, default=None)

    class Meta:
        model = PracticalLesson
        fields = ['id', 'lesson_item', 'lesson_item_name', 'lesson_type', 'date', 'status',
                  'remarks', 'attended', 'submitted_by_student', 'is_approved',
                  'instructor_name', 'vehicle_registration']


class TheoryLessonSerializer(serializers.ModelSerializer):
    lesson_item_name = serializers.CharField(source='lesson_item.name', read_only=True, default=None)
    instructor_name = serializers.CharField(source='instructor.user.full_name', read_only=True, default=None)

    class Meta:
        model = TheoryLesson
        fields = ['id', 'lesson_item', 'lesson_item_name', 'topic', 'date', 'time_start',
                  'time_end', 'status', 'notes', 'attended', 'instructor_name']


# ============================== STUDENT ==============================


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    category_name = serializers.CharField(source='course.category.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = StudentEnrollment
        fields = ['id', 'course', 'course_name', 'category_name', 'package_choice',
                  'branch_name', 'status', 'enrollment_date', 'expected_graduation',
                  'total_fees', 'amount_paid', 'balance']


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    instructor_name = serializers.CharField(source='instructor.user.full_name', read_only=True, default=None)
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True, default=None)
    enrollments = StudentEnrollmentSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'student_number', 'user', 'course', 'course_name', 'category_name',
                  'package_choice', 'branch_name', 'instructor_name', 'vehicle_registration',
                  'status', 'enrollment_date', 'expected_graduation', 'payment_reminder',
                  'discount', 'discount_reason',
                  'lessons_completed', 'total_lessons', 'progress_percentage',
                  'total_fees', 'amount_paid', 'balance', 'enrollments']


class AdmissionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Admission
        fields = ['id', 'admission_number', 'full_name', 'email', 'phone', 'gender',
                  'national_id', 'address', 'date_of_birth',
                  'category_name', 'course_name', 'package_choice', 'branch_name',
                  'preferred_schedule', 'status', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    student_name = serializers.SerializerMethodField()
    student_number = serializers.SerializerMethodField()

    def get_student_name(self, obj):
        return obj.student.user.full_name if obj.student else ''

    def get_student_number(self, obj):
        return obj.student.student_number if obj.student else ''

    class Meta:
        model = Payment
        fields = ['id', 'receipt_number', 'amount', 'method', 'method_display',
                  'reference_number', 'status', 'status_display', 'description',
                  'student_name', 'student_number', 'created_at']


class MpesaTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaTransaction
        fields = ['id', 'phone_number', 'amount', 'account_reference',
                  'checkout_request_id', 'mpesa_receipt', 'status', 'created_at']


class NTSASerializer(serializers.ModelSerializer):
    pdl_status_display = serializers.CharField(source='get_pdl_status_display', read_only=True)
    theory_exam_status_display = serializers.CharField(source='get_theory_exam_status_display', read_only=True)
    practical_exam_status_display = serializers.CharField(source='get_practical_exam_status_display', read_only=True)
    driving_test_status_display = serializers.CharField(source='get_driving_test_status_display', read_only=True)

    class Meta:
        model = NTSARecord
        fields = ['id', 'pdl_status', 'pdl_status_display', 'pdl_date', 'pdl_number',
                  'theory_exam_status', 'theory_exam_status_display', 'theory_exam_date', 'theory_exam_score',
                  'practical_exam_status', 'practical_exam_status_display', 'practical_exam_date',
                  'driving_test_status', 'driving_test_status_display', 'driving_test_date',
                  'licence_issued', 'licence_number', 'licence_issue_date', 'licence_expiry_date',
                  'overall_progress']


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    student_name = serializers.CharField(source='student.user.full_name', read_only=True)
    student_number = serializers.CharField(source='student.student_number', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'notification_type_display',
                  'is_read', 'reply', 'replied_at', 'created_at', 'student_name', 'student_number']


class StudentDocumentSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    file_extension = serializers.CharField(read_only=True)
    file_size_display = serializers.CharField(read_only=True)

    class Meta:
        model = StudentDocument
        fields = ['id', 'title', 'description', 'file', 'file_extension',
                  'file_size_display', 'category', 'uploaded_at']

    def get_file(self, obj):
        return _absolute(self.context.get('request'), obj.file.url if obj.file else None)


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message']
