from flask import Flask, request, render_template, redirect, url_for, jsonify, session
import mysql.connector
from mysql.connector import cursor
import io
import requests
import cnocr
from PIL import Image
import qrcode
import jwt
import datetime
import secrets
import os
import json
import base64
import tempfile
from tempfile import NamedTemporaryFile
from io import BytesIO
from datetime import datetime
from cnocr import CnOcr

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
# app.config['TEMPLATES_AUTO_RELOAD'] = True
# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# app.config['JSON_AS_ASCII'] = False
# app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
# app.config['JSON_SORT_KEYS'] = False
# app.config['JSONIFY_MIMETYPE'] = 'application/json;charset=utf-8'

# 全局变量用于存储 image_path
global_image_path = None


@app.after_request
# 跨域不会报错
# ajax: No 'Access-Control-Allow-Origin' header is present on the requested
def cors(environ):
    environ.headers['Access-Control-Allow-Origin'] = '*'
    environ.headers['Access-Control-Allow-Method'] = '*'
    environ.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    return environ


# 加载CnOCR模型
cn_ocr = cnocr.CnOcr()

# MySQL数据库配置
db_config = {
    'host': 'rm-2zes377d5erb8201ubo.mysql.rds.aliyuncs.com',
    'user': 'cxsj_dev',
    'password': '123456',
    'database': 'cxsj_admin_dev'
}


def get_db_cursor():
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor(dictionary=True)
    return db, cursor


# 生成 Token
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token 有效期
    }
    token = jwt.encode(payload, 'your-secret-key', algorithm='HS256')
    return token


# 登录页面路由
@app.route('/api/login', methods=['POST'])
def api_login():
    db, cursor = get_db_cursor()
    data = request.json  # 获取JSON数据
    username = data.get('username')
    password = data.get('password')

    if not username:
        return jsonify({"error": "请输入用户名。", "code": 400}), 400
    if not password:
        return jsonify({"error": "请输入密码。", "code": 400}), 400
    # 查询数据库以验证用户
    query = f"SELECT * FROM ledger_users_py WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()

    if user:
        # 登录成功，执行其他操作
        token = generate_token(user['id'])
        return jsonify({"message": "登录成功", "code": 200, "token": token}), 200
    else:
        # 登录失败
        return jsonify({"error": "登录失败，请检查用户名和密码。", "code": 401}), 401


# 注册
@app.route('/api/register', methods=['POST'])
def api_register():
    db, cursor = get_db_cursor()
    data = request.json  # 获取JSON数据

    username = data.get('username')
    password = data.get('password')

    if not username:
        return jsonify({"error": "请输入用户名。", "code": 400}), 400
    if not password:
        return jsonify({"error": "请输入密码。", "code": 400}), 400

    # 查询数据库以验证用户名是否已存在
    query = f"SELECT * FROM ledger_users_py WHERE username = '{username}'"
    cursor.execute(query)
    existing_user = cursor.fetchone()

    if existing_user:
        return jsonify({"error": "用户名已经存在", "code": 400}), 400

    # 插入用户信息到数据库
    insert_query = "INSERT INTO ledger_users_py (username, password) VALUES (%s, %s)"
    data = (username, password)
    cursor.execute(insert_query, data)
    db.commit()

    token = generate_token(cursor.lastrowid)  # 获取插入的用户ID
    return jsonify({"message": "注册成功", "code": 200, "token": token}), 200


