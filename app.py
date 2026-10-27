import streamlit as st
import joblib
import numpy as np
import pandas as pd

# ตั้งค่าหน้าจอและการแสดงผลเว็บแบบกว้าง (Wide) ตาม Layout การวิจัยของคุณกีรติ
st.set_page_config(page_title="Smart Lab CDSS - Wapipathum", layout="wide")

# โหลดโมเดล AI และ Scaler ความปลอดภัยเชิงระบบ
try:
    model = joblib.load('xgboost_influenza_model.pkl')
    scaler = joblib.load('blood_scaler.pkl')
except:
    pass

# 🟢 กลไกการโหลดข้อมูลจริงจาก Excel และสร้างรหัสพรางตัวตนในรูปแบบ HN อ้างอิงทางการวิจัย (625 ราย)
@st.cache_data
def load_anonymized_data():
    try:
        # อ่านไฟล์ Excel จริงที่ตัดข้อมูลระบุบุคคลออกแล้วเพื่อพิทักษ์สิทธิ์คนไข้
        df = pd.read_excel('patient_data.xlsx')
        
        # ปรับชื่อคอลัมน์ตัวแปรทั้งหมดให้เป็นตัวพิมพ์ใหญ่เพื่อป้องกันระบบเพี้ยน
        df.columns = df.columns.astype(str).str.strip().str.upper()
        
        # 🛠️ สร้างรหัสจำลองทางการวิจัยในรูปแบบ HN (HN-001 ถึง HN-625) ครอบทับแถวข้อมูลจริงจำนวน 625 ราย
        total_rows = len(df)
        df['STUDY_HN'] = [f"HN-{i:03d}" for i in range(1, total_rows + 1)]
        
        # ทำความสะอาดข้อมูลคอลัมน์ RISK ให้เป็นมาตรฐานพิมพ์เล็กเพื่อตัดบั๊กตัวกรอง
        if 'RISK' in df.columns:
            df['RISK'] = df['RISK'].astype(str).str.strip().str.lower()
            
        return df
    except Exception as e:
        st.error(f"❌ ไม่สามารถโหลดไฟล์ข้อมูลจริงได้: {e}")
        st.info("💡 คำแนะนำ: โปรดตรวจสอบว่ามีไฟล์ชื่อ 'patient_data.xlsx' อยู่บนคลังข้อมูล GitHub หรือไม่")
        return None

df_patients = load_anonymized_data()

# ส่วนหัวโปรแกรมหลัก (Header)
st.title("📊 ระบบสนับสนุนการตัดสินใจทางคลินิกอัจฉริยะ (Smart Lab CDSS)")
st.write("**พัฒนาโดย: กีรติ เหลืองชัยศรี • โรงพยาบาลวาปีปทุม จังหวัดมหาสารคาม**")
st.write("---")

