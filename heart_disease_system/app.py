# 必须放在最前面！
import streamlit as st
st.set_page_config(page_title="❤️ 心脏病风险预测", page_icon="❤️", layout="wide")

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import time   # 未雨绸缪这一块
import warnings
warnings.filterwarnings('ignore')

# 导入认证和工具
import streamlit_authenticator as stauth
from auth_config import users, cookie, preauthorized_emails
from utils import init_db, save_prediction, get_user_history, export_to_csv, export_to_pdf

# 新特征和项目那个一致
def add_features(df_raw):
    df = df_raw.copy()
    df['age_group'] = pd.cut(df['age'], bins=[0,35,55,100], labels=['young','middle','senior'])
    df['bp_group'] = pd.cut(df['trestbps'], bins=[0,120,140,300], labels=['normal','pre_high','high'])
    df['chol_bp_ratio'] = df['chol'] / (df['trestbps'] + 1e-5)   # 加小量防除零
    df['hr_age_ratio'] = df['thalach'] / (df['age'] + 1e-5)
    df['bp_load'] = df['trestbps'] / (df['trestbps'] + 50)
    df['high_risk'] = ((df['bp_group'].astype(str) == 'high') & (df['chol'] > 240) & (df['exang'] == 1)).astype(int)
    df['age_group'] = df['age_group'].fillna('middle')
    df['bp_group'] = df['bp_group'].fillna('normal')
    df.fillna({'chol_bp_ratio':0, 'hr_age_ratio':0, 'bp_load':0, 'high_risk':0}, inplace=True)
    return df

# 数据库整个表
init_db()

# 用户认证部分
creds = {"usernames": users}
authenticator = stauth.Authenticate(
    creds,
    cookie["name"],
    cookie["key"],
    cookie["expiry_days"],
    preauthorized_emails
)

# 演示账号提示
st.info("📢 **Demo Account**\n\nUsername: `zhangsan`\nPassword: `123456`")

# 登录表单
authenticator.login(location='main')

# 从 session_state 拿登录信息
name = st.session_state.get('name')
auth_status = st.session_state.get('authentication_status')
uname = st.session_state.get('username')

if auth_status is False:
    st.error("用户名或密码错误 | Incorrect username or password")
    st.stop()
elif auth_status is None:
    st.warning("请输入用户名和密码 | Please enter username and password")
    st.stop()

# 登录成功
st.sidebar.write(f"欢迎，{name} | Welcome, {name}")
authenticator.logout("退出 | Logout", "sidebar")

