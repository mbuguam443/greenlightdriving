from django.db import models


class Branch(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    address = models.TextField()
    town = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image = models.ImageField(upload_to="branches/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "branches"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=200, default="Greenlight Defensive Driving School")
    tagline = models.CharField(max_length=300, default="Drive Safe, Drive Smart")
    phone_primary = models.CharField(max_length=20)
    phone_secondary = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    address = models.TextField()
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    working_hours = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to="site/", blank=True)
    favicon = models.ImageField(upload_to="site/", blank=True)
    exam_fee = models.DecimalField(max_digits=10, decimal_places=2, default=3100,
                                    help_text="Exam booking fee applied to all students (KES)")

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class DailyLog(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    log_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-log_date', '-created_at']

    def __str__(self):
        return f"{self.log_date} - {self.title}"
