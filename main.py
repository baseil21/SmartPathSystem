import streamlit as st
import pandas as pd
import os
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام المسار الذكي", layout="wide")

# إدارة البيانات
DB_FILE = "smart_data.csv"

def init_db():
    if not os.path.exists(DB_FILE):
        data = []
        for sec, count in [("قسم الخروج", 14), ("قسم الدخول", 14), ("قسم صالة القدوم", 8)]:
            for i in range(1, count + 1):
                dtype = "شحن" if i == 13 and sec != "قسم صالة القدوم" else "خاص" if i == 14 and sec != "قسم صالة القدوم" else "عادي"
                data.append({"القسم": sec, "المسار": i, "الحالة": "فارغ", "الموظف": "-", "النوع": dtype, "الوقت": "-", "البلاغ": "سليم"})
        pd.DataFrame(data).to_csv(DB_FILE, index=False)

init_db()

# نظام الدخول المباشر (تجنباً لخطأ الحساب غير نشط)
if 'user_auth' not in st.session_state: st.session_state.user_auth = None

if not st.session_state.user_auth:
    st.title("🔐 دخول النظام")
    u = st.text_input("المستخدم")
    p = st.text_input("الرمز", type="password")
    if st.button("دخول"):
        if u == "admin" and p == "123":
            st.session_state.user_auth = u
            st.rerun()
        else: st.error("بيانات خاطئة")
else:
    st.sidebar.write(f"المستخدم: {st.session_state.user_auth}")
    tab1, tab2 = st.tabs(["العمليات الميدانية", "التقارير والطباعة"])
    
    db = pd.read_csv(DB_FILE)

    with tab1:
        sec = st.radio("القسم:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"], horizontal=True)
        lanes = db[db['القسم'] == sec]
        cols = st.columns(4 if "صالة القدوم" in sec else 7)
        
        for i, (idx, row) in enumerate(lanes.iterrows()):
            with cols[i % (4 if "صالة القدوم" in sec else 7)]:
                # عرض البيانات بدون مباعدة أو زخرفة تسبب أخطاء
                st.info(f"{row['النوع']} {row['المسار']}\n({row['الموظف']})")
                
                if row["الحالة"] == "فارغ":
                    if st.button("استلام", key=f"in_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'الموظف'], db.at[idx, 'الوقت'] = "مشغول", st.session_state.user_auth, datetime.now().strftime("%H:%M")
                        db.to_csv(DB_FILE, index=False); st.rerun()
                elif row["الحالة"] == "مشغول":
                    if st.button("🚨 عطل", key=f"err_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'البلاغ'] = "عطل", "عطل فني"
                        db.to_csv(DB_FILE, index=False); st.rerun()
                    if st.button("تسليم", key=f"out_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'الموظف'] = "فارغ", "-"
                        db.to_csv(DB_FILE, index=False); st.rerun()
                elif row["الحالة"] == "عطل":
                    if st.button("إصلاح", key=f"fix_{idx}"):
                        db.at[idx, 'الحالة'], db.at[idx, 'البلاغ'] = "فارغ", "سليم"
                        db.to_csv(DB_FILE, index=False); st.rerun()

    with tab2:
        st.header(f"كروكي {sec} الرسمي")
        p_df = db[db['القسم'] == sec]
        st.table(p_df[['المسار', 'النوع', 'الحالة', 'الموظف', 'الوقت', 'البلاغ']])
        st.write("---")
        st.write(f"توقيع رئيس المناوبة: ........................ | الختم الرسمي للقسم: [ {sec} ]")
        st.caption("نصيحة: استخدم متصفح الجوال واضغط 'طباعة' لتحويل الصفحة لـ PDF")
