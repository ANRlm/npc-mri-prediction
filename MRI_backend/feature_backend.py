from flask import Flask, jsonify, send_file, request, session
import os
import glob
import json
from flask_cors import CORS
import pandas as pd
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime, timedelta
import jwt
import functools  # 确保导入这个模块

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 开启跨域并支持凭证
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')  # 用于JWT

# MongoDB连接
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['mri_database']  # 数据库名称
users_collection = db['users']  # 用户集合

# 默认输出文件目录
DEFAULT_OUTPUT_DIR = './data/16after/00C1068568/outline_original'

# JWT配置
JWT_SECRET = os.environ.get('JWT_SECRET', 'your_jwt_secret_here')
JWT_EXPIRATION = int(os.environ.get('JWT_EXPIRATION', 3600))  # 令牌过期时间(秒)


# 修复后的装饰器实现
def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': '需要授权令牌'}), 401

        # 移除Bearer前缀（如果存在）
        if token.startswith('Bearer '):
            token = token[7:]

        try:
            # 验证令牌
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            # 获取用户
            current_user = users_collection.find_one({'user_id': data['user_id']})
            if not current_user:
                raise Exception('用户不存在')
        except Exception as e:
            return jsonify({'error': f'无效的令牌: {str(e)}'}), 401

        # 将当前用户作为第一个参数传递给被装饰的函数
        return f(current_user, *args, **kwargs)

    return decorated


# 用户注册API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    # 验证请求数据
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': '用户名和密码是必填项'}), 400

    username = data['username']
    password = data['password']
    email = data.get('email', '')

    # 检查用户是否已存在
    if users_collection.find_one({'username': username}):
        return jsonify({'error': '用户名已存在'}), 409

    # 如果提供了邮箱，检查邮箱是否已被使用
    if email and users_collection.find_one({'email': email}):
        return jsonify({'error': '邮箱已被使用'}), 409

    # 创建新用户
    user = {
        'username': username,
        'password': generate_password_hash(password),
        'email': email,
        'created_at': datetime.utcnow(),
        'last_login': None,
        'active': True,
        'user_id': str(uuid.uuid4())
    }

    try:
        result = users_collection.insert_one(user)
        return jsonify({
            'message': '注册成功',
            'user_id': user['user_id']
        }), 201
    except Exception as e:
        return jsonify({'error': f'注册失败: {str(e)}'}), 500


