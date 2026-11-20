import pytest
from app.services.academic_service import calculate_attendance_math


def test_attendance_math_zero_classes():
    res = calculate_attendance_math(current_attended=0, current_total=0, target_pct=75.0)
    assert res["current_percentage"] == 100.0
    assert res["classes_needed"] == 0
    assert res["can_miss_classes"] == 0


def test_attendance_math_above_target():
    # 8 attended out of 10 total = 80% > 75%
    res = calculate_attendance_math(current_attended=8, current_total=10, target_pct=75.0)
    assert res["current_percentage"] == 80.0
    assert res["classes_needed"] == 0
    # Can miss: floor((100*8 - 75*10)/75) = floor(50/75) = 0
    assert res["can_miss_classes"] == 0

    # 18 attended out of 20 = 90%
    # floor((100*18 - 75*20)/75) = floor((1800 - 1500)/75) = 300/75 = 4
    res2 = calculate_attendance_math(current_attended=18, current_total=20, target_pct=75.0)
    assert res2["current_percentage"] == 90.0
    assert res2["can_miss_classes"] == 4


def test_attendance_math_below_target():
    # 6 attended out of 10 total = 60% < 75%
    # Needed: ceil((75*10 - 100*6)/(100 - 75)) = ceil((750 - 600)/25) = ceil(150/25) = 6
    res = calculate_attendance_math(current_attended=6, current_total=10, target_pct=75.0)
    assert res["current_percentage"] == 60.0
    assert res["classes_needed"] == 6
    assert res["can_miss_classes"] == 0


def test_attendance_math_exact_target():
    # 15 attended out of 20 total = 75.0%
    res = calculate_attendance_math(current_attended=15, current_total=20, target_pct=75.0)
    assert res["current_percentage"] == 75.0
    assert res["classes_needed"] == 0
    assert res["can_miss_classes"] == 0
