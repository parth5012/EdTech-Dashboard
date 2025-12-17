from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List

# from datetime import date,datetime
from utils.llms import (
    get_ats_score,
    get_job_details,
    get_achievements,
    get_readiness_score,
    get_str_output,
)


class JobDetails(TypedDict):
    title: str
    company: str


class ATS(TypedDict):
    match_score: float
    summary: str
    matched_skills: List[str]
    missing_skills: List[str]


class Candidate(TypedDict):
    certifications: List[str]
    issuing_authority: List[str]
    date_earned: List[str]
    platform_link: List[str]


class DashboardState(TypedDict):
    resume_text: str
    job_desc: str
    job_details: JobDetails
    candidate_details: Candidate
    analysis_quote: List[str]
    readiness_score: float
    ats: ATS


def ats(state: DashboardState):
    content = state["resume_text"]
    desc = state["job_desc"]
    ats = get_ats_score(content, job_desc=desc)
    return {"ats": ats}


def job_details(state: DashboardState):
    desc = state["job_desc"]
    details = get_job_details(desc)
    return {"job_details": details}


def candidate_details(state: DashboardState):
    content = state["resume_text"]
    details = get_achievements(content)
    return {"candidate_details": details}


def quote(state: DashboardState):
    content = state["resume_text"]
    quotes = get_str_output(content)
    return {"analysis_quote": quotes}


def readiness_score(state: DashboardState):
    content = state["resume_text"]
    score = get_readiness_score(content)
    return {"readiness_score": score}

def get_dashboard_workflow():
    graph = StateGraph(DashboardState)

    graph.add_node("ats", ats)
    graph.add_node("quote", quote)
    graph.add_node("readiness_score", readiness_score)
    graph.add_node("job_details", job_details)
    graph.add_node("candidate_details", candidate_details)

    graph.add_edge(START, "ats")
    graph.add_edge(START, "quote")
    graph.add_edge(START, "readiness_score")
    graph.add_edge(START, "job_details")
    graph.add_edge(START, "candidate_details")
    graph.add_edge("ats", END)
    graph.add_edge("quote", END)
    graph.add_edge("readiness_score", END)
    graph.add_edge("job_details", END)
    graph.add_edge("candidate_details", END)

    return graph.compile()
