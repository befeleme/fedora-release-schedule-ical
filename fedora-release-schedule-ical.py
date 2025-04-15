# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "ics",
#     "requests",
# ]
# ///
from ics import Calendar

import requests


CALENDAR_FILENAME = "fedora-releases.ics"

# non-existent calendars are skipped so don"t be shy and
# add more of those as they approach
FEDORA_VERSIONS = (42, 43, 44, 45, 46, 47, 48, 49, 50)

SUMMARY_PATTERNS = {
    "Fedora Linux {f_version} release",
    "Key Tasks & Milestones",
    "RelEng",
    "Spins SIG",
    "Keepalive deadline for spins",
    "Post Release Cleanup",
    "Post Release Cleanup [rel-eng]",
    "Beta Release Public Availability",
    "Final Release Public Availability (GA)",
}


def build_remove_set(version):
    return {pattern.format(f_version=version) for pattern in SUMMARY_PATTERNS}


all_events = set()
for version in FEDORA_VERSIONS:
    cal_file = requests.get(f"https://fedorapeople.org/groups/schedule/f-{version}/f-{version}-key.ics")
    if not cal_file.ok:
        continue
    cal = Calendar(cal_file.text)
    remove_summaries = build_remove_set(version)

    for event in cal.events:
        event.make_all_day()
        if event.name in remove_summaries:
            continue
        if event.name.startswith("Final Freeze"):
            # add custom event to remind about obsoleting packages requiring the old Pythons
            obsolete_event = event.clone()
            obsolete_event.name = f"Update fedora-obsolete-packages for Fedora {version}"
            all_events.add(obsolete_event)
        event.name = f"F{version}: {event.name}"
        all_events.add(event)

final_cal = Calendar()
final_cal.events = all_events

with open(CALENDAR_FILENAME, "w") as f:
    for line in final_cal:
        f.write(line)
        if "PRODID" in line:
            f.write("X-WR-CALNAME:Fedora releases key tasks schedule\n")
            f.write("X-WR-CALDESC:Fedora releases key tasks schedule parsed from https://fedorapeople.org/groups/schedule/\n")
