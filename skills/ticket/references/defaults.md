# Defaults (the project file overrides these; Gustavo overrides both)

- **Team / board:** the project file's. A ticket ID's prefix (`ABC-123`) names the team.
- **Labels:** the project file's set for the ticket type. Read the tracker's real labels;
  never invent one. Never add a label twice. Research gets the project's research or task
  label, never the bug label.
- **Priority:** 2 to 4 on a 1 (urgent) to 4 (low) scale, or the tracker's equivalent. Pick one
  when not given, and say you picked it. Review leftovers are the lowest.
- **Estimate:** always. Points 1, 2, 3, 5, 8 unless the project uses another scale (T-shirt
  sizes, hours). Above 5 points, or the scale's equivalent, propose a split. A tracker with no
  estimate field gets it in the description's **Estimate** section.
- **State:** the backlog state, or the "to do" state if he says it is next.
- **Assignee:** "me" for his own epic work or when he says so. The named person otherwise.
  Unassigned by default for tickets going to a coding agent.
- **Project / milestone:** leave empty unless told.
- **Parent:** the epic he names. Ask before adding follow-ups to an epic that is about to ship.
- **Relations:** always link the source ticket, PR, design file or Slack thread, and
  blocked-by when order matters.
