import streamlit as st
import joblib
import numpy as np
import pandas as pd

# 1. โหลดโมเดล XGBoost และ Scaler จากไฟล์ที่คุณเตรียมไว้
try:
    model = joblib.load('xgboost_influenza_model.pkl')
    scaler = joblib.load('blood_scaler.pkl')
except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการโหลดไฟล์กรุณาตรวจสอบชื่อไฟล์: {e}")

st.set_page_page_config(page_title="AI Influenza Predictor - Wapipathum", layout="centered")

st.title("🩺 ระบบสนับสนุนการตัดสินใจทำนายเชื้อไวรัสไข้หวัดใหญ่")
st.write("### โรงพยาบาลวาปีปทุม จังหวัดมหาสารคาม")
st.write("--- ข้อมูลระบบจำลองสำหรับทดสอบนวัตกรรม (Try-out) ---")

# 2. สร้างโครงสร้างรับข้อมูลทางคลินิก (ตัวอย่างฟีเจอร์พื้นฐาน)
st.sidebar.header("📊 ส่วนป้อนข้อมูลผู้ป่วย")
age = st.sidebar.number_input("อายุ (ปี)", min_value=0, max_value=120, value=25)
gender = st.sidebar.selectbox("เพศ", ["ชาย", "หญิง"])
temp = st.sidebar.number_input("อุณหภูมิร่างกายแรกรับ (°C)", min_value=35.0, max_value=42.0, value=37.5, step=0.1)

st.write("#### 🩸 ดัชนีทางโลหิตวิทยา (CBC Parameters)")
wbc = st.number_input("จำนวนเม็ดเลือดขาว (WBC Count x10^3/uL)", min_value=0.0, value=6.5, step=0.1)
lymph = st.number_input("เปอร์เซ็นต์ลิมโฟไซต์ (Lymphocyte %)", min_value=0.0, max_value=100.0, value=30.0, step=0.1)
plt = st.number_input("จำนวนเกล็ดเลือด (Platelet Count x10^3/uL)", min_value=0.0, value=250.0, step=1.0)

# 3. กระบวนการคำนวณเมื่อกดปุ่มทำนาย
if st.button("🚀 ประมวลผลและทำนายความเสี่ยง"):
    # แปลงเพศเป็นตัวเลข (ตัวอย่าง: ชาย=1, หญิง=0 ขึ้นอยู่กับการเทรนโมเดลเดิมของคุณ)
    gender_encoded = 1 if gender == "ชาย" else 0
    
    # รวมข้อมูลนำเข้าเป็นแถวตาราง (ลำดับตัวแปรต้องตรงกับตาราง Dataset ตอนเทรน)
    raw_features = np.array([[age, gender_encoded, temp, wbc, lymph, plt]])
    
    try:
        # ใช้ blood_scaler.pkl ปรับช่วงข้อมูลตัวเลขผลเลือดตามที่โมเดลต้องการ
        scaled_features = scaler.transform(raw_features)
        
        # ส่งให้โมเดล XGBoost คำนวณความน่าจะเป็น
        probability = model.predict_proba(scaled_features)[0][1] * 100
        prediction = model.predict(scaled_features)[0]
        
        # 4. ส่วนแสดงผลลัพธ์หน้าจอแสดงผลข้อมูล Dashboard
        st.write("---")
        st.subheader("📋 ผลการประเมินประสิทธิภาพโดยปัญญาประดิษฐ์")
        
        if probability >= 70:
            st.error(f"🔴 ความน่าจะเป็นในการติดเชื้อไวรัสไข้หวัดใหญ่สูง: {probability:.2f}%")
            st.warning("คำแนะนำทางการแพทย์: แนะนำตรวจ Rapid Influenza Test")
        elif 40 <= probability < 70:
            st.warning(f"🟡 ความน่าจะเป็นในการติดเชื้อไวรัสไข้หวัดใหญ่ปานกลาง: {probability:.2f}%")
        else:
            st.success(f"🟢 ความน่าจะเป็นในการติดเชื้อไวรัสไข้หวัดใหญ่ต่ำ: {probability:.2f}%")
            
    except Exception as e:
        st.error(f"เกิดความคลาดเคลื่อนในกระบวนการประมวลผลข้อมูล: {e}")