# 鉴权接口
@app.route('/api/protected', methods=['GET'])
def api_protected():
    token = request.headers.get('Authorization')  # 从请求头中获取 Token
    if not token:
        return jsonify({"error": "缺少身份验证信息", "code": 401}), 401

    try:
        payload = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
        user_id = payload['user_id']
        # 在这里可以使用 user_id 查询用户信息或执行其他操作
        return jsonify({"message": "鉴权通过", "code": 200}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token已过期", "code": 401}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "无效的Token", "code": 401}), 401


# 退出登录
@app.route('/api/logout', methods=['POST'])
def api_logout():
    # 清除用户的会话信息，可以根据实际情况进行调整
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({"message": "已成功退出登录", "code": 200}), 200


# @app.route('/api/upload', methods=['POST'])
# def api_upload():
#     global global_image_path
#     # 从POST请求中获取上传的图片文件
#     image_file = request.files.get('image')
#
#     if not image_file:
#         return jsonify({"error": "请选择要上传的图片。", "code": 400}), 400
#
#     # 获取上传的图片文件的扩展名
#     image_extension = image_file.filename.split('.')[(-1)].lower()
#
#     # 生成临时文件路径
#     image_path = 'temp_image.' + image_extension
#
#     # 保存上传的图片到临时文件
#     image_file.save(image_path)
#
#     # 返回上传成功的消息
#     response_data = {"message": "图片上传成功"}
#     return jsonify(response_data), 200
#
#
# def allowed_file(filename):
#     # 这个函数用于验证文件扩展名是否是允许的图像格式
#     allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
#
#
# @app.route('/api/ocr', methods=['POST'])
# def api_ocr():
#     db, curses = get_db_cursor()
#     # data = request.json
#     # dictionary = data.get("dictionary_id")
#     # id = data.get("id")
#     image_file = request.files.get('image')  # 获取上传的图片文件
#     id = request.form.get('id')  # 获取ID字段的值
#     # image_path = api_upload.image_path
#     # 初始化 recognized_text
#     recognized_text = ""
#     qr_image_data = ""
#     # 打开图片文件
#     if image_file and allowed_file(image_file.filename):
#         image_data = image_file.read()
#         image = Image.open(io.BytesIO(image_data))
#         # image = Image.open(image_file)
#
#         # 进行OCR识别
#         text = cn_ocr.ocr(image)
#
#         recognized_text = '\n'.join([''.join(line['text']) for line in text])
#
#         # 将上传的图片数据编码为 Base64 字符串
#         with open(image_file, 'rb') as img_file:
#             uploaded_image_data = img_file.read()
#         uploaded_image_base64 = base64.b64encode(uploaded_image_data).decode('utf-8')
#
#         # 存储识别日期
#         recognition_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#
#         # 生成二维码
#         qr = qrcode.QRCode(
#             version=5,
#             error_correction=qrcode.constants.ERROR_CORRECT_L,
#             box_size=5,
#             border=2,
#         )
#
#         qr.add_data(text)
#         qr.make(fit=True)
#
#         img = qr.make_image(fill_color='black', back_color='white')
#         img = img.convert("RGBA")
#
#         qr_image_path = 'temp_qr_image.png'
#         img.save(qr_image_path)
#
#         # 将生成的二维码图片转换为 Base64 编码
#         with open(qr_image_path, 'rb') as f:
#             qr_image_data = base64.b64encode(f.read()).decode('utf-8')
#
#         # 删除临时文件
#         os.remove(image_file)
#
#         # 将识别结果存储到数据库
#         insert_query = "INSERT INTO ledger_receipts_py (recognized_text, uploaded_image, recognition_date, qrcode, " \
#                         "dictionary_id) VALUES (%s, %s, %s, %s, %s)"
#         data = (recognized_text, uploaded_image_base64, recognition_date, qr_image_data, id)
#         cursor.execute(insert_query, data)
#         db.commit()
#
#         print("识别结果和上传的图片已存入数据库")
#
#         # 关闭数据库连接
#         db.close()
#
#     # 将识别的文字作为部分数据包含在返回的JSON中
#     response_data = {
#        "message": "图片上传和处理成功",
#        "recognized_text": recognized_text,  # 将识别的文字添加到返回数据中
#        "qr_image_data": qr_image_data
#     }
#
#     return jsonify(response_data), 200

@app.route('/api/upload', methods=['POST'])
def api_upload():
    db, cursor = get_db_cursor()  # 初始化数据库连接，确保有一个 get_db_cursor 函数
    # 获取上传的图片文件
    data = json.loads(request.data)
    image_path = data.get('image')
    dictionary_id = data.get("id")
    print(image_path, dictionary_id)

    if not image_path:
        return jsonify({"error": "请选择要上传的图片。", "code": 400}), 400

    # 发送HTTP请求并获取图像内容
    response = requests.get(image_path)
    if response.status_code != 200 or not response.content:
        return jsonify({"error": "无法获取图像。", "code": 400}), 400

    # 打开图片文件
    image = Image.open(BytesIO(response.content))

    # 进行OCR识别
    text = cn_ocr.ocr(image)
    # 获取识别到的文字信息
    recognized_text = '\n'.join([''.join(line['text']) for line in text])

    # 将上传的图片数据编码为 Base64 字符串
    image_data = BytesIO(response.content)
    uploaded_image_data = image_data.read()
    uploaded_image_base64 = base64.b64encode(uploaded_image_data).decode('utf-8')

    # 存储识别日期
    recognition_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 生成二维码
    qr = qrcode.QRCode(
        version=1,  # 使用合法的版本号，1到40之间
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    img = img.convert("RGBA")

    # 创建临时文件来保存二维码图像
    with NamedTemporaryFile(delete=True, suffix='.png') as qr_temp_file:
        img.save(qr_temp_file, 'PNG')
        qr_temp_file.seek(0)
        qr_image_data = base64.b64encode(qr_temp_file.read()).decode('utf-8')

    # 删除临时文件
    os.remove(qr_temp_file.name)

    # 将识别结果存储到数据库
    insert_query = "INSERT INTO ledger_receipts_py (recognized_text, uploaded_image, recognition_date, qrcode, " \
                   "dictionary_id) VALUES (%s, %s, %s, %s, %s)"
    data = (recognized_text, uploaded_image_base64, recognition_date, qr_image_data, dictionary_id)
    cursor.execute(insert_query, data)
    db.commit()

    print("识别结果和上传的图片已存入数据库")

    # 关闭数据库连接
    db.close()

    # 将识别的文字作为部分数据包含在返回的JSON中
    response_data = {
        "message": "图片上传和处理成功",
        "recognized_text": recognized_text,
        "qr_image_data": qr_image_data
    }

    return jsonify(response_data), 200



# 查询灭菌凭条类型
@app.route('/api/dictionary', methods=['GET'])
def api_show_dictionary():
    db, cursor = get_db_cursor()
    # 查询第一级数据
    query_first_level = "SELECT * FROM ledger_dictionary_py WHERE parent_id IS NULL OR parent_id = 0"
    cursor.execute(query_first_level)
    first_level_items = cursor.fetchall()

    result = []

    # 查询第二级数据
    for item in first_level_items:
        query_second_level = f"SELECT * FROM ledger_dictionary_py WHERE parent_id = {item['id']}"
        cursor.execute(query_second_level)
        second_level_items = cursor.fetchall()

        # 将第一级数据添加到结果中
        first_item = item.copy()
        first_item['children'] = []

        result.append(first_item)

        # 查询第三级数据
        for second_item in second_level_items:
            query_third_level = f"SELECT * FROM ledger_dictionary_py WHERE parent_id = {second_item['id']}"
            cursor.execute(query_third_level)
            third_level_items = cursor.fetchall()

            # 将第二级数据添加到第一级数据的 children 中
            second_item_copy = second_item.copy()
            second_item_copy['children'] = third_level_items

            first_item['children'].append(second_item_copy)

    cursor.close()
    db.close()

    result = {
        'code': 200,
        'data': result  # 将查询到的数据放在这里
    }
    return jsonify(result), 200


# 查询所有数据
@app.route('/api/queryAll', methods=['GET'])
def api_queryAll():
    db, cursor = get_db_cursor()
    dictionary_id = request.args.get("id")

    # 查询第一级数据
    query_first_level = "SELECT * FROM ledger_dictionary_py WHERE parent_id IS NULL OR parent_id = 0"
    cursor.execute(query_first_level)
    first_level_items = cursor.fetchall()

    result = []
    result1 = []

    # 查询第二级数据
    for item in first_level_items:
        query_second_level = f"SELECT * FROM ledger_dictionary_py WHERE parent_id = {item['id']}"
        cursor.execute(query_second_level)
        second_level_items = cursor.fetchall()

        # 将第一级数据添加到结果中
        first_item = item.copy()
        first_item['children'] = []

        result.append(first_item)

        # 查询第三级数据
        for second_item in second_level_items:

            query_third_level = """
                SELECT
                    r.`id`,
                    `recognized_text`,
                    `create_time`,
                    `uploaded_image`,
                    `recognition_date`,
                    `qrcode`,
                    `dictionary_id`,
                    d.name
                FROM
                    `ledger_receipts_py` r INNER JOIN ledger_dictionary_py d ON r.dictionary_id = d.id
            """

            if dictionary_id:
                query_third_level += f" WHERE dictionary_id = {dictionary_id}"
            cursor.execute(query_third_level)
            third_level_items = cursor.fetchall()

            # 将第二级数据添加到第一级数据的 children 中
            second_item_copy = second_item.copy()
            second_item_copy['children'] = third_level_items

            first_item['children'].append(second_item_copy)

            for third_item in third_level_items:
                # create_time_str = third_item['create_time']
                # parsed_create_time = datetime.strptime(create_time_str, "%a, %d %b %Y %H:%M:%S %Z")
                #
                # # 将解析后的日期时间对象添加到字典中
                # third_item['parsed_create_time'] = parsed_create_time

                # 拼接第二级和第三级 name，并设置为第三级的
                combined_name = f"{first_item['name']}-{second_item['name']}-{third_item['name']}"
                third_item['name'] = combined_name
                result1.append(third_item)

    cursor.close()
    db.close()

    result1 = {
        'code': 200,
        'data': result1  # 将查询到的数据放在这里
    }
    return jsonify(result1), 200


# 根据id查询灭菌类型具体名称
@app.route('/api/get_name_by_id', methods=['GET'])
def api_get_name_by_id():
    db, cursor = get_db_cursor()
    id = request.args.get("id")

    if id is None:
        return jsonify({"error": "未提供有效的id参数。", "code": 400}), 400

    try:
        typeid = int(id)  # 将字符串转换为整数
    except ValueError:
        return jsonify({"error": "id 必须是数字。", "code": 400}), 400

    query = "SELECT * FROM ledger_dictionary_py WHERE id = %s"
    cursor.execute(query, (typeid,))
    result = cursor.fetchone()

    cursor.close()
    db.close()

    if result:
        return jsonify({"code": 200, "data": result}), 200
    else:
        return jsonify({"error": "未找到对应的记录。", "code": 404}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000, host="192.168.1.31")