# 页面样式（随便调的，感觉有点人机）
st.markdown("""
<style>
    .stButton>button { background-color: #ff4b4b; color: white; border-radius: 20px; padding: 0.5rem 1.5rem; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #ff6b6b; }
    .result-card { background-color: #f8f9fa; border-radius: 20px; padding: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.05); text-align: center; }
    .risk-low { color: #2ecc71; font-weight: bold; }
    .risk-medium { color: #f39c12; font-weight: bold; }
    .risk-high { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 模型加载，别问为什么
@st.cache_resource
def load_model():
    # 旧方法：每次重新加载，太慢，改成缓存
    # model = joblib.load('heart_model_pipeline.pkl')
    # return model
    return joblib.load('heart_model_pipeline.pkl')

model = load_model()
tmp = 0  # 临时变量，没用
# print("模型加载完成")，调试用

# 标题
st.title("❤️ 心脏病风险预测系统 | Heart Disease Risk Prediction System")
st.markdown("根据临床指标评估风险 | Assess risk based on clinical data")

# 输入表单
with st.form("pred_form"):
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("年龄 | Age", 20, 100, 50)
        sex = st.selectbox("性别 | Sex", ["男 | Male", "女 | Female"])
        cp = st.selectbox("胸痛类型 | Chest Pain Type", [1,2,3,4], format_func=lambda x: {1:"典型心绞痛 | Typical Angina",2:"非典型心绞痛 | Atypical Angina",3:"非心绞痛性胸痛 | Non-anginal Pain",4:"无症状 | Asymptomatic"}[x])
        trestbps = st.number_input("静息血压 (mm Hg) | Resting BP", 80, 200, 120)
        chol = st.number_input("胆固醇 (mg/dl) | Cholesterol", 100, 600, 200)
    with col2:
        fbs = st.selectbox("空腹血糖 > 120 | Fasting BS > 120", [0,1], format_func=lambda x: "是 | Yes" if x else "否 | No")
        restecg = st.selectbox("心电图结果 | Resting ECG", [0,1,2], format_func=lambda x: {0:"正常 | Normal",1:"ST-T异常 | ST-T Abnormality",2:"左心室肥大 | LVH"}[x])
        thalach = st.number_input("最大心率 | Max Heart Rate", 60, 220, 150)
        exang = st.selectbox("运动诱发心绞痛 | Exercise Angina", [0,1], format_func=lambda x: "是 | Yes" if x else "否 | No")
        oldpeak = st.number_input("ST段压低 | ST Depression", 0.0, 6.0, 1.0, 0.1)
    col3, col4 = st.columns(2)
    with col3:
        slope = st.selectbox("ST段斜率 | ST Slope", [1,2,3], format_func=lambda x: {1:"上斜 | Up",2:"平 | Flat",3:"下斜 | Down"}[x])
        ca = st.selectbox("主要血管数 | Major Vessels (0-3)", [0,1,2,3])
    with col4:
        thal = st.selectbox("地中海贫血类型 | Thalassemia", [3,6,7], format_func=lambda x: {3:"正常 | Normal",6:"可逆缺陷 | Reversible Defect",7:"固定缺陷 | Fixed Defect"}[x])
    
    sex_val = 1 if sex.startswith("男") else 0
    submitted = st.form_submit_button("🔍 开始预测 | Predict", use_container_width=True)

# 预测与保存
if submitted:
    input_df = pd.DataFrame({
        'age': [age], 'sex': [sex_val], 'cp': [cp], 'trestbps': [trestbps], 'chol': [chol],
        'fbs': [fbs], 'restecg': [restecg], 'thalach': [thalach], 'exang': [exang],
        'oldpeak': [oldpeak], 'slope': [slope], 'ca': [ca], 'thal': [thal]
    })
    # print(input_df.head())  # 临时看看输入
    with st.spinner("模型分析中 | Model analyzing..."):
        proba = model.predict_proba(input_df)[0][1]
        pred = 1 if proba > 0.5 else 0
        # print(f"概率: {proba}, 预测结果: {pred}")  # 调试
    # 存数据库
    save_prediction(uname, input_df, proba, pred)
    
    st.markdown("---")
    st.subheader("📊 预测结果 | Prediction Result")
    col_res1, col_res2, col_res3 = st.columns([1,2,1])
    with col_res2:
        if pred == 1:
            st.markdown('<div class="result-card"><h2 style="color:#e74c3c;">⚠️ 有心脏病风险 | Heart Disease Risk Detected</h2></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="result-card"><h2 style="color:#2ecc71;">✅ 无心脏病风险 | No Heart Disease Risk</h2></div>', unsafe_allow_html=True)
        st.write(f"**风险概率 | Risk Probability: {proba:.2%}**")
        st.progress(proba)
        if proba > 0.7:
            st.markdown('<p class="risk-high">🔴 高风险，建议就医检查 | High risk, medical consultation recommended</p>', unsafe_allow_html=True)
        elif proba > 0.3:
            st.markdown('<p class="risk-medium">🟡 中等风险，注意生活方式 | Moderate risk, healthy lifestyle advised</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="risk-low">🟢 低风险，保持健康习惯 | Low risk, maintain healthy habits</p>', unsafe_allow_html=True)

# 侧边栏：历史记录与导出
st.sidebar.markdown("## 📜 历史记录 | History")
if st.sidebar.button("查看我的预测历史 | View My History"):
    df_hist = get_user_history(uname)
    if df_hist.empty:
        st.sidebar.info("暂无历史记录 | No history records yet")
    else:
        st.sidebar.dataframe(df_hist)
        csv_data = export_to_csv(df_hist)
        st.sidebar.download_button("📥 下载 CSV | Download CSV", csv_data, "history.csv", "text/csv")
        pdf_buf = export_to_pdf(df_hist)
        st.sidebar.download_button("📄 下载 PDF | Download PDF", pdf_buf, "report.pdf", "application/pdf")

st.markdown("---")
st.caption("💡 本模型基于UCI心脏病数据集训练，仅供科研参考，不作为医疗诊断依据。 | Model trained on UCI Heart Disease dataset. For research purposes only, not a medical diagnostic tool.")
