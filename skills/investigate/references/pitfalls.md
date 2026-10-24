# Pitfalls already corrected

Each line is a mistake from a past investigation that any project invites.
Don't repeat it. Mistakes only one system invites live in its profile's
`domain.md` § Pitfalls.

- **Trusting the ticket's premise.** Release follow-up tickets assume the
  release caused the error. In most past cases it didn't. Test the premise
  like any other hypothesis.
- **Assuming the wrong code path.** A feature flag that only a few companies
  have can make a code path look central when most traffic takes the old
  one. Check the profile's `domain.md` and the flag's real reach before you build on a
  path, and say which path you assumed in the framing note.
- **A mechanism with no live case.** A race or gap found in code or in one
  dev record is not a production problem until production data shows it.
  Find the company / flow / worker that has it, or label it a hypothesis.
- **Counting on the wrong base.** A percentage needs the right denominator,
  such as rows users actually see rather than all rows. Records that are
  archived or excluded on purpose should be left out or reported
  separately.
- **Mixing up similar stores.** Use the table or collection names the code
  uses, and don't let a loose word like "summary" stand for two different
  stores.
- **Fixing the wrong place for a non-customer problem.** When only demo or
  internal accounts are hit, the fix goes where the bad data came from,
  not into code that customers depend on or that is frozen.
- **Reading code at the wrong commit.** What ran is what was deployed at
  that time (`sources.md` says where to find it). The default branch may
  already differ.
- **Sampled logs.** When the error tracker samples logs, a log count is a
  floor, not a total. Say so when you use it.
- **Unbounded acceptance criteria.** "Audit every handler for the same
  pattern" has no end. Time-box it, or file each finding as its own ticket.
- **Raw query output in the conversation.** Several past investigations ran
  out of room and had to summarize themselves halfway through. Raw output
  goes to `$CASE/evidence/`.
