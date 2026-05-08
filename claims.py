"""Synthetic claims for triage agent smoke testing.

Five varied scenarios that exercise the routing logic:
    1. Small honest claim    -> expected: fast_track
    2. Large honest urgent   -> expected: standard or fast_track (high severity, clean)
    3. Repeat-pattern OPD    -> expected: fraud_review
    4. Missing-info admit    -> expected: fraud_review or standard
    5. Stroke emergency      -> expected: fast_track or standard (urgent, clean)

The amounts are in INR (Indian Rupees) since the agent is framed for the
Indian health insurance context.
"""

CLAIMS: list[dict] = [
    {
        "claim_id": "CLM-2026-0001",
        "claim_text": (
            "Outpatient consultation and basic blood work at a network clinic on "
            "2026-04-22. Itemised receipt attached, doctor's prescription on letterhead, "
            "diagnostic lab report scanned. First claim in the policy year. Insured has "
            "been with the insurer for 3 years with no prior claims."
        ),
        "claim_amount": 4_500.00,
    },
    {
        "claim_id": "CLM-2026-0002",
        "claim_text": (
            "Coronary artery bypass graft (CABG) at Lilavati Hospital, Mumbai, on "
            "2026-04-15. Pre-authorisation issued by the insurer prior to admission. "
            "Discharge summary, surgical notes, ICU records, and itemised hospital bill "
            "all attached. Insured was admitted via emergency after acute chest pain."
        ),
        "claim_amount": 8_50_000.00,
    },
    {
        "claim_id": "CLM-2026-0003",
        "claim_text": (
            "Outpatient dermatology consultation and a minor in-clinic procedure. This "
            "is the third claim from the insured in the last six months from the same "
            "small clinic; the previous two were also OPD consultations. Receipts are "
            "handwritten, no diagnostic report is attached, and the doctor's stamp is "
            "inconsistent across the three visits. Treatment codes vary widely for very "
            "similar presenting complaints."
        ),
        "claim_amount": 12_500.00,
    },
    {
        "claim_id": "CLM-2026-0004",
        "claim_text": (
            "Hospital admission claim for 'chest pain'. Only a lump-sum amount is "
            "stated on the bill with no itemisation. Dates of admission and discharge "
            "are not specified clearly. The insured separately disputes that the hospital "
            "also charged them in cash for some services. No discharge summary attached."
        ),
        "claim_amount": 1_25_000.00,
    },
    {
        "claim_id": "CLM-2026-0005",
        "claim_text": (
            "Emergency stroke admission on 2026-05-06 at Apollo Hospital. Thrombolysis "
            "was administered within the golden-hour window. ICU stay of 4 days, "
            "neurology consult, MRI and CT imaging, and a full discharge summary are "
            "all attached. The insured has requested time-critical approval for pending "
            "physiotherapy and follow-up imaging."
        ),
        "claim_amount": 4_50_000.00,
    },
]
