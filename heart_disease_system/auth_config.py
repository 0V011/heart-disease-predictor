# auth_config.py - 用户配置，折腾了半天
# 注意：密码是 bcrypt 哈希，别直接写明文

# 用户字典
users = {
    "zhangsan": {
        "name": "张三",
        # 密码哈希：123456 生成的，忘了的话重新生成，已经在页面进行提示
        "password": "$2b$12$3CzJiS/8IUkdk1Awy5KDmuoe3w5ODmj70WZWaBGwpj1nopsdLlhme"
    },
    "lisi": {
        "name": "李四",
        "password": "$2b$12$Lly/18rom0YMrLYuF.ytxutjrQteyzmyS4hlYzCQ/HLAy1smXhNku"
    }
}

# cookie 配置
cookie = {
    "expiry_days": 30,
    #key 
    "key": "a_random_long_string_here_123456",
    "name": "heart_disease_cookie"
}

# 预授权邮箱，暂时没用到
preauthorized_emails = []

# 调试用，看看用户加载了没
# print("auth_config 加载完成，用户列表:", list(users.keys()))
