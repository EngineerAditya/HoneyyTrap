from decision_maker.decision_engine import DecisionMaker

_dm = DecisionMaker()

def run_decision(analysis_json: dict, session_id: str):
    return _dm.run(analysis_json, session_id)