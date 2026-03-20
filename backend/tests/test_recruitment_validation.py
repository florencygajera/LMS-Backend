import pytest
from pydantic import ValidationError

from schemas.recruitment import ApplicationVerificationRequest


def test_application_verification_requires_batch():
    with pytest.raises(ValidationError):
        ApplicationVerificationRequest(
            age_eligible=True,
            education_eligible=True,
            physical_eligible=True,
            documents_verified=True,
        )


def test_application_verification_accepts_valid_payload():
    payload = ApplicationVerificationRequest(
        recruitment_batch="2026-A",
        force_type="Army",
        trade_category="General Duty",
        age_eligible=True,
        education_eligible=True,
        physical_eligible=True,
        documents_verified=True,
    )

    assert payload.recruitment_batch == "2026-A"



