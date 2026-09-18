from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
CAPS = (0.01, 0.03, 0.05, 0.10)
BUDGET = 3

SUBJECT_RE = re.compile(r"\b(?:Valve|Unit|Channel|Rack|Sensor|Loop)\s+\d+\b", re.I)
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
REV_RE = re.compile(r"\brevision\s+\d+(?:\.\d+)?\b", re.I)
DURATION_RE = re.compile(r"\b\d+(?:\.\d+)?[- ]minute\b", re.I)
THRESHOLD_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:bar|psi|kpa|degrees?\s*C)\b", re.I)
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")

EVENT_RE = re.compile(
    r"\b(?:event log|log entry|audit trail|witness record|inspection record|"
    r"run record|batch record|recorded|logged|observed)\b",
    re.I,
)
REGISTRY_RE = re.compile(
    r"\b(?:registry|register|database|inventory|certificate|certified)\b",
    re.I,
)
DECL_RE = re.compile(
    r"\b(?:policy|manual|procedure|specification|declaration|states that|"
    r"requires|shall|must)\b",
    re.I,
)
MEAS_RE = re.compile(
    r"\b(?:measurement|measured|reading|gauge|sensor reading|test value)\b",
    re.I,
)

STOP = {
    "the","a","an","and","or","of","to","for","during","was","is","are","remained",
    "remain","record","recorded","entry","shows","showed","indicates","indicated",
    "that","this","it","in","on","at","by","with","from","under","after","before",
    "its","their","same","while","within","throughout","current","required",
}


@dataclass(frozen=True)
class Child:
    child_id: str
    text: str
    subject: str | None
    inherited_subject: str | None
    scope: str | None
    wrong_subject: str | None
    wrong_scope: str | None
    expected_form: str
    wrong_form: str
    predicate_terms: tuple[str, ...]


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    text: str
    gold_class: str
    required_for: tuple[str, ...]


@dataclass(frozen=True)
class Case:
    case_id: str
    category: str
    parent_text: str
    children: tuple[Child, Child]
    candidates: tuple[Candidate, ...]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def subject_from(text: str) -> str | None:
    match = SUBJECT_RE.search(text)
    return None if match is None else match.group(0)


def scope_from(text: str) -> str | None:
    for pattern in (DATE_RE, REV_RE, DURATION_RE, THRESHOLD_RE):
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def predicate_terms(text: str, subject: str | None, scope: str | None) -> tuple[str, ...]:
    excluded = set()
    for value in (subject, scope):
        if value:
            excluded.update(token.lower() for token in WORD_RE.findall(value))
    terms = []
    for token in WORD_RE.findall(text):
        value = token.lower()
        if len(value) < 3 or value in STOP or value in excluded:
            continue
        terms.append(value)
    return tuple(sorted(set(terms)))


def child(
    child_id: str,
    text: str,
    *,
    inherited_subject: str | None,
    wrong_subject: str | None,
    wrong_scope: str | None,
    expected_form: str,
    wrong_form: str,
) -> Child:
    explicit = subject_from(text)
    scope = scope_from(text)
    return Child(
        child_id=child_id,
        text=text,
        subject=explicit,
        inherited_subject=inherited_subject if explicit is None else None,
        scope=scope,
        wrong_subject=wrong_subject,
        wrong_scope=wrong_scope,
        expected_form=expected_form,
        wrong_form=wrong_form,
        predicate_terms=predicate_terms(text, explicit, scope),
    )


def c(candidate_id: str, text: str, gold_class: str, *required_for: str) -> Candidate:
    return Candidate(candidate_id, text, gold_class, tuple(required_for))


