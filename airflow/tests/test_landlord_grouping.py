"""Landlord-held-out CV must not leak units or collapse unknown contacts."""
import pandas as pd
import pytest

from ml.model_training import group_by_landlord_df


def test_company_first_and_name_fallback():
    frame = pd.DataFrame({
        "PropertyId": ["1", "1", "2", "3", "4", "5", "5"],
        "landlord_company": ["Acme Housing", "Acme Housing", " ACME  Housing ", None, "", None, None],
        "landlord_name": ["Alice", "Alice", "Bob", "Shared Contact", "Shared Contact", None, None],
    })
    groups = group_by_landlord_df(frame).tolist()
    assert groups[0] == groups[1] == groups[2] == "company:acme housing"
    assert groups[3] == groups[4] == "landlord:shared contact"
    assert groups[5] == groups[6] == "property:5"
    assert groups[5] != groups[3]


def test_missing_contacts_do_not_collapse_unrelated_properties():
    frame = pd.DataFrame({
        "PropertyId": ["1", "1", "2", "3"],
        "landlord_company": [None, "", "Not Found", None],
        "landlord_name": [None, "N/A", "Unknown", ""],
    })
    assert group_by_landlord_df(frame).tolist() == [
        "property:1", "property:1", "property:2", "property:3"
    ]


def test_conflicting_company_values_for_one_property_raise():
    frame = pd.DataFrame({
        "PropertyId": ["1", "1"],
        "landlord_company": ["Acme", "Other"],
        "landlord_name": ["Alice", "Alice"],
    })
    with pytest.raises(ValueError, match="Conflicting landlord_company"):
        group_by_landlord_df(frame)


def test_non_default_dataframe_index_preserved():
    frame = pd.DataFrame({"PropertyId": ["1", "2"],
                          "landlord_name": ["Alice", "Alice"]},
                         index=[20, 40])
    groups = group_by_landlord_df(frame)
    assert groups.index.tolist() == [20, 40]
    assert groups.tolist() == ["landlord:alice", "landlord:alice"]
