from django.views.generic import RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

class HomeView(LoginRequiredMixin, RedirectView):
    url = reverse_lazy('reports:dashboard')
