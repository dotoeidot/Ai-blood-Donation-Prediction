from django.urls import path
from .views import landing,home, result, donor_history, donor_probability

urlpatterns = [
    path("", landing, name="landing"),                
    path("predict/", home, name="home"),               
    path("result/", result, name="result"),
    path("history/", donor_history, name="donor_history"),
    path("probability/", donor_probability, name="donor_probability"),
]
