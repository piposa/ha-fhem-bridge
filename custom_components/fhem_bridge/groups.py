"""Group catalog entries while preserving their separate FHEM identities."""

from collections import defaultdict


def automatic_groups(catalog):
    buckets = defaultdict(list)
    for device, item in catalog.items():
        if key := item.get("group"):
            buckets[key].append(device)
    groups = {}
    for key, members in buckets.items():
        if key in catalog:
            members = [key, *(source for source in members if source != key)]
        else:
            members.sort(key=lambda device: (catalog[device].get("channel") is not None, device))
        if len(members) > 1:
            groups[key] = {"primary": members[0], "members": members}
    return groups


def member_index(groups, selected):
    """Resolve selected sources to group IDs, excluding unused group records."""
    return {
        source: group_id
        for group_id, group in groups.items()
        for source in group["members"]
        if source in selected
    }


def merge_manual(groups, anchor, members, *, group_key=None):
    """Explicit groups take precedence over module-discovered groups."""
    chosen = {anchor, *members}
    for group_id, group in tuple(groups.items()):
        rest = [member for member in group["members"] if member not in chosen]
        if len(rest) <= 1:
            groups.pop(group_id)
        elif len(rest) != len(group["members"]):
            groups[group_id] = {**group, "members": rest,
                                "primary": group["primary"] if group["primary"] in rest else rest[0]}
    groups[group_key or anchor] = {"primary": anchor, "members": [anchor, *sorted(chosen - {anchor})], "manual": True}