def build_cases() -> list[Case]:
    cases: list[Case] = []

    # 1. STARVATION: multiple attractive child-A candidates compete with one child-B item.
    starvation_subjects = [("Valve 2","Valve 3"),("Unit 4","Unit 5"),("Channel 6","Channel 7"),("Rack 8","Rack 9")]
    for idx,(subj,other) in enumerate(starvation_subjects, start=1):
        cid=f"STARVATION-{idx:02d}"
        a=f"{cid}-A"; b=f"{cid}-B"
        parent=f"{subj} remained closed during the 21-minute verification hold and its witness inspection was signed."
        ca=child(a,f"{subj} remained closed during the 21-minute verification hold.",inherited_subject=None,wrong_subject=other,wrong_scope="18-minute",expected_form="event_record",wrong_form="authoritative_declaration")
        cb=child(b,f"the witness inspection was signed.",inherited_subject=subj,wrong_subject=other,wrong_scope=None,expected_form="event_record",wrong_form="authoritative_declaration")
        candidates=(
            c(f"{cid}-01",f"Event log: {subj} remained closed throughout the 21-minute verification hold.","REQUIRED",a),
            c(f"{cid}-02",f"Run record notes {subj} stayed closed for the full 21-minute verification hold.","REDUNDANT",a),
            c(f"{cid}-03",f"Audit trail confirms no opening of {subj} during the 21-minute verification hold.","REDUNDANT",a),
            c(f"{cid}-04",f"Witness record for {subj}: the inspection bears the operator signature.","REQUIRED",b),
            c(f"{cid}-05",f"Policy requires {subj} to remain closed during verification holds.","DISTRACTOR"),
            c(f"{cid}-06",f"Event log: {other} remained closed throughout the 21-minute verification hold.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-07",f"Witness record for {other}: the inspection bears the operator signature.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-08",f"Maintenance note discusses the verification hold but does not record closure or signature state.","DISTRACTOR"),
            c(f"{cid}-09",f"Procedure states that witness inspections should be signed before release.","DISTRACTOR"),
            c(f"{cid}-10",f"Training example describes a different device that stayed closed during a 20-minute hold.","DISTRACTOR"),
        )
        cases.append(Case(cid,"STARVATION",parent,(ca,cb),candidates))

    # 2. NO_STARVATION_CONTROL: two highly direct required candidates should already compete well.
    controls = [("Valve 12","Valve 13"),("Unit 14","Unit 15"),("Channel 16","Channel 17"),("Rack 18","Rack 19")]
    for idx,(subj,other) in enumerate(controls, start=1):
        cid=f"NO-STARVATION-{idx:02d}"
        a=f"{cid}-A"; b=f"{cid}-B"
        parent=f"{subj} passed its closure inspection and its identity scan was logged."
        ca=child(a,f"{subj} passed its closure inspection.",inherited_subject=None,wrong_subject=other,wrong_scope=None,expected_form="event_record",wrong_form="authoritative_declaration")
        cb=child(b,f"{subj} identity scan was logged.",inherited_subject=None,wrong_subject=other,wrong_scope=None,expected_form="event_record",wrong_form="authoritative_declaration")
        candidates=(
            c(f"{cid}-01",f"Inspection record: {subj} passed the closure inspection.","REQUIRED",a),
            c(f"{cid}-02",f"Audit log: {subj} identity scan was logged successfully.","REQUIRED",b),
            c(f"{cid}-03",f"Run record repeats that {subj} passed the closure inspection.","REDUNDANT",a),
            c(f"{cid}-04",f"Database note references an identity scan for {other}, not {subj}.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-05",f"Policy requires closure inspection before use.","DISTRACTOR"),
            c(f"{cid}-06",f"Procedure requires identity scans to be logged.","DISTRACTOR"),
            c(f"{cid}-07",f"Inspection record: {other} passed the closure inspection.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-08",f"Training material describes closure inspections generally.","DISTRACTOR"),
            c(f"{cid}-09",f"Maintenance record lists the scanner model but not the scan event.","DISTRACTOR"),
            c(f"{cid}-10",f"General operating manual discusses release controls.","DISTRACTOR"),
        )
        cases.append(Case(cid,"NO_STARVATION_CONTROL",parent,(ca,cb),candidates))

    # 3. EXPLICIT_SUBJECT_CONFLICT: children name their own target, sibling entity is highly competitive.
    explicit = [("Valve 22","Valve 23"),("Unit 24","Unit 25"),("Channel 26","Channel 27"),("Rack 28","Rack 29")]
    for idx,(subj,other) in enumerate(explicit, start=1):
        cid=f"EXPLICIT-SUBJECT-{idx:02d}"
        a=f"{cid}-A"; b=f"{cid}-B"
        parent=f"{subj} remained closed and {subj} witness inspection was signed."
        ca=child(a,f"{subj} remained closed.",inherited_subject=None,wrong_subject=other,wrong_scope=None,expected_form="event_record",wrong_form="authoritative_declaration")
        cb=child(b,f"{subj} witness inspection was signed.",inherited_subject=None,wrong_subject=other,wrong_scope=None,expected_form="event_record",wrong_form="authoritative_declaration")
        candidates=(
            c(f"{cid}-01",f"Event log: {other} remained closed during the run.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-02",f"Event log: {subj} remained closed during the run.","REQUIRED",a),
            c(f"{cid}-03",f"Witness record: {other} inspection was signed by the operator.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-04",f"Witness record: {subj} inspection was signed by the operator.","REQUIRED",b),
            c(f"{cid}-05",f"Policy says {subj} should remain closed during the run.","DISTRACTOR"),
            c(f"{cid}-06",f"Policy says {other} should remain closed during the run.","DISTRACTOR"),
            c(f"{cid}-07",f"Maintenance note mentions both {subj} and {other}.","DISTRACTOR"),
            c(f"{cid}-08",f"Training record discusses signed inspections for similar equipment.","DISTRACTOR"),
            c(f"{cid}-09",f"Audit summary references the run without naming a valve state.","DISTRACTOR"),
            c(f"{cid}-10",f"Procedure defines what a signed inspection means.","DISTRACTOR"),
        )
        cases.append(Case(cid,"EXPLICIT_SUBJECT_CONFLICT",parent,(ca,cb),candidates))

    # 4. INHERITED_SUBJECT_CONFLICT: children are elliptical; only parent carries subject.
    inherited = [("Valve 32","Valve 33"),("Unit 34","Unit 35"),("Channel 36","Channel 37"),("Rack 38","Rack 39")]
    for idx,(subj,other) in enumerate(inherited, start=1):
        cid=f"INHERITED-SUBJECT-{idx:02d}"
        a=f"{cid}-A"; b=f"{cid}-B"
        parent=f"For {subj}, the closure check passed and the witness record was signed."
        ca=child(a,"the closure check passed.",inherited_subject=subj,wrong_subject=other,wrong_scope=None,expected_form="event_record",wrong_form="authoritative_declaration")
        cb=child(b,"the witness record was signed.",inherited_subject=subj,wrong_subject=other,wrong_scope=None,expected_form="event_record",wrong_form="authoritative_declaration")
        candidates=(
            c(f"{cid}-01",f"Inspection record: {other} closure check passed.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-02",f"Inspection record: {subj} closure check passed.","REQUIRED",a),
            c(f"{cid}-03",f"Witness record for {other} was signed.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-04",f"Witness record for {subj} was signed.","REQUIRED",b),
            c(f"{cid}-05",f"Procedure says closure checks must pass.","DISTRACTOR"),
            c(f"{cid}-06",f"Procedure says witness records must be signed.","DISTRACTOR"),
            c(f"{cid}-07",f"Maintenance note lists {subj} and {other} together.","DISTRACTOR"),
            c(f"{cid}-08",f"Event summary says a closure check passed but omits the equipment identity.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-09",f"Event summary says a witness record was signed but omits the equipment identity.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-10",f"Training note demonstrates a generic closure check.","DISTRACTOR"),
        )
        cases.append(Case(cid,"INHERITED_SUBJECT_CONFLICT",parent,(ca,cb),candidates))

    # 5. SCOPE_CONFLICT: exact subject/predicate match, wrong scope is dangerous.
    scopes = [
        ("Valve 42","revision 3.0","revision 4.0"),
        ("Unit 44","2026-08-27","2026-08-28"),
        ("Channel 46","21-minute","18-minute"),
        ("Rack 48","3.3 bar","3.8 bar"),
    ]
    for idx,(subj,good_scope,bad_scope) in enumerate(scopes, start=1):
        cid=f"SCOPE-{idx:02d}"
        a=f"{cid}-A"; b=f"{cid}-B"
        if "revision" in good_scope:
            parent=f"{subj} was approved under {good_scope} and its release record was signed under {good_scope}."
            at=f"{subj} was approved under {good_scope}."
            bt=f"{subj} release record was signed under {good_scope}."
        elif good_scope.startswith("2026"):
            parent=f"As of {good_scope}, {subj} was active and its release record was signed."
            at=f"As of {good_scope}, {subj} was active."
            bt=f"As of {good_scope}, {subj} release record was signed."
        elif "minute" in good_scope:
            parent=f"{subj} remained stable during the {good_scope} hold and its witness record covered the {good_scope} hold."
            at=f"{subj} remained stable during the {good_scope} hold."
            bt=f"{subj} witness record covered the {good_scope} hold."
        else:
            parent=f"{subj} remained below {good_scope} and its test record reports a reading below {good_scope}."
            at=f"{subj} remained below {good_scope}."
            bt=f"{subj} test record reports a reading below {good_scope}."
        ca=child(a,at,inherited_subject=None,wrong_subject=None,wrong_scope=bad_scope,expected_form="event_record",wrong_form="authoritative_declaration")
        cb=child(b,bt,inherited_subject=None,wrong_subject=None,wrong_scope=bad_scope,expected_form="event_record",wrong_form="authoritative_declaration")
        candidates=(
            c(f"{cid}-01",f"Event log for {subj}: {at.replace(subj,'').strip()}","REQUIRED",a),
            c(f"{cid}-02",f"Event log for {subj}: {at.replace(good_scope,bad_scope).replace(subj,'').strip()}","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-03",f"Run record for {subj}: {bt.replace(subj,'').strip()}","REQUIRED",b),
            c(f"{cid}-04",f"Run record for {subj}: {bt.replace(good_scope,bad_scope).replace(subj,'').strip()}","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-05",f"Policy requires records to reflect the applicable scope for {subj}.","DISTRACTOR"),
            c(f"{cid}-06",f"Manual discusses {subj} without giving the tested scope.","DISTRACTOR"),
            c(f"{cid}-07",f"Event log mentions {subj} and {bad_scope} in a different run.","UNSAFE_OR_MISLEADING"),
            c(f"{cid}-08",f"Training example uses {good_scope} but describes another device.","DISTRACTOR"),
            c(f"{cid}-09",f"Administrative note mentions {good_scope} with no observed result.","DISTRACTOR"),
            c(f"{cid}-10",f"General procedure describes verification documentation.","DISTRACTOR"),
        )
        cases.append(Case(cid,"SCOPE_CONFLICT",parent,(ca,cb),candidates))

    # 6. FORM_CONFLICT: same entity/topic, wrong form describes requirement rather than observed state.
    forms = [
        ("Valve 52","event_record","authoritative_declaration"),
        ("Unit 54","registry_entry","authoritative_declaration"),
        ("Channel 56","measurement","authoritative_declaration"),
        ("Rack 58","authoritative_declaration","event_record"),
    ]
    for idx,(subj,good_form,bad_form) in enumerate(forms, start=1):
        cid=f"FORM-{idx:02d}"
        a=f"{cid}-A"; b=f"{cid}-B"
        if good_form=="event_record":
            parent=f"{subj} closure event was logged and its witness event was logged."
            at=f"{subj} closure event was logged."
            bt=f"{subj} witness event was logged."
            good_a=f"Event log recorded that {subj} closure event occurred."
            good_b=f"Witness record logged the witness event for {subj}."
            wrong_a=f"Policy requires {subj} closure events to be logged."
            wrong_b=f"Manual states that witness events for {subj} must be logged."
        elif good_form=="registry_entry":
            parent=f"{subj} is registered as active and its release certificate is registered."
            at=f"{subj} is registered as active."
            bt=f"{subj} release certificate is registered."
            good_a=f"Registry entry lists {subj} with active status."
            good_b=f"Certificate registry lists the release certificate for {subj}."
            wrong_a=f"Policy requires {subj} to be registered as active."
            wrong_b=f"Manual requires release certificates for {subj} to be registered."
        elif good_form=="measurement":
            parent=f"{subj} measured below 3.3 bar and its verification reading measured below 3.3 bar."
            at=f"{subj} measured below 3.3 bar."
            bt=f"{subj} verification reading measured below 3.3 bar."
            good_a=f"Measurement record: {subj} gauge reading measured 3.1 bar."
            good_b=f"Sensor reading for {subj} verification measured 3.2 bar."
            wrong_a=f"Specification requires {subj} to remain below 3.3 bar."
            wrong_b=f"Procedure states that {subj} verification should be below 3.3 bar."
        else:
            parent=f"{subj} procedure requires dual sign-off and its manual requires identity verification."
            at=f"{subj} procedure requires dual sign-off."
            bt=f"{subj} manual requires identity verification."
            good_a=f"Procedure states that {subj} requires dual sign-off."
            good_b=f"Manual states that {subj} requires identity verification."
            wrong_a=f"Event log recorded a dual sign-off for {subj} in one run."
            wrong_b=f"Audit trail recorded an identity verification event for {subj}."
        ca=child(a,at,inherited_subject=None,wrong_subject=None,wrong_scope=None,expected_form=good_form,wrong_form=bad_form)
        cb=child(b,bt,inherited_subject=None,wrong_subject=None,wrong_scope=None,expected_form=good_form,wrong_form=bad_form)
        candidates=(
            c(f"{cid}-01",good_a,"REQUIRED",a),
            c(f"{cid}-02",wrong_a,"UNSAFE_OR_MISLEADING"),
            c(f"{cid}-03",good_b,"REQUIRED",b),
            c(f"{cid}-04",wrong_b,"UNSAFE_OR_MISLEADING"),
            c(f"{cid}-05",f"General note mentions {subj} but not the relevant evidentiary state.","DISTRACTOR"),
            c(f"{cid}-06",f"Training material discusses evidence handling for {subj}.","DISTRACTOR"),
            c(f"{cid}-07",f"Administrative record lists {subj} without resolving either child.","DISTRACTOR"),
            c(f"{cid}-08",f"Support document repeats terminology from {subj} controls.","DISTRACTOR"),
            c(f"{cid}-09",f"Historical note concerns a different control cycle for {subj}.","DISTRACTOR"),
            c(f"{cid}-10",f"Overview document summarizes the system without direct evidence.","DISTRACTOR"),
        )
        cases.append(Case(cid,"FORM_CONFLICT",parent,(ca,cb),candidates))

    if len(cases) != 24:
        raise RuntimeError(f"expected 24 cases, got {len(cases)}")
    return cases


