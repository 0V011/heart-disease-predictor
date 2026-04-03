# utils.py - 数据库和工具函数
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import io
import time   # 备用

# 建表，如果不存在的话
def init_db():
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp TEXT,
            age INTEGER, sex INTEGER, cp INTEGER,
            trestbps INTEGER, chol INTEGER, fbs INTEGER,
            restecg INTEGER, thalach INTEGER, exang INTEGER,
            oldpeak REAL, slope INTEGER, ca INTEGER, thal INTEGER,
            risk_prob REAL, risk_class INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    # print("数据库初始化完成")  # 调试

# 存一次预测记录
def save_prediction(uname, input_df, proba, pred_class):
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO predictions (
            username, timestamp, age, sex, cp, trestbps, chol, fbs,
            restecg, thalach, exang, oldpeak, slope, ca, thal,
            risk_prob, risk_class
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        uname, datetime.now().isoformat(),
        input_df['age'][0], input_df['sex'][0], input_df['cp'][0],
        input_df['trestbps'][0], input_df['chol'][0], input_df['fbs'][0],
        input_df['restecg'][0], input_df['thalach'][0], input_df['exang'][0],
        input_df['oldpeak'][0], input_df['slope'][0], input_df['ca'][0],
        input_df['thal'][0], proba, pred_class
    ))
    conn.commit()
    conn.close()
    # print(f"已保存 {uname} 的预测记录")  # 调试

# 查某用户的历史记录（按时间倒序）
def get_user_history(uname):
    conn = sqlite3.connect('history.db')
    df = pd.read_sql_query(
        "SELECT timestamp, risk_prob, risk_class FROM predictions WHERE username = ? ORDER BY timestamp DESC",
        conn, params=(uname,)
    )
    conn.close()
    return df

# 导出 CSV
def export_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# 导出 PDF，简陋版
def export_to_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    w, h = letter
    c.drawString(100, h - 50, "心脏病风险预测历史报告")
    y = h - 80
    for i, row in df.iterrows():
        if y < 50:
            c.showPage()
            y = h - 50
        text = f"{row['timestamp']} | 风险概率: {row['risk_prob']:.2%} | 结果: {'有风险' if row['risk_class']==1 else '无风险'}"
        c.drawString(50, y, text[:100])
        y -= 20
    c.save()
    buffer.seek(0)
    return buffer

tmp = 0  # 临时变量
