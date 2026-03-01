import streamlit as st
import pandas as pd
import os

# --- إعدادات رسمية ---
st.set_page_config(page_title="نظام المسار الذكي", layout="wide")

# --- إدارة البيانات ---
DB_FILE = "data_storage.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try: return pd.read_csv(DB_FILE).to_dict('records')
        except: pass
    initial = []
    for sec, count in [("قسم الخروج", 14), ("قسم الدخول", 14), ("قسم صالة القدوم", 8)]:
        for i in range(1, count + 1):
            dtype = "🚛 شحن" if i == 13 and sec != "قسم صالة القدوم" else "⭐ خاص" if i == 14 and sec != "قسم صالة القدوم" else "عادي"
            initial.append({"القسم": sec, "المسار": i, "الحالة": "فارغ", "الموظف": "-", "النوع": dtype})
    df = pd.DataFrame(initial)
    df.to_csv(DB_FILE, index=False)
    return initial

if 'main_db' not in st.session_state:
    st.session_state.main_db = load_data()

def save_db():
    pd.DataFrame(st.session_state.main_db).to_csv(DB_FILE, index=False)

# --- واجهة الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 بوابة المسار الذكي الرسمية")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "admin" and p == "123":
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("بيانات الدخول خاطئة")
else:
    st.sidebar.success("تم تسجيل الدخول: المسؤول")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()

    # تبويبات نصية رسمية بدون أي أيقونات
    tab1, tab2 = st.tabs(["العمليات الميدانية", "التقارير والطباعة"])
    
    with tab1:
        sec = st.radio("القسم الحالي:", ["قسم الخروج", "قسم الدخول", "قسم صالة القدوم"], horizontal=True)
        lanes = [r for r in st.session_state.main_db if r['القسم'] == sec]
        cols = st.columns(4 if "صالة القدوم" in sec else 7)
        
        for i, row in enumerate(lanes):
            with cols[i % (4 if "صالة القدوم" in sec else 7)]:
                # تحديد اللون بناءً على الحالة
                status_color = "#28a745" if row["الحالة"] == "مشغول" else "#dc3545" if row["الحالة"] == "عطل" else "#6c757d"
                
                # عرض الكبائن بشكل مبسط
                st.markdown(f"""
                <div style="background-color:{status_color}; color:white; padding:10px; border-radius:8px; text-align:center; margin-bottom:5px;">
                {row['النوع']} {row['المسار']}<br><b>{row['الموظف']}</b>
                </div>
                """, unsafe_allow_case=True)
                
                if row["الحالة"] == "فارغ":
                    if st.button("استلام", key=f"in_{sec}_{i}"):
                        row.update({"الحالة": "مشغول", "الموظف": "admin"})
                        save_db(); st.rerun()
                elif row["الحالة"] == "مشغول":
                    if st.button("🚨 عطل", key=f"err_{sec}_{i}"):
                        row.update({"الحالة": "عطل"})
                        save_db(); st.rerun()
                    if st.button("تسليم", key=f"out_{sec}_{i}"):
                        row.update({"الحالة": "فارغ", "الموظف": "-"})
                        save_db(); st.rerun()

    with tab2:
        st.header(f"📋 كروكي {sec} الرسمي")
        p_df = pd.DataFrame([r for r in st.session_state.main_db if r['القسم'] == sec])
        st.table(p_df[['المسار', 'النوع', 'الحالة', 'الموظف']])
