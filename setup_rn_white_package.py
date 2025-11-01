#!/usr/bin/env python3
# setup_rn_white_package.py - 只保留白包逻辑的RN项目创建脚本
import os
import subprocess
import json
import re
import shutil
import random
import string
from pathlib import Path
from typing import Dict, Any

# =================== 模板代码 ===================

APP_TSX_WHITE = '''/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */

import {{ StatusBar, StyleSheet }} from 'react-native';
import WebView from 'react-native-webview';
import {{ useEffect, useRef }} from 'react';
import Orientation from 'react-native-orientation-locker';
import {{ SafeAreaView }} from 'react-native-safe-area-context';

function App() {{
  // @ts-ignore
  const objRef = useRef();
  // 修改页面方向
  Orientation.lockToLandscape();

  useEffect(() => {{
  }}, []);

  return (
    <SafeAreaView style={{styles.container}}>
      <StatusBar hidden={{true}} />
      <WebView
        source={{{{
          uri: '{GAME_URL}',
        {{{{
        style={{styles.container}}
      />
    </SafeAreaView>
  );
}}

const styles = StyleSheet.create({{
  container: {{
    flex: 1,
  }},
}});

export default App;
'''

PACKAGE_JSON_DEPENDENCIES = {
    "dependencies": {
        "@react-native/new-app-screen": "0.81.1",
        "axios": "^1.11.0",
        "react": "19.1.0",
        "react-native": "0.81.1",
        "react-native-orientation-locker": "^1.7.0",
        "react-native-safe-area-context": "^5.5.2",
        "react-native-webview": "^13.16.0"
    }
}

# =================== 验证函数 ===================
def validate_environment():
    """验证必需的工具是否可用"""
    required_tools = ['node', 'npm', 'npx']
    missing_tools = []
    
    for tool in required_tools:
        if not shutil.which(tool):
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ 缺少必需工具: {', '.join(missing_tools)}")
        print("请先安装 Node.js (https://nodejs.org/)")
        return False
    
    print("✅ 环境检查通过")
    return True

def validate_inputs(app_name: str, package_name: str) -> bool:
    """验证输入格式"""
    # 验证应用名称格式
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', app_name):
        print("❌ 应用名称格式错误！只能包含字母、数字、下划线和连字符，且必须以字母开头")
        return False
    
    # 验证包名格式
    if not re.match(r'^[a-z][a-z0-9_]*(\.{1}[a-z][a-z0-9_]*)+$', package_name):
        print("❌ 包名格式错误！请使用标准格式，如 com.company.app")
        return False
    
    return True

def generate_random_package_name() -> str:
    """生成随机包名，格式：com.xxx.xxx，确保是标准的三层结构"""
    def generate_random_part(max_length: int = 6) -> str:
        # 确保第一个字符是字母，后续可以是字母或数字
        length = random.randint(3, max_length)  # 至少3个字符
        first_char = random.choice(string.ascii_lowercase)
        remaining_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length-1))
        return first_char + remaining_chars
    
    # 确保生成标准的三层包结构 com.company.app
    company_name = generate_random_part()
    app_name = generate_random_part()
    package_name = f"com.{company_name}.{app_name}"
    
    print(f"📦 自动生成包名: {package_name}")
    return package_name

