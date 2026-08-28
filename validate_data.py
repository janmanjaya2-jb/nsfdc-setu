import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SCHEMES_FILE = BASE_DIR / "data" / "schemes.json"
PARTNERS_FILE = BASE_DIR / "data" / "odisha_partners.json"


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_schemes(schemes):
    errors = []

    required_fields = [
        "scheme_id",
        "name",
        "purpose",
        "interest_rate_beneficiary"
    ]

    valid_ids = {"MFS", "TL", "EDU"}

    if not isinstance(schemes, list):
        return ["schemes.json must contain a list"]

    ids = []

    for scheme in schemes:
        for field in required_fields:
            if field not in scheme:
                errors.append(
                    f"Scheme {scheme.get('scheme_id', 'UNKNOWN')} "
                    f"is missing {field}"
                )

        scheme_id = scheme.get("scheme_id")

        if scheme_id in ids:
            errors.append(f"Duplicate scheme_id: {scheme_id}")

        ids.append(scheme_id)

        if scheme_id not in valid_ids:
            errors.append(f"Invalid scheme_id: {scheme_id}")

    return errors


def validate_partners(partners):
    errors = []

    required_fields = [
        "partner_id",
        "name",
        "type",
        "district",
        "address",
        "lat",
        "lon",
        "handles_schemes"
    ]

    valid_scheme_ids = {"MFS", "TL", "EDU"}

    if not isinstance(partners, list):
        return ["odisha_partners.json must contain a list"]

    ids = []

    for partner in partners:

        partner_id = partner.get("partner_id", "UNKNOWN")

        for field in required_fields:
            if field not in partner:
                errors.append(
                    f"Partner {partner_id} is missing {field}"
                )

        if partner_id in ids:
            errors.append(f"Duplicate partner_id: {partner_id}")

        ids.append(partner_id)

        # Validate latitude
        try:
            lat = float(partner.get("lat"))
            if not -90 <= lat <= 90:
                errors.append(
                    f"{partner_id}: invalid latitude {lat}"
                )
        except (TypeError, ValueError):
            errors.append(
                f"{partner_id}: latitude must be numeric"
            )

        # Validate longitude
        try:
            lon = float(partner.get("lon"))
            if not -180 <= lon <= 180:
                errors.append(
                    f"{partner_id}: invalid longitude {lon}"
                )
        except (TypeError, ValueError):
            errors.append(
                f"{partner_id}: longitude must be numeric"
            )

        # Validate scheme IDs
        for scheme_id in partner.get("handles_schemes", []):
            if scheme_id not in valid_scheme_ids:
                errors.append(
                    f"{partner_id}: invalid scheme ID {scheme_id}"
                )

    return errors


def main():

    print("=" * 50)
    print("NSFDC SETU DATA VALIDATION")
    print("=" * 50)

    try:
        schemes = load_json(SCHEMES_FILE)
        partners = load_json(PARTNERS_FILE)
    except Exception as error:
        print("ERROR loading JSON:", error)
        return

    scheme_errors = validate_schemes(schemes)
    partner_errors = validate_partners(partners)

    print(f"\nSchemes found: {len(schemes)}")
    print(f"Partners found: {len(partners)}")

    all_errors = scheme_errors + partner_errors

    if all_errors:
        print("\n❌ VALIDATION FAILED")

        for error in all_errors:
            print("-", error)

    else:
        print("\n✅ VALIDATION PASSED")
        print("All scheme and partner records are valid.")


if __name__ == "__main__":
    main()