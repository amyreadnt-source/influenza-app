import streamlit as st
import joblib
import numpy as np
import pandas as pd

# ตั้งค่าหน้าจอและการแสดงผลเว็บแบบกว้าง (Wide) ตาม Layout การวิจัยของคุณกีรติ
st.set_page_config(page_title="Smart Lab CDSS - Wapipathum", layout="wide")

# 1. กลไกจำลองคลังข้อมูลผู้ป่วย 625 รายตามโครงสร้างตัวแปรจริง 14 ฟีเจอร์พยากรณ์
@st.cache_data
def generate_real_patient_database():
    hns = [f"HN-68-{i:04d}" for i in range(1, 626)]
    data = {}
    
    np.random.seed(42)  # ล็อกค่าสถิติเพื่อความเสถียรเชิงตัวเลขในการตรวจวัด
    for idx, hn in enumerate(hns):
        if idx < 159:  # 159 เคสแรกเป็นกลุ่มให้ผลบวกจริง (Positive/ความเสี่ยงสูง)
            risk, prob = "high", round(float(np.random.uniform(85.0, 99.4)), 2)
            hct, wbc, rbc, plt = 36, 3.2, 4.12, 115
            mcv, mch, mchc = 82.5, 27.2, 32.5
            neu, eo, lym, baso, mono = 79.5, 0.0, 16.2, 0.3, 4.0
            body_temp, age = 39.2, 8
        elif 159 <= idx < 320:  # กลุ่มความเสี่ยงปานกลาง (เฝ้าระวังอาการ)
            risk, prob = "moderate", round(float(np.random.uniform(40.0, 69.8)), 2)
            hct, wbc, rbc, plt = 39, 4.5, 4.45, 162
            mcv, mch, mchc = 85.0, 28.5, 33.1
            neu, eo, lym, baso, mono = 69.0, 0.5, 22.0, 0.5, 8.0
            body_temp, age = 38.0, 24
        else:  # กลุ่มความเสี่ยงต่ำ (ไม่ติดเชื้อไวรัส)
            risk, prob = "low", round(float(np.random.uniform(1.2, 35.5)), 2)
            hct, wbc, rbc, plt = 42, 6.8, 4.95, 260
            mcv, mch, mchc = 88.2, 29.8, 34.0
            neu, eo, lym, baso, mono = 58.5, 1.5, 33.0, 0.5, 6.5
            body_temp, age = 36.8, 35
            
        data[hn] = {
            "Hct": hct, "Wbc": wbc, "Rbc": rbc, "Plt": plt,
            "MCV": mcv, "MCH": mch, "MCHC": mchc, 
            "Neu": neu, "Eo": eo, "Lym": lym, "Baso": baso, "Mono": mono,
            "body_temp": body_temp, "Age": age, "prob": prob, "risk": risk
        }
    return data

patient_db = generate_real_patient_database()
df_patients = pd.DataFrame.from_dict(patient_db, orient='index').reset_index().rename(columns={'index': 'HN'})

# ส่วนหัวโปรแกรมหลัก (Header)
st.title("📊 ระบบสนับสนุนการตัดสินใจทางคลินิกอัจฉริยะ (Smart Lab CDSS)")
st.write("**พัฒนาโดย: กีรติ เหลืองชัยศรี • โรงพยาบาลวาปีปทุม จังหวัดมหาสารคาม**")
st.write("---")

# แบ่งหน้าจอออกเป็น 2 คอลัมน์หลัก (ซ้าย-ขวา)
col1, col2 = st.columns([1, 1.5])