# 用户登录API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    # 验证请求数据
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': '用户名和密码是必填项'}), 400

    username = data['username']
    password = data['password']

    # 查找用户
    user = users_collection.find_one({'username': username})

    # 验证用户和密码
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': '用户名或密码错误'}), 401

    # 更新最后登录时间
    users_collection.update_one(
        {'_id': user['_id']},
        {'$set': {'last_login': datetime.utcnow()}}
    )

    # 创建JWT令牌
    exp_time = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    payload = {
        'user_id': user['user_id'],
        'username': user['username'],
        'exp': exp_time
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')

    return jsonify({
        'message': '登录成功',
        'token': token,
        'expires_at': exp_time.isoformat(),
        'user': {
            'username': user['username'],
            'email': user.get('email', ''),
            'user_id': user['user_id']
        }
    })


# 获取用户信息API（需要授权）
@app.route('/api/user', methods=['GET'])
@token_required
def get_user_info(current_user):
    return jsonify({
        'user': {
            'username': current_user['username'],
            'email': current_user.get('email', ''),
            'user_id': current_user['user_id'],
            'created_at': current_user['created_at'],
            'last_login': current_user['last_login']
        }
    })


# 修改密码API（需要授权）
@app.route('/api/change_password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()

    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': '旧密码和新密码是必填项'}), 400

    # 验证旧密码
    if not check_password_hash(current_user['password'], data['old_password']):
        return jsonify({'error': '旧密码不正确'}), 401

    # 更新密码
    users_collection.update_one(
        {'_id': current_user['_id']},
        {'$set': {'password': generate_password_hash(data['new_password'])}}
    )

    return jsonify({'message': '密码修改成功'})


# 返回所有轮廓图像文件名的列表
@app.route('/api/images', methods=['GET'])
@token_required
def get_images(current_user):
    # Get output directory from query parameters or use default
    output_dir = request.args.get('output_dir', DEFAULT_OUTPUT_DIR)

    # Check if directory exists
    if not os.path.exists(output_dir):
        return jsonify({'error': f'Directory not found: {output_dir}'}), 404

    # Find all JPG images in the directory
    image_files = glob.glob(os.path.join(output_dir, 'contour_slice_*.jpg'))

    # Sort the image files by slice number
    image_files.sort(key=lambda x: int(os.path.basename(x).split('_')[2].split('.')[0]))

    # List to store image data
    image_data = []

    # Read each image file and convert to base64
    import base64
    for file_path in image_files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'rb') as img_file:
                # Read the file and encode as base64
                encoded_img = base64.b64encode(img_file.read()).decode('utf-8')
                # Add to the list
                image_data.append({
                    'filename': filename,
                    'slice_number': int(filename.split('_')[2].split('.')[0]),
                    'base64': f'data:image/jpeg;base64,{encoded_img}'
                })
        except Exception as e:
            print(f"Error encoding image {filename}: {str(e)}")
            # Add entry with error information
            image_data.append({
                'filename': filename,
                'slice_number': int(filename.split('_')[2].split('.')[0]),
                'error': str(e)
            })

    # 记录用户查看记录到MongoDB
    access_log = {
        'user_id': current_user['user_id'],
        'username': current_user['username'],
        'action': 'view_images',
        'directory': output_dir,
        'image_count': len(image_data),
        'timestamp': datetime.utcnow()
    }
    db['access_logs'].insert_one(access_log)

    return jsonify({
        'images': image_data,
        'count': len(image_data),
        'directory': output_dir
    })


# 从all_features.csv提取的特征数据
@app.route('/api/features', methods=['GET'])
@token_required
def get_features(current_user):
    # Get output directory from query parameters or use default
    output_dir = request.args.get('output_dir', DEFAULT_OUTPUT_DIR)

    # Construct file path
    file_path = os.path.join(output_dir, 'all_features.csv')

    # Check if file exists
    if not os.path.exists(file_path):
        return jsonify({'error': 'Features file not found'}), 404

    # Read CSV
    try:
        features_df = pd.read_csv(file_path)
        # Convert DataFrame to list of dictionaries (JSON compatible)
        features_data = features_df.to_dict(orient='records')

        # 记录用户查看记录到MongoDB
        access_log = {
            'user_id': current_user['user_id'],
            'username': current_user['username'],
            'action': 'view_features',
            'directory': output_dir,
            'feature_count': len(features_data),
            'timestamp': datetime.utcnow()
        }
        db['access_logs'].insert_one(access_log)

        return jsonify({
            'features': features_data,
            'count': len(features_data)
        })
    except Exception as e:
        return jsonify({'error': f'Error reading features file: {str(e)}'}), 500


# 返回flat_statistics.json中的统计分析
@app.route('/api/statistics', methods=['GET'])
@token_required
def get_statistics(current_user):
    # Get output directory from query parameters or use default
    output_dir = request.args.get('output_dir', DEFAULT_OUTPUT_DIR)

    # Construct file path
    file_path = os.path.join(output_dir, 'flat_statistics.json')

    # Check if file exists
    if not os.path.exists(file_path):
        return jsonify({'error': 'Statistics file not found'}), 404

    # Read JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            statistics_data = json.load(f)

        # 记录用户查看记录到MongoDB
        access_log = {
            'user_id': current_user['user_id'],
            'username': current_user['username'],
            'action': 'view_statistics',
            'directory': output_dir,
            'timestamp': datetime.utcnow()
        }
        db['access_logs'].insert_one(access_log)

        return jsonify(statistics_data)
    except Exception as e:
        return jsonify({'error': f'Error reading statistics file: {str(e)}'}), 500


from flask import abort, send_from_directory

# 假设文件存储在项目目录下的 `./files` 文件夹中
FILES_DIRECTORY = os.path.join(os.getcwd(), 'data/16after/00C1068568')

# 获取文件列表接口
@app.route('/api/get-file-list', methods=['GET'])
def get_file_list():
    try:
        # 读取文件夹中的文件
        files = os.listdir(FILES_DIRECTORY)
        file_urls = [f"http://localhost:5000/files/{file}" for file in files]
        return jsonify({"files": file_urls})
    except Exception as e:
        print(f"读取文件列表失败: {e}")
        abort(500, description="读取文件列表失败")

# 提供文件下载
@app.route('/files/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # 检查文件是否存在
        if not os.path.exists(os.path.join(FILES_DIRECTORY, filename)):
            abort(404, description="文件未找到")
        return send_from_directory(FILES_DIRECTORY, filename)
    except Exception as e:
        print(f"下载文件失败: {e}")
        abort(500, description="下载文件失败")



if __name__ == '__main__':
    # 确保索引存在
    users_collection.create_index('username', unique=True)
    users_collection.create_index('email', unique=True, sparse=True)
    users_collection.create_index('user_id', unique=True)

    app.run(debug=True, host='0.0.0.0', port=5000)