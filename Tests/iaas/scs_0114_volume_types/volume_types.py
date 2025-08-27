from collections import Counter, defaultdict
import logging
import re
import typing


logger = logging.getLogger(__name__)
RECOGNIZED_FEATURES = ('encrypted', 'replicated')
ERRONEOUS = object()  # use this as key in volume_type_lookup for erroneous volume types


def _extract_feature_list(description, pattern=re.compile(r"\[scs:([^\[\]]*)\]")):
    """Extract feature-list-like prefix

    If given `description` starts with a feature-list-like prefix, return list of features,
    otherwise None. To be more precise, we look for a string of this form:

    `[scs:`feat1`, `...`, `...featN`]`

    where N >= 1 and featJ is a string that doesn't contain any comma or brackets. We return
    the list [feat1, ..., featN] of substrings.
    """
    if not description:
        # The description can be None or empty - we need to catch this here
        return
    match = pattern.match(description)
    if not match:
        return
    fs = match.group(1)
    if not fs:
        return []
    return [f.strip() for f in fs.split(",")]


def _test_feature_list(type_name: str, fl: typing.List[str], recognized=RECOGNIZED_FEATURES) -> typing.List[str]:
    """Test given list of features and return list of errors"""
    if not fl:
        # either None (no feature list) or empty feature list: nothing to check
        return
    errors = []
    if fl != sorted(fl):
        errors.append(f"{type_name}: feature list not sorted")
    ctr = Counter(fl)
    duplicates = [key for key, c in ctr.items() if c > 1]
    if duplicates:
        errors.append(f"{type_name}: duplicate features: {', '.join(duplicates)}")
    unrecognized = [f for f in ctr if f not in recognized]
    if unrecognized:
        errors.append(f"{type_name}: unrecognized features: {', '.join(unrecognized)}")
    return errors


def compute_volume_type_lookup(volume_types):
    # collect volume types according to features
    by_feature = defaultdict(list)
    for typ in volume_types:
        fl = _extract_feature_list(typ.description)
        if fl is None:
            continue
        logger.debug(f"{typ.name}: feature list {fl!r}")
        errors = _test_feature_list(typ.name, fl)
        if errors:
            by_feature[ERRONEOUS].extend(errors)
        for feat in fl:
            by_feature[feat].append(typ.name)
    return by_feature


def compute_scs_0114_syntax_check(volume_type_lookup):
    errors = volume_type_lookup.get(ERRONEOUS, ())
    for line in errors:
        logger.error(line)
    return not errors


def compute_scs_0114_aspect_type(volume_type_lookup, aspect):
    applicable = volume_type_lookup[aspect]
    if not applicable:
        logger.error(f"no volume type having aspect {aspect}")
    return bool(applicable)
