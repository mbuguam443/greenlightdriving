from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Vehicle
from .forms import VehicleForm


class StaffTestMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST')


class VehicleListView(StaffTestMixin, ListView):
    model = Vehicle
    template_name = 'vehicles/vehicle_list.html'
    context_object_name = 'vehicles'
    paginate_by = 20

    def get_queryset(self):
        qs = Vehicle.objects.select_related('assigned_instructor__user').all()
        q = (self.request.GET.get('q') or '').strip()
        category = (self.request.GET.get('category') or '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(registration_number__icontains=q)
                | Q(make__icontains=q)
                | Q(model_name__icontains=q)
            )
        if category:
            qs = qs.filter(category=category)
        return qs


class VehicleDetailView(StaffTestMixin, DetailView):
    model = Vehicle
    template_name = 'vehicles/vehicle_detail.html'
    context_object_name = 'vehicle'


class VehicleCreateView(StaffTestMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    success_url = reverse_lazy('vehicles:list')

    def form_valid(self, form):
        messages.success(self.request, 'Vehicle added successfully.')
        return super().form_valid(form)


class VehicleUpdateView(StaffTestMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    success_url = reverse_lazy('vehicles:list')

    def form_valid(self, form):
        messages.success(self.request, 'Vehicle updated successfully.')
        return super().form_valid(form)


class VehicleDeleteView(StaffTestMixin, DeleteView):
    model = Vehicle
    template_name = 'vehicles/vehicle_confirm_delete.html'
    success_url = reverse_lazy('vehicles:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Vehicle deleted successfully.')
        return super().delete(request, *args, **kwargs)
