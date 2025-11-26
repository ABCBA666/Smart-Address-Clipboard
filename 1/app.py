from flask import Flask, request, jsonify, render_template
import re
import os

app = Flask(__name__, template_folder='templates')

def extract_phone(text: str) -> tuple:
    """提取手机号"""
    phone_match = re.search(r'(1[3-9]\d{9})', text)
    if phone_match:
        return phone_match.group(1), text.replace(phone_match.group(1), '')
    return '', text

def extract_name(text: str) -> tuple:
    """提取姓名"""
    # 中文名2-4个字，或英文名（2-20个字母，可能有空格和点）
    name_match = re.search(r'^([\u4e00-\u9fa5]{2,4}|[A-Za-z\s.]{2,20})', text.strip())
    if name_match:
        name = name_match.group(1).strip()
        return name, text.replace(name, '', 1).strip()
    return '', text

def extract_address_components(address: str) -> dict:
    """提取地址各组成部分"""
    # 定义地址模式
    patterns = {
        'province': r'([^省]+省?|上海|北京|天津|重庆)',
        'city': r'([^市]+市|[^州]+州|[^盟]+盟|[^区]+区|.+区划)',
        'district': r'([^市]+市|[^区]+区|.+?[县旗]|.+?市|.+?区)',
        'street': r'([^路]+路|[^街]+街|[^道]+道|.+?镇|.+乡|.+街道)',
        'detail': r'(\d+[号-][^，,。.；;!！?？、\s]*)'
    }
    
    result = {}
    
    # 提取省市区等信息
    for key, pattern in patterns.items():
        match = re.search(pattern, address)
        if match:
            result[key] = match.group(1) if match.groups() else match.group(0)
            address = address.replace(result[key], '', 1).strip()
        else:
            result[key] = ''
    
    # 剩余部分作为详细地址补充
    if address:
        result['detail'] = (result.get('detail', '') + ' ' + address).strip()
    
    return result

def extract_address_info(address: str) -> dict:
    """
    从地址字符串中提取结构化信息
    
    Args:
        address: 包含姓名、电话和地址的字符串
        
    Returns:
        dict: 包含提取信息的字典
    """
    if not address or not isinstance(address, str):
        return {"error": "地址不能为空"}
    
    # 1. 提取手机号
    phone, remaining = extract_phone(address)
    
    # 2. 提取姓名
    name, remaining = extract_name(remaining)
    
    # 3. 提取地址信息
    address_info = extract_address_components(remaining)
    
    # 4. 组合结果
    result = {
        'name': name,
        'phone': phone,
        'province': address_info.get('province', ''),
        'city': address_info.get('city', ''),
        'district': address_info.get('district', ''),
        'street': address_info.get('street', ''),
        'detail': address_info.get('detail', '').strip()
    }
    
    # 5. 清理空值
    return {k: v for k, v in result.items() if v}

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    """API接口：提取地址信息"""
    try:
        data = request.get_json()
        if not data or 'address' not in data or not data['address'].strip():
            return jsonify({"error": "请输入有效的地址信息"}), 400
        
        result = extract_address_info(data['address'])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"处理地址时出错: {str(e)}"}), 500

if __name__ == '__main__':
    # 确保templates目录存在
    os.makedirs('templates', exist_ok=True)
    app.run(host='0.0.0.0', port=3067, debug=True)
