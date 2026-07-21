import pandas as pd
import statsmodels.formula.api as smf
from analysis import load_and_filter_data, transform_to_long_format
import warnings
warnings.filterwarnings('ignore')

def main():
    df, _ = load_and_filter_data('data.xlsx', 'listOfManuallyIdentifiedOutliers.txt')
    model_data = transform_to_long_format(df).dropna(subset=['Disruption', 'Social_Acceptability', 'Detectability', 'Appropriateness', 'ResponseId'])

    for dv in ['Disruption', 'Social_Acceptability', 'Detectability']:
        f = f"{dv} ~ C(Notification_Type, Treatment(reference='Short Speech')) + C(Asocial) + C(e_Task) + C(CM)"
        m = smf.mixedlm(f, data=model_data, groups=model_data['ResponseId']).fit(reml=False)
        p = m.pvalues["C(Notification_Type, Treatment(reference='Short Speech'))[T.Rich Speech]"]
        c = m.params["C(Notification_Type, Treatment(reference='Short Speech'))[T.Rich Speech]"]
        print(f"{dv}: Rich vs Short = {c:.3f} (p={p:.3e})")

if __name__ == '__main__':
    main()