def load_model() -> tuple[Any, Any]:
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION,trust_remote_code=False)
    model=AutoModelForSequenceClassification.from_pretrained(MODEL,revision=REVISION,trust_remote_code=False)
    model.eval()
    return tokenizer,model


def semantic_score(tokenizer: Any, model: Any, claim: str, passage: str) -> float:
    encoded=tokenizer(claim,passage,return_tensors="pt",truncation=True,max_length=512)
    with torch.no_grad():
        logits=model(**encoded).logits
    if logits.shape[-1] != 1:
        raise RuntimeError(f"expected one reranker logit, got {tuple(logits.shape)}")
    return float(torch.sigmoid(logits[0,0]).item())


def form_of(text: str) -> set[str]:
    out=set()
    if EVENT_RE.search(text):
        out.add("event_record")
    if REGISTRY_RE.search(text):
        out.add("registry_entry")
    if DECL_RE.search(text):
        out.add("authoritative_declaration")
    if MEAS_RE.search(text):
        out.add("measurement")
    if not out:
        out.add("document_text")
    return out


def exact_contains(value: str | None, text: str) -> int:
    if not value:
        return 0
    return int(value.lower() in text.lower())


def predicate_match(terms: tuple[str, ...], text: str) -> float:
    if not terms:
        return 0.0
    observed={x.lower() for x in WORD_RE.findall(text)}
    return len(set(terms)&observed)/len(set(terms))


