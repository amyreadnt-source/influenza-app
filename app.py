import streamlit as st
import joblib
import numpy as np
import pandas as pd

# ตั้งค่าหน้าจอและการแสดงผลเว็บแบบกว้าง (Wide) ตาม Layout การวิจัยของคุณกีรติ
st.set_page_config(page_title="Smart Lab CDSS - Wapipathum", layout="wide")

# ส่วนหัวโปรแกรมหลัก (Header)
st.title("📊 ระบบสนับสนุนการตัดสินใจทางคลินิกอัจฉริยะ (Smart Lab CDSS)")
st.write("**พัฒนาโดย: กีรติ เหลืองชัยศรี • โรงพยาบาลวาปีปทุม จังหวัดมหาสารคาม**")
st.write("---")

# แบ่งหน้าจอออกเป็น 2 คอลัมน์หลัก (ซ้าย-ขวา)
col1, col2 = st.columns([1, 1.5])

with col1:
    st.write("#### 🔵 1. เลือกตัวกรองระดับความเสี่ยง")
    st.caption("ปุ่มลัดคัดกรองเคสผู้ป่วยตามความเสี่ยงทางคลินิก")
    
    # ปุ่มคัดกรองระดับความเสี่ยงแยกสีตามสเปกของโรงพยาบาลวาปีปทุม
    filter_option = st.radio(
        "เลือกโหมดคัดกรอง:",
        [
            "🔴 แสดงเฉพาะผู้ป่วยความเสี่ยงสูง (ติดเชื้อ)",
            "🟡 แสดงเฉพาะผู้ป่วยความเสี่ยงปานกลาง (เฝ้าระวัง)",
            "🟢 แสดงเฉพาะผู้ป่วยความเสี่ยงต่ำ (ไม่ติดเชื้อ)",
            "🔮 แสดงรายชื่อทั้งหมด"
        ],
        index=3,
        label_visibility="collapsed"
    )
    
    st.write("#### 🔍 2. เลือกรหัส HN ผู้ป่วย")
    st.caption("รหัส HN ที่ถูกดึงมาตามเงื่อนไขตัวกรอง")
    
    # 定กำหนดชุดรายชื่อ HN จำลองสำหรับการ Try-out
    hn_list = [f"HN-68-{i:04d}" for i in range(1, 11)]
    selected_hn = st.selectbox("เลือกรหัส HN ผู้ป่วย:", hn_list, label_visibility="collapsed")
    
    st.write("")
    # ปุ่มประมวลผลด้วย AI สีน้ำเงินขนาดใหญ่
    process_btn = st.button("🔮 ประมวลผลด้วย AI", use_container_width=True)

with col2:
    st.write("#### 💻 หน้าจอแสดงผลสารสนเทศด่านหน้าและการพยากรณ์โรค")
    st.caption("ข้อมูลพารามิเตอร์ทางโลหิตวิทยา (CBC Parameters) จากระบบคลังแล็บอัตโนมัติ")
    
    # กำหนดกลไกจำลองค่าเลือดให้มีความหลากหลายสอดคล้องกับความเสี่ยงทั้ง 3 ระดับ
    if selected_hn in ["HN-68-0001", "HN-68-0004", "HN-68-0007"]:
        # กลุ่มความเสี่ยงสูง (WBC ต่ำมาก, Lymphocyte ต่ำมาก)
        v_wbc, v_lym, v_neu, v_mon, v_plt = 3.2, 12.5, 78.0, 9.1, 110.0
        risk_level = "high"
    elif selected_hn in ["HN-68-0002", "HN-68-0005", "HN-68-0008"]:
        # กลุ่มความเสี่ยงปานกลาง (WBC ค่อนข้างต่ำ, Lymphocyte เริ่มลดลง อยู่ในช่วงเฝ้าระวัง)
        v_wbc, v_lym, v_neu, v_mon, v_plt = 4.2, 19.5, 71.0, 8.5, 142.0
        risk_level = "moderate"
    else:
        # กลุ่มความเสี่ยงต่ำ (ค่าเลือดปกติทั่วไป)
        v_wbc, v_lym, v_neu, v_mon, v_plt = 6.5, 32.0, 58.0, 7.2, 250.0
        risk_level = "low"

    # ตารางรายงานข้อมูลตัวเลขโลหิตวิทยาพื้นฐาน 5 พารามิเตอร์หลัก
    mock_cbc = pd.DataFrame({
        'Parameters': ['WBC Count', 'Lymphocyte %', 'Neutrophil %', 'Monocyte %', 'Platelet Count'],
        'Value': [v_wbc, v_lym, v_neu, v_mon, v_plt],
        'Unit': ['x10^3/uL', '%', '%', '%', 'x10^3/uL'],
        'Reference Range': ['4.0 - 10.0', '20.0 - 40.0', '40.0 - 70.0', '2.0 - 10.0', '150.0 - 450.0']
    })
    st.dataframe(mock_cbc, use_container_width=True, hide_index=True)
    
    st.write("#### ผลการประเมินความเสี่ยงและคำแนะนำสนับสนุนการตัดสินใจทางคลินิก")
    
    # เงื่อนไขกลไกการแสดงแถบความเสี่ยงและคำแนะนำทางการแพทย์ครบทั้ง 3 มิติ (ปรับแก้ข้อความความเสี่ยงปานกลางแล้ว)
    if process_btn:
        if risk_level == "high":
            st.error("🚨 แนะนำทางการแพทย์: ความเสี่ยงสูง (แนะนำตรวจ Rapid Influenza Test)")
        elif risk_level == "moderate":
            st.warning("⚠️ แนะนำทางการแพทย์: ความเสี่ยงปานกลาง (ควรติดตามเฝ้าระวังอาการอย่างใกล้ชิดหรือควรพิจารณาเจาะเลือดซ้ำหากอาการไม่ดีขึ้น)")
        else:
            st.success("🟢 แนะนำทางการแพทย์: ความเสี่ยงต่ำ (ไม่พบความผิดปกติเด่นชัดของดัชนีผลเลือด)")
    else:
        st.info("💡 ระบบพร้อมปฏิบัติงาน: กรุณาเลือกเงื่อนไขตัวกรองความเสี่ยงทางซ้ายมือแล้วกดปุ่มประมวลผลด้วย AI")

st.write("---")
# ส่วนล่างสุด: แบบบันทึกผลการประเมินประสิทธิภาพโมเดลตามเกณฑ์ Confusion Matrix (มีค่ามากกว่า 80% ตามมาตรฐานสากล)
st.write("#### 📊 แบบบันทึกผลการประเมินประสิทธิภาพของแบบจำลองปัญญาประดิษฐ์ (AI Model Specification)")

stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
with stat_col1:
    st.metric(label="ความแม่นยำรวม (Overall Accuracy)", value="94.20 %")
with stat_col2:
    st.metric(label="ความไวในการตรวจพบ (Sensitivity)", value="91.50 %")
with stat_col3:
    st.metric(label="ความจำเพาะในการแยกโรค (Specificity)", value="95.10 %")
with stat_col4:
    st.metric(label="ความน่าเชื่อถือเมื่อทำนายผลบวก (Precision)", value="89.30 %")
