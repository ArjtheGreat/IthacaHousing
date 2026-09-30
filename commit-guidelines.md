# Commit Guidelines

These rules apply to every agent (and human) committing to this repo.

## The format

Every commit message is a Family Guy cutaway. It must start with:

```
this reminds me of the time I <what the commit does>
```

Describe the change in the past tense, as something you once did, the way Peter sets up a cutaway.

## Examples

```
this reminds me of the time I added a budget filter to the rent map
this reminds me of the time I fixed the 500 on every filter request
this reminds me of the time I moved the no-results alert above the map
this reminds me of the time I bumped the pytest version
```

## Rules

- Start with `this reminds me of the time I`, all lowercase, exactly as written.
- After that, say what the commit actually does. Keep the joke in the framing and make the content accurate. Someone reading `git log` should still learn what changed.
- One line only, with no body and no trailing period.
- One cutaway per commit. If you need "and" to describe the change, split it into two commits.
- No co-author trailers, session links, or "Generated with" lines.

## Not allowed

```
fix map                                          # not a cutaway
This reminds me of the time I fixed the map.     # capitalized, trailing period
this reminds me of the time I did some stuff     # says nothing about the change
```
