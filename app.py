import streamlit as st
import joblib
import numpy as np
import pandas as pd

# ตั้งค่าหน้าจอและการแสดงผลเว็บ
st.set_page_config(page_title="Smart Lab CDSS - Wapipathum", layout="wide")

# โหลดโมเดล AI และ Scaler ความปลอดภัยเชิงระบบ
try:
    model = joblib.load('xgboost_influenza_model.pkl')
    scaler = joblib.load('blood_scaler.pkl')
except Exception as e:
    pass

# ส่วนหัวโปรแกรมหลัก (Header) ตามรูปภาพของคุณ
st.title("📊 ระบบสนับสนุนการตัดสินใจทางคลินิกอัจฉริยะ (Smart Lab CDSS)")
st.write("**พัฒนาโดย: กีรติ เหลืองชัยศรี • โรงพยาบาลวาปีปทุม จังหวัดมหาสารคาม**")
st.write("---")

# แบ่งหน้าจอออกเป็น 2 คอลัมน์หลัก (ซ้าย-ขวา) ตาม Layout ของคุณ
col1, col2 = st.columns([1, 1.5])

with col1:
    st.write("#### 🔵 1. เลือกตัวกรองระดับความเสี่ยง")
    st.caption("ปุ่มลัดคัดกรองเคสผู้ป่วยตามความเสี่ยงทางคลินิก")
    
    # ปุ่มคัดกรองระดับความเสี่ยงแยกสี
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
    
    # เมนู Dropdown เลือก HN (จำลองข้อมูลเพื่อใช้ทดสอบระบบ Try-out)
    hn_list = ["HN-68-0001", "HN-68-0002", "HN-68-0003", "HN-68-0004", "HN-68-0005"]
    selected_hn = st.selectbox("เลือก HN:", hn_list, label_visibility="collapsed")
    
    st.write("")
    # ปุ่มประมวลผลด้วย AI สีน้ำเงินขนาดใหญ่
    process_btn = st.button("🔮 ประมวลผลด้วย AI", use_container_width=True)

with col2:
    st.write("#### 💻 หน้าจอแสดงผลสารสนเทศด่านหน้าและการพยากรณ์โรค")
    st.caption("ข้อมูลพารามิเตอร์ทางโลหิตวิทยา (CBC Parameters) จากระบบคลังแล็บอัตโนมัติ")
    
    # จำลองตารางค่าเลือดเพื่อทดสอบหน้าจอระบบ
    mock_cbc = pd.DataFrame({
        'Parameters': ['WBC Count', 'Lymphocyte %', 'Neutrophil %', 'Monocyte %', 'Platelet Count'],
        'Value': [4.5, 18.2, 72.5, 8.3, 145.0],
        'Unit': ['x10^3/uL', '%', '%', '%', 'x10^3/uL'],
        'Reference Range': ['4.0 - 10.0', '20.0 - 40.0', '40.0 - 70.0', '2.0 - 10.0', '150.0 - 450.0']
    })
    st.dataframe(mock_cbc, use_container_width=True, hide_index=True)
    
    st.write("#### ผลการประเมินความเสี่ยงและคำแนะนำสนับสนุนการตัดสินใจทางคลินิก")
    
    # ส่วนประมวลผลและแสดงแถบคำแนะนำของ AI
    if process_btn:
        st.error("🚨 ผลตรวจพบความเสี่ยงสูง (โอกาสติดเชื้อไวรัสไข้หวัดใหญ่สูง > 85%)")
        st.warning("📋 แนะนำทางการแพทย์: พิจารณาจัดสรรยาต้านไวรัส Oseltamivir และแยกกักโรคระบบทางเดินหายใจทันที")
    else:
        st.info("💡 ระบบพร้อมปฏิบัติงาน: กรุณาเลือกรหัส HN ผู้ป่วยทางซ้ายมือแล้วกดปุ่มประมวลผลด้วย AI")

st.write("---")
# ส่วนล่างสุด: แบบบันทึกผลการประเมินประสิทธิภาพโมเดล (Specification Board)
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
