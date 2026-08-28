"""NSFDC Setu - Recommender + EMI backend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
SCHEMES_FILE = BASE_DIR / "data" / "schemes.json"


def load_schemes(path: str | Path = SCHEMES_FILE) -> List[Dict[str, Any]]:
    """Load scheme records from data/schemes.json."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Scheme file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        schemes = json.load(f)
    if not isinstance(schemes, list):
        raise ValueError("schemes.json must contain a list.")
    return schemes


def get_scheme_by_id(scheme_id: str, schemes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return a scheme by scheme_id."""
    for scheme in schemes:
        if scheme.get("scheme_id") == scheme_id:
            return scheme
    return None


def validate_profile(profile: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate the profile required by the recommender."""
    if not isinstance(profile, dict):
        return False, "Profile must be a dictionary."
    if "purpose" not in profile:
        return False, "Missing required field: purpose."
    if "project_cost" not in profile:
        return False, "Missing required field: project_cost."

    purpose = str(profile["purpose"]).strip().lower()
    if purpose not in {"project", "education"}:
        return False, "purpose must be 'project' or 'education'."

    try:
        cost = float(profile["project_cost"])
    except (TypeError, ValueError):
        return False, "project_cost must be numeric."
    if cost < 0:
        return False, "project_cost cannot be negative."

    return True, ""


def recommend_scheme(profile: Dict[str, Any], schemes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Recommend MFS, TL, or EDU using the updated JSON thresholds."""
    valid, error = validate_profile(profile)
    if not valid:
        raise ValueError(error)

    purpose = str(profile["purpose"]).strip().lower()
    cost = float(profile["project_cost"])

    mfs = get_scheme_by_id("MFS", schemes)
    tl = get_scheme_by_id("TL", schemes)
    edu = get_scheme_by_id("EDU", schemes)

    if not all((mfs, tl, edu)):
        raise ValueError("schemes.json must contain MFS, TL and EDU.")

    if purpose == "education":
        return edu

    if cost <= float(mfs["max_project_cost"]):
        return mfs

    min_tl = float(tl.get("min_project_cost", float(mfs["max_project_cost"]) + 1))
    max_tl = float(tl["max_project_cost"])
    if min_tl <= cost <= max_tl:
        return tl

    return None


def calculate_max_loan(project_cost: float, scheme: Dict[str, Any]) -> float:
    """Calculate loan as the lower of percentage-based and scheme cap."""
    project_cost = float(project_cost)
    if project_cost < 0:
        raise ValueError("project_cost cannot be negative.")

    pct_amount = project_cost * float(scheme["max_loan_pct_of_cost"]) / 100
    cap = scheme.get("max_loan_amount")
    if cap is not None:
        pct_amount = min(pct_amount, float(cap))
    return round(pct_amount, 2)


def calculate_moratorium_interest(principal: float, annual_rate_pct: float, moratorium_months: int) -> float:
    """Prototype simple-interest model for a numeric moratorium."""
    principal = float(principal)
    annual_rate_pct = float(annual_rate_pct)
    moratorium_months = int(moratorium_months)
    if principal < 0 or annual_rate_pct < 0 or moratorium_months < 0:
        raise ValueError("Principal, rate and moratorium must be non-negative.")
    monthly_rate = annual_rate_pct / 100 / 12
    return round(principal * monthly_rate * moratorium_months, 2)


def calculate_emi(
    principal: float,
    annual_rate_pct: float,
    tenure_years: float,
    moratorium_months: int = 0,
) -> Dict[str, float]:
    """Calculate reducing-balance EMI using a numeric moratorium."""
    principal = float(principal)
    annual_rate_pct = float(annual_rate_pct)
    tenure_years = float(tenure_years)
    moratorium_months = int(moratorium_months)

    if principal < 0:
        raise ValueError("principal cannot be negative.")
    if annual_rate_pct < 0:
        raise ValueError("annual_rate_pct cannot be negative.")
    if tenure_years <= 0:
        raise ValueError("tenure_years must be greater than zero.")
    if moratorium_months < 0:
        raise ValueError("moratorium_months cannot be negative.")

    monthly_rate = annual_rate_pct / 100 / 12
    repayment_months = round(tenure_years * 12)
    accrued_interest = calculate_moratorium_interest(principal, annual_rate_pct, moratorium_months)
    adjusted_principal = principal + accrued_interest

    if monthly_rate == 0:
        emi = adjusted_principal / repayment_months
    else:
        emi = (
            adjusted_principal * monthly_rate * (1 + monthly_rate) ** repayment_months
            / ((1 + monthly_rate) ** repayment_months - 1)
        )

    total_repayment = emi * repayment_months
    return {
        "principal_before_moratorium": round(principal, 2),
        "moratorium_interest": round(accrued_interest, 2),
        "principal_after_moratorium": round(adjusted_principal, 2),
        "repayment_months": float(repayment_months),
        "emi": round(emi, 2),
        "total_repayment": round(total_repayment, 2),
        "total_interest": round(total_repayment - adjusted_principal, 2),
    }


def get_loan_estimate(
    profile: Dict[str, Any],
    schemes: List[Dict[str, Any]],
    interest_rate: Optional[float] = None,
    moratorium_months: Optional[int] = None,
) -> Dict[str, Any]:
    """Return recommendation, loan amount, and EMI estimate for the frontend.

    For EDU, the JSON gives a text moratorium description rather than a numeric
    month count. Therefore the returned EMI is a base estimate with 0-month
    numeric moratorium unless the caller supplies a numeric value.
    """
    scheme = recommend_scheme(profile, schemes)
    if scheme is None:
        return {
            "success": False,
            "message": "Project cost exceeds the maximum project cost supported by the loaded project schemes.",
        }

    project_cost = float(profile["project_cost"])
    loan_amount = calculate_max_loan(project_cost, scheme)
    selected_rate = float(scheme["interest_rate_beneficiary"]) if interest_rate is None else float(interest_rate)

    # Numeric moratorium values exist for MFS/TL. EDU contains a description.
    if moratorium_months is not None:
        selected_moratorium = int(moratorium_months)
    elif isinstance(scheme.get("moratorium_months"), int):
        selected_moratorium = int(scheme["moratorium_months"])
    else:
        selected_moratorium = 0

    if scheme["scheme_id"] == "TL":
        allowed = {int(scheme["moratorium_months"]), int(scheme["extended_moratorium_months"])}
        if selected_moratorium not in allowed:
            raise ValueError(f"Moratorium must be one of {sorted(allowed)} months for {scheme['name']}.")
    elif "moratorium_months" in scheme and isinstance(scheme["moratorium_months"], int):
        allowed = int(scheme["moratorium_months"])
        if moratorium_months is not None and selected_moratorium != allowed:
            raise ValueError(f"Moratorium must be {allowed} months for {scheme['name']}.")

    if selected_rate != float(scheme["interest_rate_beneficiary"]):
        raise ValueError(f"Interest rate must be {scheme['interest_rate_beneficiary']}% for {scheme['name']}.")

    emi_data = calculate_emi(
        loan_amount,
        selected_rate,
        float(scheme["max_tenure_years"]),
        selected_moratorium,
    )

    result = {
        "success": True,
        "scheme_id": scheme["scheme_id"],
        "scheme_name": scheme["name"],
        "purpose": scheme["purpose"],
        "description": scheme["description"],
        "project_cost": round(project_cost, 2),
        "max_loan_amount": loan_amount,
        "interest_rate": selected_rate,
        "max_tenure_years": scheme["max_tenure_years"],
        "selected_moratorium_months": selected_moratorium,
        "emi_details": emi_data,
        "source": scheme.get("source"),
        "last_verified": scheme.get("last_verified"),
    }

    if "moratorium_description" in scheme:
        result["moratorium_note"] = scheme["moratorium_description"]
        result["emi_note"] = "EDU moratorium is described in the data rather than given as a numeric duration; this EMI is a base estimate before that additional moratorium is modeled."
    elif scheme["scheme_id"] == "TL":
        result["moratorium_options"] = [
            int(scheme["moratorium_months"]),
            int(scheme["extended_moratorium_months"]),
        ]

    return result


def main() -> None:
    """Quick CLI demo."""
    schemes = load_schemes()
    examples = [
        {"purpose": "project", "project_cost": 140000},
        {"purpose": "project", "project_cost": 140001},
        {"purpose": "project", "project_cost": 5000000},
        {"purpose": "project", "project_cost": 5000001},
        {"purpose": "education", "project_cost": 1000000},
    ]

    for profile in examples:
        print("\n" + "=" * 65)
        print("INPUT:", profile)
        result = get_loan_estimate(profile, schemes)
        if not result["success"]:
            print(result["message"])
            continue
        print("SCHEME:", result["scheme_name"])
        print("MAX LOAN: ₹{:,.2f}".format(result["max_loan_amount"]))
        print("INTEREST: {}%".format(result["interest_rate"]))
        print("MORATORIUM: {} months".format(result["selected_moratorium_months"]))
        print("TENURE: {} years".format(result["max_tenure_years"]))
        print("EMI: ₹{:,.2f}".format(result["emi_details"]["emi"]))
        if "moratorium_note" in result:
            print("NOTE:", result["moratorium_note"])


if __name__ == "__main__":
    main()
