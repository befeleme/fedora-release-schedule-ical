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

URL_ICS = "https://fedorapeople.org/groups/schedule/f-{version}/f-{version}-key.ics"
URL_HTML = "https://fedorapeople.org/groups/schedule/f-{version}/f-{version}-key-tasks.html"

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
    cal_file = requests.get(URL_ICS.format(version=version))
    if not cal_file.ok:
        continue
    cal = Calendar(cal_file.text)
    remove_summaries = build_remove_set(version)

    # the auto closure happens for a version two numbers earlier
    omit_pattern = f"Fedora Linux {version - 2} EOL auto closure"

    for event in cal.events:
        event.make_all_day()
        if event.name in remove_summaries:
            continue
        if event.name.startswith("Final Freeze"):
            # add custom event to remind about obsoleting packages requiring the old Pythons
            obsolete_event = event.clone()
            obsolete_event.name = f"Update fedora-obsolete-packages for Fedora {version}"
            obsolete_event.end = None
            obsolete_event.uid = f"custom-update-fedora-obsolete-packages-for-fedora-{version}"
            all_events.add(obsolete_event)
        if event.name != omit_pattern:
            event.name = f"F{version}: {event.name}"
        event.url = URL_HTML.format(version=version)
        all_events.add(event)

final_cal = Calendar()
final_cal.events = all_events

with open(CALENDAR_FILENAME, "w") as f:
    for line in final_cal:
        f.write(line)
        if "PRODID" in line:
            f.write("X-WR-CALNAME:Fedora releases key tasks schedule\n")
            f.write("X-WR-CALDESC:Fedora releases key tasks schedule parsed from https://fedorapeople.org/groups/schedule/\n")
