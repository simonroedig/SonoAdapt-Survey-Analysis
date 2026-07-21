import pandas as pd
import statsmodels.formula.api as smf
from analysis import load_and_filter_data, transform_to_long_format
import warnings
warnings.filterwarnings('ignore')

def main():
    df, _ = load_and_filter_data('data.xlsx', 'listOfManuallyIdentifiedOutliers.txt')
    model_data = transform_to_long_format(df).dropna(subset=['Disruption', 'Social_Acceptability', 'Detectability', 'Appropriateness', 'ResponseId'])

    f = "Disruption ~ C(Notification_Type) + C(Asocial, Treatment(reference='Interactive')) + C(e_Task, Treatment(reference='Low')) + C(CM, Treatment(reference='Quiet'))"
    m = smf.mixedlm(f, data=model_data, groups=model_data['ResponseId']).fit(reml=False)
    print('\n=== DISRUPTION P-VALUES ===')
    print(m.pvalues)

    f = "Social_Acceptability ~ C(Notification_Type) + C(Asocial, Treatment(reference='Interactive')) + C(e_Task, Treatment(reference='Low')) + C(CM, Treatment(reference='Quiet'))"
    m = smf.mixedlm(f, data=model_data, groups=model_data['ResponseId']).fit(reml=False)
    print('\n=== SOCIAL ACCEPTABILITY P-VALUES ===')
    print(m.pvalues)

    f = "Detectability ~ C(Notification_Type) + C(Asocial, Treatment(reference='Interactive')) + C(e_Task, Treatment(reference='Low')) + C(CM, Treatment(reference='Quiet'))"
    m = smf.mixedlm(f, data=model_data, groups=model_data['ResponseId']).fit(reml=False)
    print('\n=== DETECTABILITY P-VALUES ===')
    print(m.pvalues)

if __name__ == '__main__':
    main()