def descriptor_score(candidate: dict[str, Any], child: Child, field: str, *, wrong: bool=False) -> float:
    text=str(candidate["text"])
    if field=="subject":
        target=child.wrong_subject if wrong else (child.subject or child.inherited_subject)
        return float(exact_contains(target,text))
    if field=="scope":
        target=child.wrong_scope if wrong else child.scope
        return float(exact_contains(target,text))
    if field=="form":
        target=child.wrong_form if wrong else child.expected_form
        return float(target in form_of(text))
    if field=="predicate":
        return predicate_match(child.predicate_terms,text)
    if field=="full":
        values=[
            descriptor_score(candidate,child,"subject",wrong=False),
            descriptor_score(candidate,child,"scope",wrong=False),
            descriptor_score(candidate,child,"form",wrong=False),
            descriptor_score(candidate,child,"predicate",wrong=False),
        ]
        applicable=[]
        if child.subject or child.inherited_subject:
            applicable.append(values[0])
        if child.scope:
            applicable.append(values[1])
        applicable.append(values[2])
        applicable.append(values[3])
        return sum(applicable)/len(applicable) if applicable else 0.0
    raise ValueError(field)


def semantic_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows,key=lambda r:(-float(r["best_score"]),str(r["candidate_id"])))


def coverage_repair(rows: list[dict[str, Any]], selected: list[dict[str, Any]], cap: float) -> list[dict[str, Any]]:
    child_counts={}
    for row in selected:
        child_counts[row["best_child"]]=child_counts.get(row["best_child"],0)+1
    all_children=sorted({str(x) for row in rows for x in row["child_scores"]})
    missing=[x for x in all_children if child_counts.get(x,0)==0]
    if not missing:
        return semantic_order(selected)
    if len(missing)!=1:
        return semantic_order(selected)
    missing_child=missing[0]
    outside=[r for r in rows if r not in selected and r["best_child"]==missing_child]
    if not outside:
        return semantic_order(selected)
    challenger=max(outside,key=lambda r:(float(r["best_score"]),str(r["candidate_id"])))
    victims=[
        r for r in selected
        if child_counts.get(r["best_child"],0)>1
    ]
    if not victims:
        return semantic_order(selected)
    victim=min(victims,key=lambda r:(float(r["best_score"]),str(r["candidate_id"])))
    loss=float(victim["best_score"])-float(challenger["best_score"])
    if loss <= cap+1e-12:
        return semantic_order([r for r in selected if r is not victim]+[challenger])
    return semantic_order(selected)


