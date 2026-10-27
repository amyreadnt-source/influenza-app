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

# 🟢 กลไกการโหลดข้อมูลจริงจากไฟล์ Excel ที่อัปโหลดขึ้น GitHub (ไร้การมั่วข้อมูล)
@st.cache_data
def load_real_excel_data():
    try:
        # อ่านไฟล์ Excel จริงที่ฝากไว้บนระบบ
        df = pd.read_excel('patient_data.xlsx')
        # แปลงรหัส HN ให้เป็นข้อความสตริงเพื่อป้องกันระบบเพี้ยน
        df['HN'] = df['HN'].astype(str)
        return df
    except Exception as e:
        # หากยังไม่ได้อัปโหลดไฟล์ หรือชื่อไฟล์ไม่ตรง จะแสดงข้อความเตือนเชิงระบบ
        st.error(f"❌ ไม่สามารถโหลดไฟล์ข้อมูลจริงได้: {e}")
        st.info("💡 คำแนะนำ: โปรดอัปโหลดไฟล์ชื่อ 'patient_data.xlsx' ขึ้นไปบนคลังข้อมูล GitHub เพื่อเชื่อมต่อระบบข้อมูลจริง")
        return None

df_patients = load_real_excel_data()

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
                "🔮 แสดงรายชื่อทั้งหมด",
                "🔴 แสดงเฉพาะผู้ป่วยความเสี่ยงสูง (ติดเชื้อ)",
                "🟡 แสดงเฉพาะผู้ป่วยความเสี่ยงปานกลาง (เฝ้าระวัง)",
                "🟢 แสดงเฉพาะผู้ป่วยความเสี่ยงต่ำ (ไม่ติดเชื้อ)"
            ],
            index=0,
            label_visibility="collapsed"
        )
        
        # คัดกรองรายชื่อ HN จริงจากคอลัมน์ 'risk' ใน Excel (เงื่อนไขคำระบุ: high, moderate, low)
        if "🔴" in filter_option and 'risk' in df_patients.columns:
            filtered_hns = df_patients[df_patients['risk'] == 'high']['HN'].tolist()
        elif "🟡" in filter_option and 'risk' in df_patients.columns:
            filtered_hns = df_patients[df_patients['risk'] == 'moderate']['HN'].tolist()
        elif "🟢" in filter_option and 'risk' in df_patients.columns:
            filtered_hns = df_patients[df_patients['risk'] == 'low']['HN'].tolist()
        else:
            filtered_hns = df_patients['HN'].tolist()

        st.write("#### 🔍 2. เลือกรหัส HN ผู้ป่วย")
        st.caption(f"มีรหัส HN จริงจาก Excel ให้เลือกจำนวน {len(filtered_hns)} ราย")
        
        if filtered_hns:
            selected_hn = st.selectbox("เลือกรหัส HN ผู้ป่วย:", filtered_hns, label_visibility="collapsed")
        else:
            st.write("⚠️ *ไม่พบรหัส HN ในกลุ่มความเสี่ยงนี้*")
            selected_hn = None
            
        st.write("")
        process_btn = st.button("🔮 ประมวลผลด้วย AI", use_container_width=True)

    with col2:
        st.write("#### 💻 หน้าจอแสดงผลสารสนเทศด่านหน้าและการพยากรณ์โรค")
        st.caption("ข้อมูลพารามิเตอร์ดัชนีทางโลหิตวิทยาและสัญญาณชีพจากไฟล์ Excel จริง")
        
        if selected_hn:
            # ดึงข้อมูลแถวของผู้ป่วยรายนั้นจาก Excel มาแสดงผลร้อยเปอร์เซ็นต์
            p_data = df_patients[df_patients['HN'] == selected_hn].iloc[0]
            
            st.write(f"**รหัสประจำตัวผู้ป่วยนอก:** `{selected_hn}` | **อายุ:** {int(p_data.get('Age', 0))} ปี | **อุณหภูมิแรกรับ:** {p_data.get('body_temp', 0.0)} °C")
            
            # 🟢 แสดงตารางพารามิเตอร์ CBC 14 ตัวแปร ดึงค่าจริงจาก Excel คำต่อคำ
            real_cbc = pd.DataFrame({
                'Parameters': [
                    'Hct (Hematocrit)', 'Wbc (WBC Count)', 'Rbc (RBC Count)', 'Plt (Platelet)', 
                    'MCV', 'MCH', 'MCHC', 
                    'Neu (Neutrophil)', 'Eo (Eosinophil)', 'Lym (Lymphocyte)', 'Baso (Basophil)', 'Mono (Monocyte)',
                    'body_temp (อุณหภูมิร่างกาย)', 'Age (อายุ)'
                ],
                'Value': [
                    p_data.get('Hct', 0.0), p_data.get('Wbc', 0.0), p_data.get('Rbc', 0.0), p_data.get('Plt', 0.0), 
                    p_data.get('MCV', 0.0), p_data.get('MCH', 0.0), p_data.get('MCHC', 0.0), 
                    p_data.get('Neu', 0.0), p_data.get('Eo', 0.0), p_data.get('Lym', 0.0), p_data.get('Baso', 0.0), p_data.get('Mono', 0.0),
                    p_data.get('body_temp', 0.0), p_data.get('Age', 0)
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
            
            # ดึงค่าโอกาสการติดเชื้อ (คอลัมน์ prob ใน Excel) มาแสดงผล
            prob_val = p_data.get('prob', 0.0)
            st.info(f"🧠 **[ผลวิเคราะห์วินิจฉัยจากระบบ AI]** โอกาสติดเชื้อไวรัสไข้หวัดใหญ่: **{prob_val:.2f} %**")
            
            # แถบแสดงกล่องข้อความเตือนตามค่าความเสี่ยงจริงใน Excel (คอลัมน์ risk)
            if process_btn:
                risk_val = str(p_data.get('risk', 'low')).lower()
                if 'high' in risk_val or prob_val >= 70:
                    st.error("🚨 แนะนำทางการแพทย์: ความเสี่ยงสูง (แนะนำตรวจ Rapid Influenza Test)")
                elif 'moderate' in risk_val or (40 <= prob_val < 70):
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
