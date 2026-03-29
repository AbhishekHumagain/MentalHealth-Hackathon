from __future__ import annotations

from app.application.services.listing_risk import ListingRiskService


def test_internship_risk_flags_obvious_payment_scam_as_high() -> None:
    service = ListingRiskService()

    result = service.analyze_internship(
        title="Remote Intern - Apply Immediately",
        company="Confidential",
        description=(
            "Apply immediately. Training fee required before interview. "
            "Send payment by gift card and contact us on WhatsApp."
        ),
        application_url="https://bit.ly/fake-internship",
        source_url="https://example.com/listing",
    )

    assert result.level == "high"
    assert result.score >= 7.0
    assert any("payment" in reason.lower() for reason in result.reasons)


def test_internship_risk_flags_missing_details_as_medium() -> None:
    service = ListingRiskService()

    result = service.analyze_internship(
        title="Operations Intern",
        company="Confidential",
        description="Operations internship details are available at hiringteam@gmail.com.",
        application_url="https://example.com/jobs/1",
        source_url="https://example.com/jobs/1",
    )

    assert result.level == "medium"
    assert any("vague" in reason.lower() for reason in result.reasons)


def test_event_risk_leaves_normal_support_event_low() -> None:
    service = ListingRiskService()

    result = service.analyze_event(
        title="Career Fair",
        description="Meet alumni and employers for internship guidance and networking.",
        organizer_name="Career Center",
        location="Campus Hall",
        meeting_url=None,
        mode="in_person",
    )

    assert result.level == "low"
    assert result.score == 0.0
    assert result.reasons == []