def descriptor_repair(
    rows: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    case: Case,
    cap: float,
    field: str,
    *,
    wrong: bool=False,
) -> list[dict[str, Any]]:
    current=list(selected)
    child_by_id={x.child_id:x for x in case.children}
    for child_id in [x.child_id for x in case.children]:
        child_obj=child_by_id[child_id]
        owned=[r for r in current if r["best_child"]==child_id]
        outside=[r for r in rows if r not in current and r["best_child"]==child_id]
        if not owned or not outside:
            continue
        victim=min(
            owned,
            key=lambda r:(
                descriptor_score(r,child_obj,field,wrong=wrong),
                float(r["best_score"]),
                str(r["candidate_id"]),
            ),
        )
        challenger=max(
            outside,
            key=lambda r:(
                descriptor_score(r,child_obj,field,wrong=wrong),
                float(r["best_score"]),
                str(r["candidate_id"]),
            ),
        )
        v=descriptor_score(victim,child_obj,field,wrong=wrong)
        q=descriptor_score(challenger,child_obj,field,wrong=wrong)
        loss=float(victim["best_score"])-float(challenger["best_score"])
        if q>v+1e-12 and loss<=cap+1e-12:
            trial=[r for r in current if r is not victim]+[challenger]
            represented={r["best_child"] for r in trial}
            if all(x.child_id in represented for x in case.children):
                current=semantic_order(trial)
    return semantic_order(current)


