# Proposition Compiler Evaluator RC0 Semantic Annotation Specification

Status: FROZEN FOR RC0 DEVELOPMENT PILOT
Profile: `pc-evaluator-rc0-explicit-conjunction-v1`

## 1. Supported semantic profile

RC0 may accept only either (a) one clear independently auditable proposition (`NOT_NEEDED`) or (b) an explicit top-level conjunctive `all_of` decomposition whose children are independently propositional and whose interpretation is sufficiently explicit from the root plus authorized local context.

RC0 does not solve arbitrary ambiguity, disjunction, nested Boolean logic, pragmatic implicature, presupposition projection, generalized quantifier scope, counterfactuals, or world-knowledge decontextualization. Material dependence on those phenomena yields `INDETERMINATE`.

## 2. Conservation obligations

For root R and conjunction of children C, acceptance requires both conceptual obligations under one supported interpretation:

1. Root-supports-children: R licenses every assertion made by C. Any added relation, stronger force, changed argument binding, or invented assertion fails this direction.
2. Children-reconstruct-root: C preserves every assertion and required dependency of R. Any dropped proposition, qualifier, relation, argument, or weaker force fails this direction.

These are specification obligations, not NLI-score gates. NLI or LLM outputs may be measurement evidence only.

## 3. Binding and attachment

Presence of the same words is insufficient. Annotators must track what each operator or modifier governs. Promotion-critical bindings include population, time, location, condition, exception, attribution, restrictive modifiers, negation, modality, epistemic stance, quantification, comparison baseline/direction, temporal ordering, entity/referent, subject/object roles, and assertion/embedding type.

## 4. Propositionhood and auditability

Every declared child must express a truth-evaluable or otherwise auditable proposition within the authorized context. Bare entities, predicates without required arguments, subordinate fragments, or unresolved references are not acceptable children. Context may disambiguate a retained expression, but RC0 must not invent decontextualizing facts.

## 5. Under- and over-decomposition

Under-decomposition is behavioral: a child retains a separable explicit top-level conjunction that the RC0 profile requires to be represented as separate children.

Over-decomposition is behavioral: a split creates non-propositional fragments, breaks an inseparable relation, loses required context, duplicates an audit unit, or introduces an assertion not licensed by the root. Child count or child length alone is not a semantic defect.

## 6. Ambiguity rule

If materially different defensible readings change whether a candidate is safe, the gold disposition is `INDETERMINATE`. Majority preference cannot manufacture semantic authority. A case with unresolved gold uncertainty is removed from a decisive accept/reject gate or retained explicitly as an ambiguity probe.

## 7. Dispositions

- `ACCEPTABLE_WITHIN_PROFILE`: structurally valid, root is in profile, both conservation obligations are satisfied, children are auditable, and no promotion-critical binding defect remains.
- `REJECT_UNSAFE`: a concrete meaning-changing or profile-contract defect is positively identified.
- `INDETERMINATE`: conservation cannot be established within the supported profile, including intrinsic ambiguity or unsupported semantic structure.
- `INVALID_INPUT`: malformed evaluator input or impossible structural state.

## 8. Annotation sequence

Before viewing a mutation label or evaluator output, analyze root meaning: asserted propositions, argument roles, operators, scopes, relations, referents, assertion types, possible alternate readings, and profile membership. Then judge each candidate separately for structure, propositionhood, root-supports-children, children-reconstruct-root, attachment/binding, duplication, under/over-decomposition, and final disposition.

## 9. Gold integrity

Gold and adjudication notes are never runtime evaluator inputs. Development gold may inform RC0 evaluator development; therefore RC0 is not an independent reproduction. Fresh qualification requires frozen evaluator bytes before fresh roots, mutations, and gold are revealed to the executor.
