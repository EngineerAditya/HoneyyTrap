import pandas as pd

class ThemeDetector:
    def __init__(self, mapping_path="scam_intent_mapping.csv"):
        self.df = pd.read_csv(mapping_path)
        self.categories = self.df['scam_category'].unique().tolist()
        self.theme_map = {
            cat: self.df[self.df['scam_category'] == cat]['keyword'].str.lower().tolist() 
            for cat in self.categories
        }

    def detect(self, text):
        text = str(text).lower()
        counts = {cat: sum(1 for kw in kws if kw in text) for cat, kws in self.theme_map.items()}
        winner = max(counts, key=counts.get)
        return winner if counts[winner] > 0 else "GENERAL"