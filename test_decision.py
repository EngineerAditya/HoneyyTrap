from decision_maker.decision_engine import DecisionMaker

dm = DecisionMaker()

samples = [
    {
        "predicted_class": "impersonation",
        "confidence": 0.82,
        "entropy": 0.42,
        "ood_score": 0.2
    },
    {
        "predicted_class": "impersonation",
        "confidence": 0.79,
        "entropy": 0.40,
        "ood_score": 0.1
    },
    {
        "predicted_class": "loan_investment",
        "confidence": 0.75,
        "entropy": 0.48,
        "ood_score": 0.2
    }
]

for i, s in enumerate(samples):
    print(dm.run(s, "session_1"))