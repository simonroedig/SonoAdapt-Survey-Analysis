data.xlsx
-> The FULL dataset from Qualtrics. We then remove the outliers, and all rows previous of 30 June (those were all test runs) in the python files


app.py
-> This is simply the Dashboard (streamlit)
(https://sonoadapt-survey-analysis-5ksagofflradkiwemckaun.streamlit.app/)

analysis.py
-> Main analysis:
Berechnet die deskriptiven Statistiken (Mittelwert und Standardabweichung) für jede Kombination aus Szenario und Notification Type. Speichert diese ab (descriptive_statistics.csv).
Danach rechnet es die vier LMMs aus und printet Summaries in die Konsole (also p-values, beta coefficients usw).
Terminal print wird auch in mainAnalysis.txt gespeichert.

mainBoxPlotsALL.py
-> Created the main effect plots found in /plots (in MA those are the plots a)

mainBoxPlotsALL2.py
-> Created the additional plots in /plots2 (in MA those are the plots b,c,d,e)


WIP:
pereference.py
-> Further analysis of preference and timing of users
intraUserVariance.py
-> Also further analyis to see if people change the type and and not just stick to one


