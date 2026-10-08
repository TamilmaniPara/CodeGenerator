import json
import re
from pathlib import Path

from phoenix.otel import register


# ---------------------------------------------------------
# Phoenix
# ---------------------------------------------------------

tracer_provider = register(
    project_name="data-element-analysis",
    endpoint="http://localhost:6006/v1/traces"
)

tracer = tracer_provider.get_tracer(__name__)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

REQUIRED_FIELDS = [
    "source_name",
    "source_id",
    "code_file",
    "class_name",
    "method_name",
    "variable_name",
    "evidence",
    "confidence",
    "status"
]


# ---------------------------------------------------------
# Load JSON
# ---------------------------------------------------------

def load_json(file_name):

    with open(file_name, "r", encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------
# Basic validation
# ---------------------------------------------------------

def validate_schema(elements):

    errors = []

    for index, element in enumerate(elements):

        for field in REQUIRED_FIELDS:

            if not element.get(field):

                errors.append(
                    f"Element {index}: missing {field}"
                )

    return errors


# ---------------------------------------------------------
# Evidence validation
# ---------------------------------------------------------

def validate_evidence(element):

    evidence = element.get("evidence", "")

    if not evidence.strip():
        return False

    return True


# ---------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------

def find_duplicates(elements):

    seen = set()
    duplicates = []

    for element in elements:

        key = (
            element.get("source_name"),
            element.get("table"),
            element.get("column"),
            element.get("code_file")
        )

        if key in seen:
            duplicates.append(key)

        seen.add(key)

    return duplicates


# ---------------------------------------------------------
# Main analysis
# ---------------------------------------------------------

def analyze(file_name):

    with tracer.start_as_current_span(
        "data-element-analysis"
    ) as span:

        data = load_json(file_name)

        review_id = data.get("review_id", "")
        review_name = data.get("review_name", "")

        elements = data.get("data_elements", [])

        # Metadata
        span.set_attribute(
            "review.id",
            review_id
        )

        span.set_attribute(
            "review.name",
            review_name
        )

        span.set_attribute(
            "data_elements.total",
            len(elements)
        )

        # Schema validation
        schema_errors = validate_schema(elements)

        # Evidence validation
        evidence_missing = []

        for index, element in enumerate(elements):

            if not validate_evidence(element):

                evidence_missing.append(index)

        # Duplicate detection
        duplicates = find_duplicates(elements)

        # Confidence
        high = sum(
            1 for x in elements
            if x.get("confidence") == "HIGH"
        )

        medium = sum(
            1 for x in elements
            if x.get("confidence") == "MEDIUM"
        )

        low = sum(
            1 for x in elements
            if x.get("confidence") == "LOW"
        )

        confirmed = sum(
            1 for x in elements
            if x.get("status") == "CONFIRMED"
        )

        uncertain = sum(
            1 for x in elements
            if x.get("status") == "UNCERTAIN"
        )

        # Quality score
        total = len(elements)

        if total == 0:
            quality_score = 0
        else:
            valid = total - len(schema_errors) - len(evidence_missing)

            quality_score = round(
                max(valid, 0) / total * 100,
                2
            )

        # Phoenix attributes
        span.set_attribute(
            "validation.schema_errors",
            len(schema_errors)
        )

        span.set_attribute(
            "validation.evidence_missing",
            len(evidence_missing)
        )

        span.set_attribute(
            "validation.duplicates",
            len(duplicates)
        )

        span.set_attribute(
            "confidence.high",
            high
        )

        span.set_attribute(
            "confidence.medium",
            medium
        )

        span.set_attribute(
            "confidence.low",
            low
        )

        span.set_attribute(
            "status.confirmed",
            confirmed
        )

        span.set_attribute(
            "status.uncertain",
            uncertain
        )

        span.set_attribute(
            "quality.score",
            quality_score
        )

        # Print result
        print()
        print("=" * 60)
        print("DATA ELEMENT ANALYSIS")
        print("=" * 60)

        print(f"Review ID          : {review_id}")
        print(f"Review Name        : {review_name}")
        print(f"Total Elements     : {total}")
        print(f"Confirmed          : {confirmed}")
        print(f"Uncertain          : {uncertain}")
        print(f"High Confidence    : {high}")
        print(f"Medium Confidence  : {medium}")
        print(f"Low Confidence     : {low}")
        print(f"Schema Errors      : {len(schema_errors)}")
        print(f"Missing Evidence   : {len(evidence_missing)}")
        print(f"Duplicates         : {len(duplicates)}")
        print(f"Quality Score      : {quality_score}%")

        print("=" * 60)

        return {
            "review_id": review_id,
            "review_name": review_name,
            "total": total,
            "confirmed": confirmed,
            "uncertain": uncertain,
            "schema_errors": schema_errors,
            "evidence_missing": evidence_missing,
            "duplicates": duplicates,
            "quality_score": quality_score
        }


# ---------------------------------------------------------
# Run
# ---------------------------------------------------------

if __name__ == "__main__":

    result = analyze(
        "data_elements.json"
    )

    print("\nAnalysis completed.")