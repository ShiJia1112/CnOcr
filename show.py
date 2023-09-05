from flask import Flask, jsonify, request
import mysql.connector
import qrcode
import json

app = Flask(__name__)

# # MySQL数据库配置
# db_config = {
#     'host': 'rm-2zes377d5erb8201ubo.mysql.rds.aliyuncs.com',
#     'user': 'cxsj_dev',
#     'password': '123456',
#     'database': 'cxsj_admin_dev'
# }
#
# # @app.route('/image/<filename>')
# # def get_image(filename):
# #     return send_from_directory('path_to_image_folder', filename)
#
#
# # 查询灭菌凭条类型
# @app.route('/api/dictionary', methods=['GET'])
# def api_show_dictionary():
#     data = request.json  # 获取JSON数据
#     parent_id = data.get('parent_id')
#
#     try:
#         parent_id = int(parent_id)  # 尝试将字符串转换为整数
#     except ValueError:
#         return jsonify({"error": "parent_id 必须是数字。"}), 400
#
#     # 连接到数据库
#     db = mysql.connector.connect(**db_config)
#     cursor = db.cursor(dictionary=True)
#
#     # 查询第一级数据（根据 parent_id 进行查询）
#     query_first_level = f"SELECT * FROM ledger_dictionary_py WHERE parent_id = {parent_id}"
#     cursor.execute(query_first_level)
#     first_level_items = cursor.fetchall()
#
#     # 查询第二级数据（根据第一级数据的 id 进行查询）
#     for item in first_level_items:
#         query_second_level = f"SELECT * FROM ledger_dictionary_py WHERE parent_id = {item['id']}"
#         cursor.execute(query_second_level)
#         second_level_items = cursor.fetchall()
#         item['children'] = second_level_items
#
#     # 关闭数据库连接
#     db.close()
#
#     return jsonify(first_level_items), 200
#
#
# # 查询列表收据
# @app.route('/api/receipts', methods=['GET'])
# def api_show_receipts():
#     # 连接到数据库
#     db = mysql.connector.connect(**db_config)
#     cursor = db.cursor(dictionary=True)
#
#     # 查询数据库表
#     query = "SELECT * FROM ledger_receipts_py"
#     cursor.execute(query)
#     receipts = cursor.fetchall()
#
#     # 关闭数据库连接
#     db.close()
#
#     return jsonify(receipts), 200



# 要生成二维码的文本
text_to_encode = "让你扫你就扫啊，傻不傻，缺乏防范意识！！！"

# 创建QR码对象
qr = qrcode.QRCode(
    version=1,  # 版本号，通常为1
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # 错误纠正级别
    box_size=10,  # 每个小格子的像素大小
    border=4,  # 边框大小，推荐为4
)

# 将文本添加到QR码对象中
qr.add_data(text_to_encode)
qr.make(fit=True)

qr_img = qr.make_image(fill_color="black", back_color="white")

# 保存QR码图像到文件
qr_img.save("qr_code.png")

qr_img.show()


if __name__ == '__main__':
    app.run(debug=True)
