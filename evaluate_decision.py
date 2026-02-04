import pandas as pd
from decision_maker.decision_engine import DecisionMaker

dm = DecisionMaker("scam_intent_mapping.csv")

import pickle
with open("decision_maker.pkl", "wb") as f:
    pickle.dump(dm, f)

print("✅ Model saved as decision_maker.pkl")

# Load your decision dataset
df = pd.read_csv("decision_dataset.csv")

results = []
correct = 0

print("Evaluating 15k samples... (Columns: Verdict, Command, Progress)")

for i, row in df.iterrows():
    msg_text = row['text']
    ml_intent = row['intent']
    ground_truth = str(row['verdict']).lower() 
    
    sess_id = f"user_{i // 5}"
    res = dm.run(msg_text, ml_intent, sess_id)
    
    is_detected = (res['verdict'] == "SCAM")
    is_actually_scam = ground_truth in ['spam', 'scam', '1', 'other_scam']
    
    if is_detected == is_actually_scam:
        correct += 1
    
    results.append(res)

accuracy = (correct / len(df)) * 100

print("\n" + "="*40)
print(f"FINAL ACCURACY: {accuracy:.2f}%")
print("="*40 + "\n")

output_df = pd.DataFrame(results)
print("5 SAMPLE OUTPUTS:")
print(output_df[['verdict', 'command', ]].head(5))

output_df.to_csv("final_clean_report.csv", index=False)
print("\n✅ Clean report saved: final_clean_report.csv")

output_df.to_json("final_clean_report.json", orient="records", indent=4)
print("✅ JSON report saved: final_clean_report.json")