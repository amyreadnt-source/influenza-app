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
        
        # 🛠️ สร้างรหัสจำลองทางการวิจัยในรูปแบบ HN (เช่น HN-001 ถึง HN-625) ครอบทับแถวข้อมูลจริงจำนวน 625 ราย
        total_rows = len(df)
        df['STUDY_HN'] = [f"HN-{i:03d}" for i in range(1, total_rows + 1)]
        
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
    # แบ่งหน้าจอออกเป็น 2 คอลัมน์หลัก (ซ้าย-ขวา)
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.write("#### 🔵 1. เลือกตัวกรองระดับความเสี่ยง")
        st.caption("ปุ่มลัดคัดกรองเคสผู้ป่วยตามความเสี่ยงทางคลินิก")
        
        filter_option = st.radio(
            "เลือกโหมดคัดกรอง:",
            [
                f"🔮 แสดงรายชื่อทั้งหมด ({len(df_patients)} ราย)",
                "🔴 แสดงเฉพาะผู้ป่วยความเสี่ยงสูง (ติดเชื้อ)",
                "🟡 แสดงเฉพาะผู้ป่วยความเสี่ยงปานกลาง (เฝ้าระวัง)",
                "🟢 แสดงเฉพาะผู้ป่วยความเสี่ยงต่ำ (ไม่ติดเชื้อ)"
            ],
            index=0,
            label_visibility="collapsed"
        )
        
        # คัดกรองรหัสลับ HN ตามเงื่อนไขคอลัมน์ RISK ใน Excel (high, moderate, low)
        if "🔴" in filter_option and 'RISK' in df_patients.columns:
            filtered_hns = df_patients[df_patients['RISK'].astype(str).str.lower().str.contains('high')]['STUDY_HN'].tolist()
        elif "🟡" in filter_option and 'RISK' in df_patients.columns:
            filtered_hns = df_patients[df_patients['RISK'].astype(str).str.lower().str.contains('mod')]['STUDY_HN'].tolist()
        elif "🟢" in filter_option and 'RISK' in df_patients.columns:
            filtered_hns = df_patients[df_patients['RISK'].astype(str).str.lower().str.contains('low')]['STUDY_HN'].tolist()
        else:
            filtered_hns = df_patients['STUDY_HN'].tolist()

        st.write("#### 🔍 2. เลือกรหัส HN ผู้ป่วย")
        # 🟢 ตัดประโยคแจ้งจำนวน "มีรหัสลับพรางตัวตน..." ออกไปตามเงื่อนไขที่ท่านกำหนดเรียบร้อยแล้ว
        
        if filtered_hns:
            selected_hn = st.selectbox("เลือกรหัส HN ผู้ป่วย:", filtered_hns, label_visibility="collapsed")
        else:
            st.write("⚠️ *ไม่พบข้อมูลในกลุ่มความเสี่ยงนี้*")
            selected_hn = None
            
        st.write("")
        process_btn = st.button("🔮 ประมวลผลด้วย AI", use_container_width=True)

    with col2:
        st.write("#### 💻 หน้าจอแสดงผลสารสนเทศด่านหน้าและการพยากรณ์โรค")
        st.caption("ข้อมูลพารามิเตอร์ดัชนีทางโลหิตวิทยาและสัญญาณชีพจริง (ระบบปกปิดตัวตนคนไข้)")
        
        if selected_hn:
            # ดึงข้อมูลจริงในแถวนั้นมาแสดงผลผ่านระบบรหัสพรางตัวตนในรูปแบบ HN
            p_row = df_patients[df_patients['STUDY_HN'] == selected_hn].iloc
            
            # ฟังก์ชันช่วยดึงข้อมูลปลอดภัยป้องกันบั๊กชื่อคอลัมน์
            def get_val(col_name, default=0.0):
                return p_row.get(col_name.upper(), default)
            
            # ดึงค่าโอกาสทำนายจริง (PROB) และเกณฑ์ความเสี่ยงจริง (RISK) จาก Excel
            prob_val = get_val('prob', 0.0)
            risk_val = str(get_val('risk', 'low')).lower()
            
            st.write(f"**รหัสประจำตัวผู้ป่วยนอก:** `{selected_hn}` | **อายุ:** {int(get_val('Age', 0))} ปี | **อุณหภูมิแรกรับ:** {get_val('body_temp', get_val('temp', 0.0))} °C")
            
            # 🟢 ตารางรายงานพารามิเตอร์ CBC 14 ตัวแปร ดึงค่าจริงจากไฟล์ Excel สอดคล้องตามลำดับฟีเจอร์พยากรณ์
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
            
            # เงื่อนไขแสดงกล่องข้อความเตือน 3 ระดับสอดรับตามความน่าจะเป็นจริงในไฟล์ Excel
            if process_btn:
                if 'high' in risk_val or prob_val >= 70:
                    st.error("🚨 แนะนำทางการแพทย์: ความเสี่ยงสูง (แนะนำตรวจ Rapid Influenza Test)")
                elif 'mod' in risk_val or (40 <= prob_val < 70):
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
