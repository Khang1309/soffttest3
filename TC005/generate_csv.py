import pandas as pd
import math

df = pd.read_excel('TC-005_converted.xlsx')
test_cases = df['Test Case'].unique()

data = []
for tc in test_cases:
    if str(tc) == 'nan' or tc == 'TC-005-000':
        continue
    
    tc_df = df[df['Test Case'] == tc]
    
    q_name = ""
    q_text = ""
    def_mark = ""
    id_num = ""
    expected = ""
    flow_type = "normal"
    
    for _, row in tc_df.iterrows():
        cmd = str(row['Command']).strip()
        tgt = str(row['Target']).strip()
        val = str(row['Value'])
        if val == 'nan': val = ""
        
        if cmd == 'type' and tgt == 'id=id_name':
            q_name = val
        elif cmd == 'editContent' and tgt == 'id=tinymce':
            q_text = val.replace("Katalon Recorder is recording...Stop", "").strip()
        elif cmd == 'type' and tgt == 'id=id_defaultmark':
            def_mark = val
        elif cmd == 'type' and tgt == 'id=id_idnumber':
            id_num = val
        elif cmd == 'verifyText':
            expected = val
            if 'id_error' in tgt:
                flow_type = "error_msg"
                
    if not expected:
        continue
        
    data.append({
        'TC_ID': tc,
        'QuestionName': q_name,
        'QuestionText': q_text,
        'DefaultMark': def_mark,
        'IDNumber': id_num,
        'ExpectedResult': expected,
        'FlowType': flow_type
    })

out_df = pd.DataFrame(data)
out_df.to_csv('test_data_level1.csv', index=False)

# For level 2, append the performance test
data.append({
    'TC_ID': 'TC-NFT-001',
    'QuestionName': 'Performance Question',
    'QuestionText': 'This is to test the performance',
    'DefaultMark': '1',
    'IDNumber': '',
    'ExpectedResult': '15',
    'FlowType': 'performance'
})
pd.DataFrame(data).to_csv('test_data_level2.csv', index=False)
print("Extracted", len(out_df), "test cases.")
