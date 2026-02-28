import os
import joblib
import numpy as np
import time

from django.conf import settings
from django.shortcuts import render, redirect

from .models import DonationRecord, DonorHistory,SmartMatchingLog


# =========================
# LOAD ML MODEL & ENCODERS
# =========================
ML_DIR = os.path.join(settings.BASE_DIR, "predictor", "ml")

ml_model = joblib.load(os.path.join(ML_DIR, "donor_predictor.pkl"))
city_encoder = joblib.load(os.path.join(ML_DIR, "city_encoder.pkl"))
blood_encoder = joblib.load(os.path.join(ML_DIR, "blood_encoder.pkl"))


# =========================
# HOME – ELIGIBILITY CHECK
# =========================
def home(request):
    if request.method == "POST":
        age = int(request.POST["age"])
        weight = int(request.POST["weight"])
        hb = float(request.POST["hb"])
        days = int(request.POST["last_donation"])

        eligible = (
            age >= 18 and
            weight >= 50 and
            hb >= 12.5 and
            days >= 90
        )

        DonationRecord.objects.create(
            age=age,
            weight=weight,
            hemoglobin=hb,
            last_donation_days=days,
            is_eligible=eligible
        )

        request.session["eligible"] = eligible
        return redirect("result")

    return render(request, "index.html")


# =========================
# ELIGIBILITY RESULT PAGE
# =========================
def result(request):
    eligible = request.session.get("eligible")
    return render(request, "results.html", {"eligible": eligible})


# =========================
# DONOR HISTORY + ML MODEL
# =========================
def donor_history(request):
    if request.method == "POST":
        city = request.POST["city"]
        blood_group = request.POST["blood_group"]

        donation_count = int(request.POST["donation_count"])
        total_blood = float(request.POST.get("total_blood_donated", 0))
        months_since_first = int(request.POST["months_since_first_donation"])
        recency = int(request.POST["recency_months"])

        # SAFE ENCODING
        city_encoded = (
            city_encoder.transform([city])[0]
            if city in city_encoder.classes_
            else -1
        )

        blood_encoded = (
            blood_encoder.transform([blood_group])[0]
            if blood_group in blood_encoder.classes_
            else -1
        )

        # FEATURE ENGINEERING (TRAINING CONSISTENT)
        created_at_numeric = time.time()
        recency_score = 1 / (recency + 1)
        city_donation_density = donation_count
        donation_rate_city = donation_count / (city_donation_density + 1)
        engagement_score = (recency_score + donation_rate_city) / 2

        # FINAL FEATURE VECTOR (ORDER MATTERS)
        X = np.array([[
            city_encoded,
            blood_encoded,
            months_since_first,
            created_at_numeric,
            recency_score,
            city_donation_density,
            donation_rate_city,
            engagement_score
        ]])

        probability = ml_model.predict_proba(X)[0][1]
        probability_percent = round(float(probability * 100), 2)

        # SAVE TO DATABASE
        DonorHistory.objects.create(
            city=city,
            blood_group=blood_group,
            donation_count=donation_count,
            total_blood_donated=total_blood,
            months_since_first_donation=months_since_first,
            recency_months=recency
        )

        # STORE SESSION DATA
        request.session["ml_probability"] = probability_percent
        request.session["city"] = city
        request.session["blood_group"] = blood_group
        request.session["donation_count"] = donation_count
        request.session["months_since_first_donation"] = months_since_first
        request.session["recency_months"] = recency

        return redirect("donor_probability")

    return render(request, "donor_history.html")


# =========================
# SMART MATCHING SYSTEM
# =========================
def donor_probability(request):
    ml_probability = request.session.get("ml_probability", 0)

    city = request.session.get("city")
    blood_group = request.session.get("blood_group")

    donation_count = request.session.get("donation_count", 0)
    months_since_first = request.session.get("months_since_first_donation", 0)
    recency_months = request.session.get("recency_months", 0)

    # REAL FEATURE ENGINEERING
    recency_score = 1 / (recency_months + 1)
    donation_frequency = donation_count / (months_since_first + 1)

    engagement_score = round(
        (recency_score + donation_frequency) / 2,
        3
    )

    # SMART MATCH SCORE
    match_score = round(
        (ml_probability * 0.65) +
        (engagement_score * 35),
        2
    )
    match_score = min(match_score, 100)

    # PRIORITY
    if match_score >= 75:
        priority = "HIGH"
    elif match_score >= 45:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    # DYNAMIC EXPLANATIONS (FIXED)
    if priority == "HIGH":
        explanations = [
            "Consistent donation history",
            "Recent donation activity",
            "High predicted likelihood of future donation",
            "Strong overall engagement score"
        ]

    elif priority == "MEDIUM":
        explanations = [
            "Moderate donation frequency",
            "Some gaps in recent donation activity",
            "Average engagement score",
            "Moderate predicted likelihood of donation"
        ]

    else:  # LOW
        explanations = [
            "Low donation frequency",
            "Long gap since last donation",
            "Low engagement score",
            "Lower predicted likelihood of donation"
        ]

    return render(
        request,
        "donorprob.html",
        {
            "ml_probability": ml_probability,
            "match_score": match_score,
            "priority": priority,
            "engagement_score": round(engagement_score * 100, 2),
            "city": city,
            "blood_group": blood_group,
            "reasons": explanations, 
        }
    )
def landing(request):
    return render(request, "landing.html")