def select_arms(scored: list[dict[str, Any]], case: Case, cap: float) -> dict[str,list[str]]:
    ordered=semantic_order(scored)
    semantic=ordered[:BUDGET]
    coverage=coverage_repair(ordered,semantic,cap)
    arms={
        "semantic_top3":semantic,
        "child_coverage":coverage,
        "child_coverage_plus_subject":descriptor_repair(ordered,coverage,case,cap,"subject"),
        "child_coverage_plus_wrong_subject":descriptor_repair(ordered,coverage,case,cap,"subject",wrong=True),
        "child_coverage_plus_scope":descriptor_repair(ordered,coverage,case,cap,"scope"),
        "child_coverage_plus_wrong_scope":descriptor_repair(ordered,coverage,case,cap,"scope",wrong=True),
        "child_coverage_plus_form":descriptor_repair(ordered,coverage,case,cap,"form"),
        "child_coverage_plus_wrong_form":descriptor_repair(ordered,coverage,case,cap,"form",wrong=True),
        "child_coverage_plus_full_obligation":descriptor_repair(ordered,coverage,case,cap,"full"),
        "child_coverage_plus_predicate_lexical_control":descriptor_repair(ordered,coverage,case,cap,"predicate"),
    }
    return {k:[str(x["candidate_id"]) for x in v] for k,v in arms.items()}


