# Pitfalls already corrected

Each line is a mistake from a past investigation. Don't repeat it.

- **Trusting the ticket's premise.** Release follow-up tickets assume the
  release caused the error. In most past cases it didn't. Test the premise
  like any other hypothesis.
- **Assuming the wrong code path.** A feature flag that only a few companies
  have can make a code path look central when most traffic takes the old
  one. Check `domain.md` and the flag's real reach before you build on a
  path, and say which path you assumed in the framing note.
- **A mechanism with no live case.** A race or gap found in code or in one
  dev record is not a production problem until production data shows it.
  Find the company / flow / worker that has it, or label it a hypothesis.
- **Counting on the wrong base.** A percentage needs the right denominator,
  such as rows users actually see rather than all rows. Records that are
  archived or excluded on purpose (for example, workers with no segments)
  should be left out or reported separately.
- **Mixing up similar collections.** Use the collection names the code
  uses, and don't let a loose word like "summary" stand for two different
  stores.
- **Fixing frozen code for a non-customer problem.** When only demo or
  internal companies are hit, the fix goes where the bad data came from,
  not into code that is frozen for customers.
- **Reading code at the wrong commit.** What ran in production is on the
  production branch at that time. Main may already differ.
- **Sentry logs are sampled.** A log count is a floor, not a total. Say
  so when you use it.
- **Unbounded acceptance criteria.** "Audit every handler for the same
  pattern" has no end. Time-box it, or file each finding as its own ticket.
- **Raw query output in the conversation.** Several past investigations ran
  out of room and had to summarize themselves halfway through. Raw output
  goes to `$CASE/evidence/`.