# =================== 主函数 ===================
def main():
    print("🚀 开始创建 RN 白包项目")
    
    # 环境预检查
    if not validate_environment():
        return

    app_name = input("请输入应用名称（项目目录名）: ").strip()
    package_name = generate_random_package_name()
    
    # 输入验证
    if not validate_inputs(app_name, package_name):
        return
    
    lock_landscape = input("是否锁定横屏? (y/N): ").strip().lower() in ['y', 'yes']

    game_url = "https://storage.y8.com/y8-studio/html5/Playgama/fruity_match/?key=y8&value=default"
    game_url_input = input(f"游戏 URL (回车使用默认): ")
    if game_url_input.strip():
        game_url = game_url_input

    project_path = Path(app_name)
    if project_path.exists():
        print(f"❌ 目录 {app_name} 已存在，请删除或换名")
        return

    # 1. 创建项目
    print(f"\n🔧 创建 React Native 项目: {app_name}")
    try:
        # 使用 shell=True 确保在 Windows 上正确执行
        cmd = f'npx @react-native-community/cli init {app_name} --package-name {package_name}'
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建项目失败: {e}")
        return
    except FileNotFoundError:
        print("❌ 找不到 npx 命令，请确保 Node.js 已正确安装并添加到 PATH")
        return

    os.chdir(app_name)

    # 2. 写入 package.json 依赖
    print("\n📦 安装依赖...")
    with open('package.json', 'r') as f:
        pkg = json.load(f)

    pkg["dependencies"].update(PACKAGE_JSON_DEPENDENCIES["dependencies"])
    with open('package.json', 'w') as f:
        json.dump(pkg, f, indent=2)

    try:
        subprocess.check_call("npm install", shell=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装依赖失败: {e}")
        return

    # 3. 写入 App.tsx
    print("\n📝 生成 App.tsx...")
    code = APP_TSX_WHITE.format(GAME_URL=game_url)
    with open('App.tsx', 'w') as f:
        f.write(code)

    # 4. 修复Android目录中的重复com文件夹问题
    print("\n🔧 检查并修复Android目录结构...")
    fix_android_package_structure(package_name, app_name)

    # 5. 添加Android权限
    print("\n🔒 添加Android权限...")
    add_android_permissions()

    # 6. 添加Gradle依赖
    print("\n📦 添加Gradle依赖...")
    add_gradle_dependencies()

    # 7. 完成
    print(f"""
🎉 项目创建完成！
📁 进入目录: cd {app_name}
📱 构建命令: npx react-native build-android
💡 注意检查: 签名文件、版本号、logo、RAM Bundle 是否生效
    """)


def fix_android_package_structure(package_name: str, app_name: str):
    """修复Android目录中的重复com文件夹问题"""
    import shutil
    
    # Android Java源码路径
    java_src_path = Path("android/app/src/main/java")
    if not java_src_path.exists():
        print("⚠️  Android源码目录不存在，跳过修复")
        return
    
    # 包名路径 components
    package_parts = package_name.split('.')
    
    # 检查是否存在重复的com文件夹结构
    # 正确的路径应该是: com/company/app/
    # 但可能出现: com/com.company.app/
    
    com_dir = java_src_path / "com"
    if not com_dir.exists() or not com_dir.is_dir():
        print("⚠️  Android目录结构异常，跳过修复")
        return
    
    # 获取com目录下的子目录
    com_subdirs = [d for d in com_dir.iterdir() if d.is_dir()]
    print(f"🔍 com目录下的子目录: {[d.name for d in com_subdirs]}")
    
    # 如果com目录下只有一个子目录，且名称包含点号，说明是错误的结构
    if len(com_subdirs) == 1:
        subdir_name = com_subdirs[0].name
        print(f"🔍 检查子目录: {subdir_name}")
        
        # 检查是否是错误的结构（子目录名包含点号，且与完整包名相同或相似）
        if '.' in subdir_name and (subdir_name == package_name or package_name.endswith(subdir_name)):
            # 错误的结构: com/com.company.app/
            print(f"🔄 检测到重复com文件夹结构，正在修复...")
            print(f"   错误路径: com/{subdir_name}/")
            print(f"   正确路径应该是: {'/'.join(['com'] + package_parts[1:])}/")
            
            # 创建正确的目录结构
            correct_path = com_dir
            try:
                for part in package_parts[1:]:  # 跳过第一个"com"
                    correct_path = correct_path / part
                    if not correct_path.exists():
                        correct_path.mkdir(parents=True, exist_ok=True)
                        print(f"   创建目录: {correct_path}")
            except Exception as e:
                print(f"❌ 创建目录失败: {e}")
                return
            
            # 移动文件到正确位置
            wrong_path = com_subdirs[0]
            correct_file_path = correct_path
            
            # 移动Java/Kotlin文件
            try:
                files_moved = 0
                for file in wrong_path.iterdir():
                    if file.is_file():
                        target_file = correct_file_path / file.name
                        print(f"   移动文件: {file.name} -> {target_file}")
                        shutil.move(str(file), str(target_file))
                        files_moved += 1
                
                # 删除错误的目录结构
                print(f"   删除错误目录: {wrong_path}")
                shutil.rmtree(str(wrong_path))
                
                print(f"✅ Android目录结构修复完成，共移动 {files_moved} 个文件")
            except Exception as e:
                print(f"❌ 移动文件时出错: {e}")
            return
        else:
            print(f"✅ 子目录 {subdir_name} 看起来是正确的")
    
    print("✅ Android目录结构正常，无需修复")


def add_android_permissions():
    """在AndroidManifest.xml中添加所需权限"""
    manifest_path = Path("android/app/src/main/AndroidManifest.xml")
    
    # 检查AndroidManifest.xml是否存在
    if not manifest_path.exists():
        print("⚠️  AndroidManifest.xml文件不存在，跳过权限添加")
        return
    
    # 需要添加的权限列表
    permissions = [
        '<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />',
        '<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />',
        '<uses-permission android:name="com.google.android.gms.permission.AD_ID" />',
        '<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />',
        '<uses-permission android:name="android.permission.INTERNET" />'
    ]
    
    try:
        # 读取AndroidManifest.xml内容
        # 首先尝试UTF-8编码，如果失败则尝试系统默认编码
        try:
            content = manifest_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = manifest_path.read_text()
        
        # 检查是否已经添加过这些权限
        permissions_added = 0
        for permission in permissions:
            # 提取权限名称进行检查
            permission_name = permission.split('"')[1]  # 提取android:name="..."中的内容
            if permission_name not in content:
                # 在<manifest>标签后添加权限（如果找不到<manifest>标签，则添加到文件开头）
                manifest_pos = content.find('<manifest')
                if manifest_pos != -1:
                    # 找到<manifest>标签后的第一个>字符
                    manifest_end_pos = content.find('>', manifest_pos)
                    if manifest_end_pos != -1:
                        # 在>后添加换行和权限
                        insert_pos = manifest_end_pos + 1
                        content = content[:insert_pos] + '\n    ' + permission + content[insert_pos:]
                        permissions_added += 1
                        print(f"✅ 添加权限: {permission_name}")
        
        if permissions_added > 0:
            # 写入更新后的内容
            # 使用UTF-8编码写入文件
            try:
                manifest_path.write_text(content, encoding='utf-8')
            except UnicodeEncodeError:
                # 如果UTF-8失败，使用系统默认编码
                manifest_path.write_text(content)
            print(f"✅ 成功添加 {permissions_added} 个权限到 AndroidManifest.xml")
        else:
            print("✅ 所需权限已存在，无需重复添加")
            
    except Exception as e:
        print(f"❌ 添加权限时出错: {e}")


def add_gradle_dependencies():
    """在build.gradle中添加所需依赖"""
    gradle_path = Path("android/app/build.gradle")
    
    # 检查build.gradle是否存在
    if not gradle_path.exists():
        print("⚠️  build.gradle文件不存在，跳过依赖添加")
        return
    
    # 需要添加的依赖项
    dependencies = [
        'implementation("androidx.appcompat:appcompat:1.7.1")',
        'implementation("com.google.android.material:material:1.13.0")',
        'implementation("androidx.activity:activity:1.11.0")',
        'implementation("androidx.constraintlayout:constraintlayout:2.2.1")',
        'implementation("com.google.code.gson:gson:2.13.2")',
        'implementation \'com.adjust.sdk:adjust-android:4.35.0\'',
        'implementation("com.android.installreferrer:installreferrer:2.2")',
        'implementation \'com.google.android.gms:play-services-ads-identifier:18.1.0\''
    ]
    
    try:
        # 读取build.gradle内容
        # 首先尝试UTF-8编码，如果失败则尝试系统默认编码
        try:
            content = gradle_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = gradle_path.read_text()
        
        # 查找dependencies块
        dependencies_pos = content.find("dependencies")
        if dependencies_pos == -1:
            print("❌ 未找到dependencies块，无法添加依赖")
            return
        
        # 查找dependencies块的开始大括号
        open_brace_pos = content.find("{", dependencies_pos)
        if open_brace_pos == -1:
            print("❌ 未找到dependencies块的开始大括号，无法添加依赖")
            return
        
        # 查找dependencies块的结束大括号
        close_brace_pos = open_brace_pos
        brace_count = 1
        for i in range(open_brace_pos + 1, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    close_brace_pos = i
                    break
        
        if brace_count != 0:
            print("❌ dependencies块格式错误，无法添加依赖")
            return
        
        # 检查是否已经添加过这些依赖
        dependencies_added = []
        for dep in dependencies:
            # 提取依赖的关键部分进行检查
            # 处理不同的引号格式
            dep_key = dep.split(' ')[0].replace('implementation', '').replace('(', '').replace(')', '').replace("'", '').replace('"', '').strip()
            if dep_key and dep_key not in content:
                dependencies_added.append(dep)
        
        if dependencies_added:
            # 在dependencies块中添加依赖项
            # 找到第一个依赖项的位置
            first_dep_pos = content.find("implementation", open_brace_pos)
            if first_dep_pos == -1 or first_dep_pos > close_brace_pos:
                # 如果没有找到现有的implementation，就在大括号后添加
                insert_pos = open_brace_pos + 1
            else:
                # 如果找到了现有的implementation，就在第一个依赖项前添加
                insert_pos = first_dep_pos
            
            # 构造要插入的依赖项内容
            dependencies_content = "\n    " + "\n    ".join(dependencies_added) + "\n\n"
            
            # 插入依赖项
            updated_content = content[:insert_pos] + dependencies_content + content[insert_pos:]
            
            # 写入更新后的内容
            # 使用UTF-8编码写入文件
            try:
                gradle_path.write_text(updated_content, encoding='utf-8')
            except UnicodeEncodeError:
                # 如果UTF-8失败，使用系统默认编码
                gradle_path.write_text(updated_content)
            print(f"✅ 成功添加 {len(dependencies_added)} 个依赖到 build.gradle")
            for dep in dependencies_added:
                print(f"   - {dep}")
        else:
            print("✅ 所需依赖已存在，无需重复添加")
            
    except Exception as e:
        print(f"❌ 添加依赖时出错: {e}")


if __name__ == "__main__":
    main()