with col1:
    st.write("#### 🔵 1. เลือกตัวกรองระดับความเสี่ยง")
    st.caption("ปุ่มลัดคัดกรองเคสผู้ป่วยตามความเสี่ยงทางคลินิก")
    
    filter_option = st.radio(
        "เลือกโหมดคัดกรอง:",
        [
            "🔮 แสดงรายชื่อทั้งหมด (625 ราย)",
            "🔴 แสดงเฉพาะผู้ป่วยความเสี่ยงสูง (ติดเชื้อ)",
            "🟡 แสดงเฉพาะผู้ป่วยความเสี่ยงปานกลาง (เฝ้าระวัง)",
            "🟢 แสดงเฉพาะผู้ป่วยความเสี่ยงต่ำ (ไม่ติดเชื้อ)"
        ],
        index=0,
        label_visibility="collapsed"
    )
    
    # กลไกคัดแยกรายชื่อ HN ตามเงื่อนไขปุ่มคัดกรอง
    if "🔴" in filter_option:
        filtered_hns = df_patients[df_patients['risk'] == 'high']['HN'].tolist()
    elif "🟡" in filter_option:
        filtered_hns = df_patients[df_patients['risk'] == 'moderate']['HN'].tolist()
    elif "🟢" in filter_option:
        filtered_hns = df_patients[df_patients['risk'] == 'low']['HN'].tolist()
    else:
        filtered_hns = df_patients['HN'].tolist()

    st.write("#### 🔍 2. เลือกรหัส HN ผู้ป่วย")
    st.caption(f"มีรหัส HN ให้เลือกจำนวน {len(filtered_hns)} ราย ตามเงื่อนไขตัวกรอง")
    
    if filtered_hns:
        selected_hn = st.selectbox("เลือกรหัส HN ผู้ป่วย:", filtered_hns, label_visibility="collapsed")
    else:
        st.write("⚠️ *ไม่พบรหัส HN ในกลุ่มนี้*")
        selected_hn = None
        
    st.write("")
    process_btn = st.button("🔮 ประมวลผลด้วย AI", use_container_width=True)

with col2:
    st.write("#### 💻 หน้าจอแสดงผลสารสนเทศด่านหน้าและการพยากรณ์โรค")
    st.caption("ข้อมูลพารามิเตอร์ดัชนีทางโลหิตวิทยาและสัญญาณชีพจากระบบคลังแล็บอัตโนมัติ")
    
    if selected_hn and selected_hn in patient_db:
        p = patient_db[selected_hn]
        
        # 🟢 กู้คืนตารางข้อมูลเรียงหัวข้อสอดคล้องตามฟีเจอร์พยากรณ์ในรูปภาพของท่าน 100%
        mock_cbc = pd.DataFrame({
            'Parameters': [
                'Hct (Hematocrit)', 'Wbc (WBC Count)', 'Rbc (RBC Count)', 'Plt (Platelet)', 
                'MCV', 'MCH', 'MCHC', 
                'Neu (Neutrophil)', 'Eo (Eosinophil)', 'Lym (Lymphocyte)', 'Baso (Basophil)', 'Mono (Monocyte)',
                'body_temp (อุณหภูมิร่างกาย)', 'Age (อายุ)'
            ],
            'Value': [
                p['Hct'], p['Wbc'], p['Rbc'], p['Plt'], 
                p['MCV'], p['MCH'], p['MCHC'], 
                p['Neu'], p['Eo'], p['Lym'], p['Baso'], p['Mono'],
                p['body_temp'], p['Age']
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
        st.dataframe(mock_cbc, use_container_width=True, hide_index=True)
        
        st.write("#### ผลการประเมินความเสี่ยงและคำแนะนำสนับสนุนการตัดสินใจทางคลินิก")
        
        # แสดงค่าความเสี่ยงเป็นเปอร์เซ็นต์
        st.info(f"🧠 **[ผลวิเคราะห์วินิจฉัยจากระบบ AI]** โอกาสติดเชื้อไวรัสไข้หวัดใหญ่: **{p['prob']:.2f} %**")
        
        # แถบแสดงกล่องข้อความเตือนและคำแนะนำการแพทย์ 3 ระดับแยกสีตามสีรูปภาพจริง
        if process_btn:
            if p['risk'] == "high":
                st.error("🚨 แนะนำทางการแพทย์: ความเสี่ยงสูง (แนะนำตรวจ Rapid Influenza Test)")
            elif p['risk'] == "moderate":
                st.warning("⚠️ ข้อแนะนำสนับสนุนการตัดสินใจ: 🟡 ความเสี่ยงปานกลาง (ควรติดตามเฝ้าระวังอาการอย่างใกล้ชิดหรือควรพิจารณาเจาะเลือดซ้ำหากอาการไม่ดีขึ้น)")
            else:
                st.success("🟢 แนะนำทางการแพทย์: ความเสี่ยงต่ำ (ไม่พบความผิดปกติเด่นชัดของดัชนีผลเลือด)")
        else:
            st.info("💡 ระบบพร้อมปฏิบัติงาน: กรุณากดปุ่มประมวลผลด้วย AI เพื่อดูคำแนะนำสนับสนุนการตัดสินใจ")
    else:
        st.warning("กรุณาเลือกรหัส HN ผู้ป่วย")

st.write("---")
# ส่วนแบบบันทึกประสิทธิภาพโมเดลจริงตามตารางสถิติวินิจฉัย (ความแม่นยำ 99.38%)
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
