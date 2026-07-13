"""Data loading and demographic enrichment for child coverage reports."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

DEFAULT_INPUT = Path(
    "results/big_cleaned_dataset/default_naturalistic_merged_006_023/"
    "all_child_longitudinal_age_coverage_summary.csv"
)
DEFAULT_AGE_POINTS = Path(
    "results/big_cleaned_dataset/default_naturalistic_merged_006_023/all_child_longitudinal_age_points.csv"
)
DEFAULT_DEMOGRAPHIC_CODEBOOK = Path(
    "results/metadata/strict_naturalistic_child_demographic_codebook_2026-06-03.csv"
)
DEFAULT_ONLINE_VALUE_PATCHES = Path("configs/child_demographic_online_value_patches.csv")
DEFAULT_ONLINE_RESEARCH_AUDIT = Path("configs/child_demographic_online_research_audit.csv")

DATASET_REGIONS = {
    "Belfast": "UK / Northern Ireland",
    "Brown": "US",
    "Demetras1": "US",
    "Forrester": "UK",
    "Kuczaj": "US",
    "Lara": "UK",
    "MPI-EVA-Manchester": "UK",
    "Manchester": "UK",
    "Post": "US",
    "Providence": "US",
    "Sachs": "US",
    "Weist": "US",
    "Wells": "UK",
}

UNKNOWN_VALUES = {
    "",
    "nan",
    "none",
    "not_available_in_current_extracted_metadata",
    "not_extracted",
    "unavailable",
    "unavailable_in_current_metadata",
    "unknown",
}

ONLINE_PATCH_COLUMNS = [
    "dataset",
    "child_id",
    "field",
    "value",
    "scope",
    "source_type",
    "source_url",
    "source_note",
    "confidence",
    "replace_policy",
    "coding_note",
]

ONLINE_AUDIT_COLUMNS = [
    "dataset",
    "child_id",
    "fields_checked",
    "result",
    "source_type",
    "source_url",
    "source_note",
    "coding_decision",
]


def fmt(value: object, digits: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "" if value is None else str(value)
    if not math.isfinite(number):
        return ""
    if abs(number - round(number)) < 1e-9:
        return f"{int(round(number)):,}"
    return f"{number:,.{digits}f}"


def known(value: object) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    return text not in UNKNOWN_VALUES


def scope_class(scope: object) -> str:
    text = "" if scope is None else str(scope).strip().lower()
    if text == "child_specific":
        return "child-specific"
    if text in {"corpus_level_single_child", "corpus_level"}:
        return "corpus-level"
    if text in {"corpus_level_predominant", "community_or_study_population", "community_description"}:
        return "predominant/community-level"
    return "unknown/unavailable"


def read_counts(path: Path) -> pd.DataFrame:
    usecols = [
        "dataset",
        "child_id",
        "child_utterances_in_route1_age_range",
        "child_sessions",
        "child_files",
        "child_age_min_months",
        "child_age_max_months",
        "child_age_bins",
    ]
    frame = pd.read_csv(path, usecols=usecols)
    frame = frame.rename(columns={"child_utterances_in_route1_age_range": "child_utterances"})
    frame["child_utterances"] = pd.to_numeric(frame["child_utterances"], errors="coerce")
    frame["child_label"] = frame["dataset"] + " / " + frame["child_id"]
    return frame.sort_values("child_utterances", ascending=False).reset_index(drop=True)


def read_age_points(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["age_months"] = pd.to_numeric(frame["age_months"], errors="coerce")
    frame["n_utterances"] = pd.to_numeric(frame["n_utterances"], errors="coerce")
    frame["child_label"] = frame["dataset"] + " / " + frame["child_id"]
    return frame.dropna(subset=["age_months"])


def read_demographic_codebook(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["dataset", "child_id"])

    columns = [
        "dataset",
        "child_id",
        "sex",
        "local_chat_group_values",
        "local_chat_ses_values",
        "local_chat_education_values",
        "local_demographic_header_available",
        "ses_category",
        "ses_label",
        "ses_scope",
        "ses_source_type",
        "ses_source_url",
        "ses_source_note",
        "ses_confidence",
        "race_ethnicity",
        "race_scope",
        "race_source_type",
        "race_source_url",
        "race_source_note",
        "race_confidence",
        "parental_education",
        "parental_education_scope",
        "parental_education_source_url",
        "parental_education_source_note",
        "demographic_notes",
        "ses_usable_as_core_predictor",
        "race_usable_as_core_predictor",
    ]
    frame = pd.read_csv(path, usecols=lambda col: col in columns)
    return frame.fillna("unknown")


def _read_optional_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    frame = pd.read_csv(path)
    for col in columns:
        if col not in frame.columns:
            frame[col] = ""
    return frame[columns].fillna("")


def read_online_value_patches(path: Path) -> pd.DataFrame:
    return _read_optional_csv(path, ONLINE_PATCH_COLUMNS)


def read_online_research_audit(path: Path) -> pd.DataFrame:
    return _read_optional_csv(path, ONLINE_AUDIT_COLUMNS)


def add_default_source_columns(profile: pd.DataFrame) -> pd.DataFrame:
    out = profile.copy()
    source_defaults = {
        "sex": {
            "scope": "child_specific",
            "source_type": "local_extracted_metadata",
            "source_url": "local_extracted_metadata",
            "source_note": "Sex/gender marker came from local extracted CHAT/metadata rows.",
            "confidence": "medium",
            "coding_note": "existing local value",
        }
    }
    for field, defaults in source_defaults.items():
        value_known = out[field].map(known) if field in out.columns else pd.Series(False, index=out.index)
        for suffix, default in defaults.items():
            col = f"{field}_{suffix}"
            if col not in out.columns:
                out[col] = "unknown"
            out.loc[value_known, col] = default
    return out


def apply_online_value_patches(profile: pd.DataFrame, patches: pd.DataFrame) -> pd.DataFrame:
    out = add_default_source_columns(profile)
    if patches.empty:
        return out

    for _, patch in patches.iterrows():
        field = str(patch["field"]).strip()
        if not field:
            continue
        if field not in out.columns:
            out[field] = "unknown"

        dataset = str(patch["dataset"]).strip()
        child_id = str(patch["child_id"]).strip()
        if child_id == "*":
            mask = out["dataset"].eq(dataset)
        else:
            mask = out["dataset"].eq(dataset) & out["child_id"].eq(child_id)
        if not mask.any():
            continue

        replace_policy = str(patch.get("replace_policy", "fill_unknown")).strip() or "fill_unknown"
        if replace_policy == "fill_unknown":
            mask = mask & ~out[field].map(known)
        elif replace_policy != "replace":
            raise ValueError(f"Unknown replace_policy: {replace_policy}")
        if not mask.any():
            continue

        out.loc[mask, field] = patch["value"]
        for patch_col, suffix in [
            ("scope", "scope"),
            ("source_type", "source_type"),
            ("source_url", "source_url"),
            ("source_note", "source_note"),
            ("confidence", "confidence"),
            ("coding_note", "coding_note"),
        ]:
            out.loc[mask, f"{field}_{suffix}"] = patch[patch_col]
    return out


def build_child_metadata_profile(
    counts: pd.DataFrame,
    codebook: pd.DataFrame,
    *,
    online_patches: pd.DataFrame | None = None,
) -> pd.DataFrame:
    profile = counts.merge(codebook, on=["dataset", "child_id"], how="left")
    required_defaults = {
        "sex": "unknown",
        "ses_category": "unknown",
        "ses_label": "unknown",
        "ses_scope": "unknown",
        "ses_confidence": "unknown",
        "race_ethnicity": "unknown",
        "race_scope": "unknown",
        "race_confidence": "unknown",
        "parental_education": "unknown",
        "parental_education_scope": "unknown",
        "ses_usable_as_core_predictor": "no",
        "race_usable_as_core_predictor": "no",
    }
    for col, default in required_defaults.items():
        if col not in profile.columns:
            profile[col] = default
    text_cols = profile.select_dtypes(include=["object"]).columns
    profile[text_cols] = profile[text_cols].fillna("unknown")
    profile["corpus_region"] = profile["dataset"].map(DATASET_REGIONS).fillna("unknown")
    profile["child_specific_nationality"] = "not_available_in_current_extracted_metadata"
    profile = apply_online_value_patches(
        profile,
        online_patches if online_patches is not None else pd.DataFrame(columns=ONLINE_PATCH_COLUMNS),
    )
    profile["sex_available"] = profile["sex"].map(known)
    profile["ses_available"] = profile["ses_category"].map(known)
    profile["race_available"] = profile["race_ethnicity"].map(known)
    profile["parental_education_available"] = profile["parental_education"].map(known)
    profile["nationality_available"] = False
    profile["ses_scope_class"] = profile["ses_scope"].map(scope_class)
    profile["race_scope_class"] = profile["race_scope"].map(scope_class)
    profile["parental_education_scope_class"] = profile["parental_education_scope"].map(scope_class)
    profile["sex_scope_class"] = profile["sex_scope"].map(scope_class)
    profile["age_range_months"] = (
        profile["child_age_min_months"].map(lambda value: fmt(value, 1))
        + "-"
        + profile["child_age_max_months"].map(lambda value: fmt(value, 1))
    )
    return profile.sort_values(["dataset", "child_id"]).reset_index(drop=True)


def field_availability(profile: pd.DataFrame) -> pd.DataFrame:
    rows = []

    scoped_fields = [
        (
            "SES / social class",
            "ses_available",
            "ses_scope_class",
            "Current codebook combines local CHAT metadata and manual TalkBank page checks.",
        ),
        (
            "Race / ethnicity",
            "race_available",
            "race_scope_class",
            "Sparse; community-level descriptions should not be treated as child-specific race codes.",
        ),
        (
            "Parental education",
            "parental_education_available",
            "parental_education_scope_class",
            "Available only when documented in corpus-level or child-specific notes.",
        ),
        (
            "Sex / gender marker",
            "sex_available",
            "sex_scope_class",
            "From local extracted metadata plus documented online patches; label kept as sex because that is the source-field name.",
        ),
    ]
    for field, known_col, scope_col, note in scoped_fields:
        subset = profile[profile[known_col]]
        rows.append(
            {
                "field": field,
                "known_child_specific": int((subset[scope_col] == "child-specific").sum()),
                "known_corpus_level": int((subset[scope_col] == "corpus-level").sum()),
                "known_predominant_or_community": int(
                    (subset[scope_col] == "predominant/community-level").sum()
                ),
                "unknown_or_unavailable": int((~profile[known_col]).sum()),
                "total_children": int(len(profile)),
                "note": note,
            }
        )

    rows.extend(
        [
            {
                "field": "Child-specific nationality",
                "known_child_specific": 0,
                "known_corpus_level": 0,
                "known_predominant_or_community": 0,
                "unknown_or_unavailable": int(len(profile)),
                "total_children": int(len(profile)),
                "note": "Not currently extracted locally. Corpus region is shown separately and must not be interpreted as nationality.",
            },
            {
                "field": "Corpus region",
                "known_child_specific": 0,
                "known_corpus_level": int(profile["corpus_region"].map(known).sum()),
                "known_predominant_or_community": 0,
                "unknown_or_unavailable": int((~profile["corpus_region"].map(known)).sum()),
                "total_children": int(len(profile)),
                "note": "Dataset-level geography only.",
            },
        ]
    )
    return pd.DataFrame(rows)


def dataset_metadata_summary(profile: pd.DataFrame) -> pd.DataFrame:
    summary = (
        profile.groupby("dataset", as_index=False)
        .agg(
            children=("child_id", "nunique"),
            child_utterances=("child_utterances", "sum"),
            sex_known=("sex_available", "sum"),
            ses_known=("ses_available", "sum"),
            race_known=("race_available", "sum"),
            parent_education_known=("parental_education_available", "sum"),
            corpus_regions=("corpus_region", lambda values: "; ".join(sorted(set(values)))),
        )
        .sort_values(["children", "dataset"], ascending=[False, True])
    )
    for col in ["sex_known", "ses_known", "race_known", "parent_education_known"]:
        summary[col] = summary[col].astype(int)
    return summary


def child_profile_display(profile: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "dataset",
        "child_id",
        "child_utterances",
        "child_sessions",
        "age_range_months",
        "child_age_bins",
        "sex",
        "sex_source_type",
        "corpus_region",
        "child_specific_nationality",
        "ses_label",
        "ses_scope",
        "ses_confidence",
        "race_ethnicity",
        "race_scope",
        "race_confidence",
        "parental_education",
        "parental_education_scope",
        "ses_usable_as_core_predictor",
        "race_usable_as_core_predictor",
    ]
    existing = [col for col in columns if col in profile.columns]
    return profile[existing].sort_values(["dataset", "child_id"]).reset_index(drop=True)


def child_source_display(profile: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "dataset",
        "child_id",
        "sex_source_type",
        "sex_source_url",
        "sex_source_note",
        "sex_confidence",
        "ses_source_type",
        "ses_source_url",
        "ses_source_note",
        "race_source_type",
        "race_source_url",
        "race_source_note",
        "parental_education_source_url",
        "parental_education_source_note",
        "demographic_notes",
    ]
    existing = [col for col in columns if col in profile.columns]
    source_frame = profile[existing].copy()
    mask = pd.Series(False, index=source_frame.index)
    if "sex_source_type" in source_frame.columns:
        mask = mask | ~source_frame["sex_source_type"].isin(["unknown", "local_extracted_metadata"])
    for col in [
        "ses_source_type",
        "ses_source_url",
        "ses_source_note",
        "race_source_type",
        "race_source_url",
        "race_source_note",
        "parental_education_source_url",
        "parental_education_source_note",
        "demographic_notes",
    ]:
        if col in source_frame.columns:
            mask = mask | source_frame[col].map(known)
    return (
        source_frame.loc[mask]
        .sort_values(["dataset", "child_id"])
        .reset_index(drop=True)
    )
