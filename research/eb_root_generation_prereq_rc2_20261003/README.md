# Public root-generation prerequisite qualification RC2

RC1 stopped `BLOCKED_AUTHORITY` before the writer POST because the frozen service version was 0.34.4 while the observed local service was 0.35.1. The writer and custody attempt budgets were not consumed.

RC2 is a separate public successor. It changes exactly one controlled runtime authority value: the pinned service version becomes 0.35.1.

The RC1 launcher, execution checker, setup validator, authoring rubric, profile surface, profile-writing task, custody schema, request options, endpoint, model, model digest, information aperture, attempt budget, and stopping rules are reused byte-for-byte.

This successor does not assume that the service-version change is semantically inert. It asks whether the already-frozen prerequisite experiment can execute and pass under the currently observed service version while every other material control remains fixed.

A supported RC2 result authorizes only a later separately frozen generation execution. Generation capability remains UNKNOWN in this study.

Execution remains CONTEXT-FREE REQUIRED.