def score_cases(cases: list[Case]) -> dict[str,Any]:
    tokenizer,model=load_model()
    out=[]
    for case in cases:
        rows=[]
        for cand in case.candidates:
            child_scores={
                ch.child_id:semantic_score(tokenizer,model,ch.text,cand.text)
                for ch in case.children
            }
            best_child=max(child_scores,key=lambda x:(child_scores[x],x))
            rows.append({
                "candidate_id":cand.candidate_id,
                "text":cand.text,
                "gold_class":cand.gold_class,
                "required_for":list(cand.required_for),
                "child_scores":child_scores,
                "best_child":best_child,
                "best_score":child_scores[best_child],
                "forms":sorted(form_of(cand.text)),
            })
        cap_arms={f"{cap:.2f}":select_arms(rows,case,cap) for cap in CAPS}
        out.append({
            "case_id":case.case_id,
            "category":case.category,
            "parent_text":case.parent_text,
            "children":[{
                "child_id":ch.child_id,
                "text":ch.text,
                "subject":ch.subject,
                "inherited_subject":ch.inherited_subject,
                "scope":ch.scope,
                "wrong_subject":ch.wrong_subject,
                "wrong_scope":ch.wrong_scope,
                "expected_form":ch.expected_form,
                "wrong_form":ch.wrong_form,
                "predicate_terms":list(ch.predicate_terms),
            } for ch in case.children],
            "candidates":rows,
            "arms":cap_arms,
        })
    return {
        "schema":"eb-composite-obligation-targeted-stress-v1-selections",
        "classification":"EXPOSED_TARGETED_STRESS_NOT_FRESH_QUALIFICATION",
        "semantic_model":{"name":MODEL,"revision":REVISION},
        "budget":BUDGET,
        "caps":list(CAPS),
        "case_count":len(out),
        "cases":out,
    }