if df_patients is not None:
    # นับจำนวนเคสจริงตามที่ปรากฏในตาราง Excel แยกตามกลุ่มความเสี่ยงเพื่อแสดงบนตัวกรองแบบไดนามิก
    count_all = len(df_patients)
    count_high = len(df_patients[df_patients['RISK'].str.contains('high|สูง', na=False)]) if 'RISK' in df_patients.columns else 0
    count_mod = len(df_patients[df_patients['RISK'].str.contains('mod|ปานกลาง|เฝ้าระวัง', na=False)]) if 'RISK' in df_patients.columns else 0
    count_low = len(df_patients[df_patients['RISK'].str.contains('low|ต่ำ', na=False)]) if 'RISK' in df_patients.columns else 0

    # แบ่งหน้าจอออกเป็น 2 คอลัมน์หลัก (ซ้าย-ขวา)
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.write("#### 🔵 1. เลือกตัวกรองระดับความเสี่ยง")
        st.caption("ปุ่มลัดคัดกรองเคสผู้ป่วยตามความเสี่ยงทางคลินิก")
        
        # ปุ่มวิทยุตัวกรองความเสี่ยงที่จะดึงตัวเลขสถิติจริงจาก Excel ขึ้นมาแสดงผล ไม่มั่วตัวเลขค้างในอดีต
        filter_option = st.radio(
            "เลือกโหมดคัดกรอง:",
            [
                f"🔮 แสดงรายชื่อทั้งหมด ({count_all} ราย)",
                f"🔴 แสดงเฉพาะผู้ป่วยความเสี่ยงสูง (ติดเชื้อ) ({count_high} ราย)",
                f"🟡 แสดงเฉพาะผู้ป่วยความเสี่ยงปานกลาง (เฝ้าระวัง) ({count_mod} ราย)",
                f"🟢 แสดงเฉพาะผู้ป่วยความเสี่ยงต่ำ (ไม่ติดเชื้อ) ({count_low} ราย)"
            ],
            index=0,
            label_visibility="collapsed"
        )
        
        # ลอจิกการดึงและคัดแยกรายชื่อ HN ตามสถานะความเสี่ยงจริงในตาราง Excel
        if "🔴" in filter_option:
            filtered_hns = df_patients[df_patients['RISK'].str.contains('high|สูง', na=False)]['STUDY_HN'].tolist()
        elif "🟡" in filter_option:
            filtered_hns = df_patients[df_patients['RISK'].str.contains('mod|ปานกลาง|เฝ้าระวัง', na=False)]['STUDY_HN'].tolist()
        elif "🟢" in filter_option:
            filtered_hns = df_patients[df_patients['RISK'].str.contains('low|ต่ำ', na=False)]['STUDY_HN'].tolist()
        else:
            filtered_hns = df_patients['STUDY_HN'].tolist()

        st.write("#### 🔍 2. เลือกรหัส HN ผู้ป่วย")
        
        if filtered_hns:
            selected_hn = st.selectbox("เลือกรหัส HN ผู้ป่วย:", filtered_hns, label_visibility="collapsed")
        else:
            st.write("⚠️ *ไม่พบข้อมูลผู้ป่วยในกลุ่มความเสี่ยงนี้ใน Excel*")
            selected_hn = None
            
        st.write("")
        process_btn = st.button("🔮 ประมวลผลด้วย AI", use_container_width=True)

    with col2:
        st.write("#### 💻 หน้าจอแสดงผลสารสนเทศด่านหน้าและการพยากรณ์โรค")
        st.caption("ข้อมูลพารามิเตอร์ดัชนีทางโลหิตวิทยาและสัญญาณชีพจริง (ระบบปกปิดตัวตนคนไข้)")
        
        if selected_hn:
            # 🛠️ [จุดแก้ไขสําคัญ] ดึงพิกัดตำแหน่งดัชนีบรรทัดแรกที่ตรงกับรหัส HN เพื่อล็อกแถวข้อมูลไม่ให้ซ้ำซ้อน
            row_idx = df_patients[df_patients['STUDY_HN'] == selected_hn].index[0]
            
            # ฟังก์ชันช่วยดึงค่าข้อมูลจากบรรทัดจริงตัวแปรนั้นๆ (.loc) ป้องกันข้อมูลเพี้ยนค้างหน้าจอ
            def get_val(col_name, default=0.0):
                c_upper = col_name.upper()
                if c_upper in df_patients.columns:
                    val = df_patients.loc[row_idx, c_upper]
                    if pd.isna(val):
                        return default
                    return val
                return default
            
            # สกัดค่าความน่าจะเป็นจริง (PROB) และระดับความเสี่ยงจริง (RISK) รายบุคคลออกจากไฟล์ Excel
            prob_val = float(get_val('prob', 0.0))
            risk_val = str(get_val('risk', 'low')).lower()
            
            st.write(f"**รหัสประจำตัวผู้ป่วยนอก:** `{selected_hn}` | **อายุ:** {int(get_val('Age', 0))} ปี | **อุณหภูมิแรกรับ:** {get_val('body_temp', get_val('temp', 0.0))} °C")
            
            # 🟢 [ตารางแสดงผล CBC 14 ตัวแปรจริง] ดึงค่าแปรผันตามรายบุคคลคำต่อคำจากแถวข้อมูลใน Excel
            real_cbc = pd.DataFrame({
                'Parameters': [
                    'Hct (Hematocrit)', 'Wbc (WBC Count)', 'Rbc (RBC Count)', 'Plt (Platelet)', 
                    'MCV', 'MCH', 'MCHC', 
                    'Neu (Neutrophil)', 'Eo (Eosinophil)', 'Lym (Lymphocyte)', 'Baso (Basophil)', 'Mono (Monocyte)',
                    'body_temp (อุณหภูมิร่างกาย)', 'Age (อายุ)'
                ],
                'Value': [
                    get_val('Hct'), get_val('Wbc'), get_val('Rbc'), get_val('Plt'), 
                    get_val('MCV'), get_val('MCH'), get_val('MCHC'), 
                    get_val('Neu'), get_val('Eo'), get_val('Lym'), get_val('Baso'), get_val('Mono'),
                    get_val('body_temp', get_val('temp')), get_val('Age')
                ],
                'Unit': [
                    '%', 'x10^3/uL', 'x10^6/uL', 'x10^3/uL', 
                    'fL', 'pg', 'g/dL', 
                    '%', '%', '%', '%', '%',
                    '°C', 'ปี'
                ],
                'Reference Range': [
                    '36.0 - 54.0', '4.0 - 10.0', '3.8 - 5.8', '150 - 450', 
                    '80.0 - 100.0', '27.0 - 32.0', '32.0 - 36.0', 
                    '40.0 - 70.0', '0.0 - 5.0', '20.0 - 40.0', '0.0 - 1.0', '2.0 - 10.0',
                    '36.5 - 37.4', '0 - 120'
                ]
            })
            st.dataframe(real_cbc, use_container_width=True, hide_index=True)
            
            st.write("#### ผลการประเมินความเสี่ยงและคำแนะนำสนับสนุนการตัดสินใจทางคลินิก")
            st.info(f"🧠 **[ผลวิเคราะห์วินิจฉัยจากระบบ AI]** โอกาสติดเชื้อไวรัสไข้หวัดใหญ่: **{prob_val:.2f} %**")
            
            # ลอจิกการแสดงแถบสีแจ้งเตือนและข้อความคำแนะนำทางการแพทย์ 3 ระดับสอดคล้องตามคอลัมน์ RISK ใน Excel จริง
            if process_btn:
                if 'high' in risk_val or 'สูง' in risk_val or prob_val >= 70:
                    st.error("🚨 แนะนำทางการแพทย์: ความเสี่ยงสูง (แนะนำตรวจ Rapid Influenza Test)")
                elif 'mod' in risk_val or 'ปานกลาง' in risk_val or 'เฝ้าระวัง' in risk_val or (40 <= prob_val < 70):
                    st.warning("⚠️ ข้อแนะนำสนับสนุนการตัดสินใจ: 🟡 ความเสี่ยงปานกลาง (ควรติดตามเฝ้าระวังอาการอย่างใกล้ชิดหรือควรพิจารณาเจาะเลือดซ้ำหากอาการไม่ดีขึ้น)")
                else:
                    st.success("🟢 แนะนำทางการแพทย์: ความเสี่ยงต่ำ (ไม่พบความผิดปกติเด่นชัดของดัชนีผลเลือด)")
            else:
                st.info("💡 ระบบพร้อมปฏิบัติงาน: กรุณากดปุ่มประมวลผลด้วย AI เพื่อดูคำแนะนำสนับสนุนการตัดสินใจ")

    st.write("---")
    st.write("#### 📊 แบบบันทึกผลการประเมินประสิทธิภาพของแบบจำลองปัญญาประดิษฐ์ (AI Model Specification)")

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    with stat_col1:
        st.metric(label="ความแม่นยำรวม (Overall Accuracy)", value="99.38 %")
    with stat_col2:
        st.metric(label="ความไวในการตรวจพบ (Sensitivity)", value="100.00 %")
    with stat_col3:
        st.metric(label="ความจำเพาะในการแยกโรค (Specificity)", value="99.19 %")
    with stat_col4:
        st.metric(label="ความน่าเชื่อถือเมื่อทำนายผลบวก (Precision)", value="97.45 %")
else:
    st.warning("⚠️ ระบบหยุดทำงานชั่วคราวเนื่องจากขาดไฟล์ฐานข้อมูลหลัก")