def evaluate(payload: dict[str,Any]) -> dict[str,Any]:
    per_case=[]
    for case in payload["cases"]:
        by_id={r["candidate_id"]:r for r in case["candidates"]}
        child_ids=[x["child_id"] for x in case["children"]]
        caps={}
        for cap,arms in case["arms"].items():
            arm_eval={}
            for arm,ids in arms.items():
                selected=[by_id[x] for x in ids]
                required_covered=set()
                for row in selected:
                    required_covered.update(row["required_for"])
                arm_eval[arm]={
                    "selected_ids":ids,
                    "required_children_covered":len(required_covered),
                    "complete_parent_coverage":set(child_ids)<=required_covered,
                    "unsafe":sum(r["gold_class"]=="UNSAFE_OR_MISLEADING" for r in selected),
                    "non_useful":sum(r["gold_class"] not in {"REQUIRED","REDUNDANT"} for r in selected),
                    "required_selected":sum(r["gold_class"]=="REQUIRED" for r in selected),
                    "semantic_child_coverage":len({r["best_child"] for r in selected}),
                }
            caps[cap]=arm_eval
        per_case.append({
            "case_id":case["case_id"],
            "category":case["category"],
            "caps":caps,
        })

    categories=sorted({x["category"] for x in per_case})
    arms=sorted(next(iter(next(iter(x["caps"].values())).keys())) for x in []) if False else [
        "semantic_top3",
        "child_coverage",
        "child_coverage_plus_subject",
        "child_coverage_plus_wrong_subject",
        "child_coverage_plus_scope",
        "child_coverage_plus_wrong_scope",
        "child_coverage_plus_form",
        "child_coverage_plus_wrong_form",
        "child_coverage_plus_full_obligation",
        "child_coverage_plus_predicate_lexical_control",
    ]
    summaries={}
    for cap in [f"{x:.2f}" for x in CAPS]:
        summaries[cap]={}
        for category in categories+["ALL"]:
            subset=[x for x in per_case if category=="ALL" or x["category"]==category]
            summaries[cap][category]={}
            for arm in arms:
                rows=[x["caps"][cap][arm] for x in subset]
                summaries[cap][category][arm]={
                    "parents":len(rows),
                    "complete_parent_coverage":sum(bool(r["complete_parent_coverage"]) for r in rows),
                    "required_children_covered":sum(int(r["required_children_covered"]) for r in rows),
                    "required_children_total":2*len(rows),
                    "unsafe":sum(int(r["unsafe"]) for r in rows),
                    "non_useful":sum(int(r["non_useful"]) for r in rows),
                    "required_selected":sum(int(r["required_selected"]) for r in rows),
                    "semantic_child_coverage_total":sum(int(r["semantic_child_coverage"]) for r in rows),
                }

    def cat(cap:str,category:str,arm:str)->dict[str,Any]:
        return summaries[cap][category][arm]

    q1=[]
    for cap in [f"{x:.2f}" for x in CAPS]:
        star_base=cat(cap,"STARVATION","semantic_top3")
        star_cov=cat(cap,"STARVATION","child_coverage")
        ctrl_base=cat(cap,"NO_STARVATION_CONTROL","semantic_top3")
        ctrl_cov=cat(cap,"NO_STARVATION_CONTROL","child_coverage")
        q1.append({
            "cap":float(cap),
            "starvation_complete_delta":star_cov["complete_parent_coverage"]-star_base["complete_parent_coverage"],
            "starvation_required_child_delta":star_cov["required_children_covered"]-star_base["required_children_covered"],
            "starvation_unsafe_delta":star_cov["unsafe"]-star_base["unsafe"],
            "control_complete_delta":ctrl_cov["complete_parent_coverage"]-ctrl_base["complete_parent_coverage"],
            "control_required_child_delta":ctrl_cov["required_children_covered"]-ctrl_base["required_children_covered"],
            "control_unsafe_delta":ctrl_cov["unsafe"]-ctrl_base["unsafe"],
        })

    q2={}
    for field,correct,wrong,cats in [
        ("subject","child_coverage_plus_subject","child_coverage_plus_wrong_subject",["EXPLICIT_SUBJECT_CONFLICT","INHERITED_SUBJECT_CONFLICT"]),
        ("scope","child_coverage_plus_scope","child_coverage_plus_wrong_scope",["SCOPE_CONFLICT"]),
        ("form","child_coverage_plus_form","child_coverage_plus_wrong_form",["FORM_CONFLICT"]),
    ]:
        rows=[]
        for cap in [f"{x:.2f}" for x in CAPS]:
            for category in cats:
                base=cat(cap,category,"child_coverage")
                cor=cat(cap,category,correct)
                bad=cat(cap,category,wrong)
                rows.append({
                    "cap":float(cap),
                    "category":category,
                    "correct_complete_delta":cor["complete_parent_coverage"]-base["complete_parent_coverage"],
                    "correct_required_child_delta":cor["required_children_covered"]-base["required_children_covered"],
                    "correct_unsafe_delta":cor["unsafe"]-base["unsafe"],
                    "wrong_complete_delta":bad["complete_parent_coverage"]-base["complete_parent_coverage"],
                    "wrong_required_child_delta":bad["required_children_covered"]-base["required_children_covered"],
                    "wrong_unsafe_delta":bad["unsafe"]-base["unsafe"],
                    "correct_vs_wrong_complete":cor["complete_parent_coverage"]-bad["complete_parent_coverage"],
                    "correct_vs_wrong_required_child":cor["required_children_covered"]-bad["required_children_covered"],
                    "correct_vs_wrong_unsafe":cor["unsafe"]-bad["unsafe"],
                })
        q2[field]=rows

    result={
        "schema":"eb-composite-obligation-targeted-stress-v1-evaluation",
        "classification":"EXPOSED_TARGETED_STRESS_NOT_FRESH_QUALIFICATION",
        "selection_sha256":sha256_json(payload),
        "summaries":summaries,
        "q1_child_coverage":q1,
        "q2_descriptors":q2,
        "per_case":per_case,
        "nonclaims":[
            "fixture author knew the prior development result",
            "this is not independent or context-free qualification",
            "a targeted positive result shows mechanism capability under adversarial ambiguity, not prevalence",
            "a targeted null result is stronger evidence against the specific descriptor mechanism on the tested ambiguity",
        ],
    }
    result["evaluation_sha256"]=sha256_json(result)
    return result


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--selection-out",required=True)
    parser.add_argument("--evaluation-out",required=True)
    args=parser.parse_args()
    cases=build_cases()
    selections=score_cases(cases)
    Path(args.selection_out).write_text(json.dumps(selections,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    evaluation=evaluate(selections)
    Path(args.evaluation_out).write_text(json.dumps(evaluation,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "selection_sha256":sha256_json(selections),
        "evaluation_sha256":evaluation["evaluation_sha256"],
        "q1":evaluation["q1_child_coverage"],
        "q2":evaluation["q2_descriptors"],
    },indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
