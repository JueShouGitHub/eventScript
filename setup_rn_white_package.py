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
from typing import Dict, Any, Optional

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

  Orientation.lockToLandscape();

  // useEffect(() => {{
  // }}, []);

  return (
    <SafeAreaView style={{styles.container}}>
      <StatusBar hidden={{true}} />
      <WebView
        source={{
          uri: '{GAME_URL}',
        }}
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
        "@react-native/new-app-screen": "0.82.1",
        "axios": "^1.11.0",
        "react": "19.1.1",
        "react-native": "0.82.1",
        "react-native-orientation-locker": "^1.7.0",
        "react-native-safe-area-context": "^5.5.2",
        "react-native-webview": "^13.16.0",
        "react-native-device-info": "^14.0.4",
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

    # 强制输入游戏URL
    game_url = ""
    while not game_url.strip():
        game_url = input("请输入游戏 URL: ").strip()
        if not game_url:
            print("❌ 游戏 URL 不能为空，请重新输入")

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

    # 7. 生成JKS签名文件
    print("\n🔐 生成JKS签名文件...")
    jks_info = generate_jks_file()
    if not jks_info:
        print("❌ JKS签名文件生成失败")
        return

    # 8. 配置签名到build.gradle
    print("\n🔧 配置签名文件...")
    if not configure_signing(jks_info):
        print("❌ 签名配置失败")
        return

    # 9. RN+Dex集成步骤
    print("\n🔧 RN+Dex集成步骤...")
    # 项目结构检查
    if not validate_project_structure("."):
        print("❌ 项目结构检查失败")
        return

    # Assets目录处理 (使用默认DEX文件路径)
    default_dex_path = str(Path(__file__).parent / "RN+Dex方案" / "app" / "assets" / "plugin_v1.dat")
    if not handle_assets_directory(".", default_dex_path):
        print("❌ Assets目录处理失败")
        return

    # Java代码部署
    if not deploy_java_files("."):
        print("❌ Java代码部署失败")
        return

    # AndroidManifest.xml配置
    if not update_android_manifest("."):
        print("❌ AndroidManifest.xml配置失败")
        return

    # 自定义插件处理 (生成随机名称)
    import random
    import string
    random_plugin_name = ''.join(random.choices(string.ascii_letters, k=1)).upper() + ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(7, 12)))
    random_module_name = ''.join(random.choices(string.ascii_letters, k=1)).upper() + ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(6, 10)))
    random_package_name = ''.join(random.choices(string.ascii_letters, k=1)).lower() + ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 9)))

    if not handle_custom_plugin(".", random_plugin_name, random_module_name, random_package_name):
        print("❌ 自定义插件处理失败")
        return

    # 10. 完成
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


def find_keytool() -> Optional[str]:
    """自动查找keytool命令的路径"""
    # 首先尝试直接使用keytool（如果在PATH中）
    if shutil.which('keytool'):
        return 'keytool'
    
    print("🔍 keytool不在PATH中，正在查找JDK安装路径...")
    
    # 常见的JDK安装路径
    common_jdk_paths = []
    
    # Windows常见路径
    if os.name == 'nt':
        # 从环境变量JAVA_HOME查找
        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            common_jdk_paths.append(Path(java_home) / 'bin' / 'keytool.exe')
        
        # 常见安装位置
        program_files = ['C:\\Program Files\\Java', 'C:\\Program Files (x86)\\Java']
        for pf in program_files:
            if os.path.exists(pf):
                for jdk_dir in Path(pf).glob('jdk*'):
                    common_jdk_paths.append(jdk_dir / 'bin' / 'keytool.exe')
        
        # Android Studio内置的JDK
        android_studio_paths = [
            Path.home() / 'AppData' / 'Local' / 'Android' / 'Sdk' / 'jdk',
            'C:\\Program Files\\Android\\Android Studio\\jbr\\bin\\keytool.exe',
        ]
        for as_path in android_studio_paths:
            if isinstance(as_path, Path):
                if as_path.exists():
                    for jdk_dir in as_path.glob('*'):
                        common_jdk_paths.append(jdk_dir / 'bin' / 'keytool.exe')
            else:
                common_jdk_paths.append(Path(as_path))
    else:
        # Linux/Mac路径
        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            common_jdk_paths.append(Path(java_home) / 'bin' / 'keytool')
        common_jdk_paths.extend([
            Path('/usr/bin/keytool'),
            Path('/usr/local/bin/keytool'),
        ])
    
    # 查找keytool
    for path in common_jdk_paths:
        if path.exists():
            print(f"✅ 找到keytool: {path}")
            return str(path)
    
    print("❌ 未找到keytool，请确保已安装JDK")
    return None


def generate_jks_file() -> Optional[dict]:
    """生成JKS签名文件并返回签名信息"""
    try:
        # 查找keytool路径
        keytool_path = find_keytool()
        if not keytool_path:
            print("❌ 无法找到keytool命令")
            print("💡 请安装JDK或设置JAVA_HOME环境变量")
            return None
        
        # 生成随机的JKS文件名（3-8个小写字母）
        jks_filename = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 8))) + '.jks'
        
        # 生成随机的alias（3-8个小写字母）
        key_alias = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
        
        # 固定密码
        store_password = '123456'
        key_password = '123456'
        
        # JKS文件路径（放在android/app目录下）
        jks_path = Path("android/app") / jks_filename
        
        # 生成随机的DN信息
        cn = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        ou = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        o = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        l = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        st = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        c = random.choice(['US', 'CN', 'JP', 'UK', 'DE', 'FR'])
        
        # 构建keytool命令
        dname = f"CN={cn}, OU={ou}, O={o}, L={l}, ST={st}, C={c}"
        keytool_cmd = [
            keytool_path,
            '-genkeypair',
            '-v',
            '-keystore', str(jks_path),
            '-alias', key_alias,
            '-keyalg', 'RSA',
            '-keysize', '2048',
            '-validity', '10000',
            '-storepass', store_password,
            '-keypass', key_password,
            '-dname', dname
        ]
        
        print(f"📝 JKS文件名: {jks_filename}")
        print(f"📝 密钥别名: {key_alias}")
        print(f"📝 密码: {store_password}")
        
        # 执行keytool命令
        result = subprocess.run(keytool_cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print(f"✅ JKS签名文件生成成功: {jks_path}")
            return {
                'filename': jks_filename,
                'alias': key_alias,
                'storePassword': store_password,
                'keyPassword': key_password
            }
        else:
            print(f"❌ keytool执行失败: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print("❌ 找不到keytool命令，请确保JDK已正确安装并添加到PATH")
        return None
    except Exception as e:
        print(f"❌ 生成JKS文件时出错: {e}")
        return None


def configure_signing(jks_info: dict) -> bool:
    """配置签名到build.gradle（强制覆盖原有配置）"""
    gradle_path = Path("android/app/build.gradle")
    
    if not gradle_path.exists():
        print("⚠️  build.gradle文件不存在，跳过签名配置")
        return False
    
    try:
        # 读取build.gradle内容
        try:
            content = gradle_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = gradle_path.read_text()
        
        # 删除原有的signingConfigs块（如果存在）
        if 'signingConfigs' in content:
            print("🔄 检测到原有签名配置，正在删除...")
            content = remove_signing_configs_block(content)
        
        # 构建新的signingConfigs配置
        signing_config = f'''    signingConfigs {{
        debug {{
            storeFile file('{jks_info["filename"]}')
            storePassword '{jks_info["storePassword"]}'
            keyAlias '{jks_info["alias"]}'
            keyPassword '{jks_info["keyPassword"]}'
        }}
        release {{
            storeFile file('{jks_info["filename"]}')
            storePassword '{jks_info["storePassword"]}'
            keyAlias '{jks_info["alias"]}'
            keyPassword '{jks_info["keyPassword"]}'
        }}
    }}

'''
        
        # 查找android块的位置
        android_pos = content.find('android {')
        if android_pos == -1:
            print("❌ 未找到android块，无法配置签名")
            return False
        
        # 在android块开始后插入signingConfigs
        insert_pos = content.find('\n', android_pos) + 1
        content = content[:insert_pos] + signing_config + content[insert_pos:]
        
        # 写入更新后的内容
        try:
            gradle_path.write_text(content, encoding='utf-8')
        except UnicodeEncodeError:
            gradle_path.write_text(content)
        
        print("✅ 签名配置完成（已覆盖原有配置）")
        return True
        
    except Exception as e:
        print(f"❌ 配置签名时出错: {e}")
        return False


def remove_signing_configs_block(content: str) -> str:
    """删除signingConfigs块"""
    import re
    
    # 使用正则表达式匹配并删除整个signingConfigs块
    # 匹配模式：signingConfigs { ... } （支持嵌套的大括号）
    pattern = r'\s*signingConfigs\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*'
    content = re.sub(pattern, '\n', content)
    
    return content



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
        'implementation \'com.google.android.gms:play-services-ads-identifier:18.1.0\'',
        'implementation("com.adjust.sdk:adjust-android:4.38.5")'
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


# =================== RN+Dex集成函数 ===================
def validate_project_structure(project_path: str) -> bool:
    """验证项目结构是否符合标准"""
    print("\n🔍 检查项目结构...")
    project = Path(project_path)

    # 检查android目录
    android_dir = project / "android"
    if not android_dir.exists() or not android_dir.is_dir():
        print("❌ 项目中未找到android目录")
        return False

    # 检查必要的Android文件
    required_files = [
        android_dir / "app" / "src" / "main" / "AndroidManifest.xml",
        android_dir / "app" / "build.gradle"
    ]

    for file_path in required_files:
        if not file_path.exists():
            print(f"❌ 未找到必需文件: {file_path}")
            return False

    print("✅ 项目结构检查通过")
    return True


def handle_assets_directory(project_path: str, dex_file_path: str) -> bool:
    """处理Assets目录，创建assets目录并复制DEX文件"""
    print("\n📁 处理Assets目录...")
    project = Path(project_path)
    android_assets_dir = project / "android" / "app" / "src" / "main" / "assets"

    try:
        # 创建assets目录（如果不存在）
        android_assets_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建assets目录: {android_assets_dir}")

        # 复制DEX文件到assets目录
        dex_file = Path(dex_file_path)
        target_dex_path = android_assets_dir / dex_file.name

        print(f"📋 复制DEX文件: {dex_file} -> {target_dex_path}")
        shutil.copy2(dex_file, target_dex_path)

        print("✅ Assets目录处理完成")
        return True
    except Exception as e:
        print(f"❌ Assets目录处理失败: {e}")
        return False


def deploy_java_files(project_path: str) -> bool:
    """部署Java代码文件到RN项目的android模块"""
    print("\n📱 部署Java代码文件...")
    project = Path(project_path)

    # 源文件路径（脚本所在目录的RN+Dex方案目录下）
    script_dir = Path(__file__).parent / "RN+Dex方案"
    source_java_dir = script_dir / "app" / "src" / "com" / "facebook" / "react"

    # 目标目录
    target_java_dir = project / "android" / "app" / "src" / "main" / "java" / "com" / "facebook" / "react"

    # 检查源文件目录是否存在
    if not source_java_dir.exists():
        print(f"❌ 源Java文件目录不存在: {source_java_dir}")
        return False

    try:
        # 创建目标目录（如果不存在）
        target_java_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目标Java目录: {target_java_dir}")

        # 需要复制的Java文件
        java_files = ["CryptoUtils.java", "IPluginActivity.java", "ProxyActivity.java"]

        # 复制文件
        for java_file in java_files:
            source_file = source_java_dir / java_file
            target_file = target_java_dir / java_file

            if source_file.exists():
                print(f"📋 复制Java文件: {java_file}")
                shutil.copy2(source_file, target_file)
            else:
                print(f"❌ 源文件不存在: {source_file}")
                return False

        print("✅ Java代码部署完成")
        return True
    except Exception as e:
        print(f"❌ Java代码部署失败: {e}")
        return False


def update_android_manifest(project_path: str) -> bool:
    """更新AndroidManifest.xml文件，注册ProxyActivity"""
    print("\n📝 更新AndroidManifest.xml...")
    project = Path(project_path)
    manifest_path = project / "android" / "app" / "src" / "main" / "AndroidManifest.xml"

    # ProxyActivity配置
    proxy_activity_config = '''
        <activity
            android:name="com.facebook.react.ProxyActivity"
            android:configChanges="keyboard|keyboardHidden|orientation|screenLayout|screenSize|smallestScreenSize|uiMode"
            android:exported="true"
            android:launchMode="singleTask"
            android:windowSoftInputMode="adjustResize" />'''

    try:
        # 读取AndroidManifest.xml内容
        # 首先尝试UTF-8编码，如果失败则尝试其他编码
        try:
            content = manifest_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试使用系统默认编码
            content = manifest_path.read_text()

        # 检查是否已经注册过
        if 'com.facebook.react.ProxyActivity' in content:
            print("✅ ProxyActivity已注册，无需重复注册")
            return True

        # 查找插入位置（在</application>标签前插入）
        insert_pos = content.rfind('</application>')
        if insert_pos == -1:
            print("❌ 未找到</application>标签，无法插入ProxyActivity配置")
            return False

        # 插入ProxyActivity配置
        updated_content = content[:insert_pos] + proxy_activity_config + '\n        ' + content[insert_pos:]

        # 写入更新后的内容
        # 使用UTF-8编码写入文件
        try:
            manifest_path.write_text(updated_content, encoding='utf-8')
        except UnicodeEncodeError:
            # 如果UTF-8失败，使用系统默认编码
            manifest_path.write_text(updated_content)
        print("✅ AndroidManifest.xml更新完成")
        return True
    except Exception as e:
        print(f"❌ AndroidManifest.xml更新失败: {e}")
        return False


def handle_custom_plugin(project_path: str, plugin_name: str, random_module_name: str, random_package_name: str) -> bool:
    """处理自定义插件"""
    print("\n🔧 处理自定义插件...")
    project = Path(project_path)

    try:
        # 创建随机模块目录
        random_module_dir = project / "android" / "app" / "src" / "main" / "java" / "com" / random_package_name.lower()
        random_module_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建随机模块目录: {random_module_dir}")

        # 创建随机模块Java文件（替换EventModule名称）
        random_module_content = f'''package com.{random_package_name.lower()};

import android.content.Intent;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import com.facebook.react.ProxyActivity;
import com.facebook.react.bridge.ReactApplicationContext;
import com.facebook.react.bridge.ReactContextBaseJavaModule;
import com.facebook.react.bridge.ReactMethod;

public class {random_module_name} extends ReactContextBaseJavaModule {{
    private final ReactApplicationContext reactContext;

    public {random_module_name}(@Nullable ReactApplicationContext reactContext) {{
        super(reactContext);
        this.reactContext = reactContext;
    }}

    @NonNull
    @Override
    public String getName() {{
        return "{random_module_name}";
    }}

    @ReactMethod
    public void jumpEvent(String url, String token) {{
        try {{
            reactContext.runOnUiQueueThread(() -> {{
                Intent intent = new Intent(reactContext, ProxyActivity.class);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                intent.putExtra("url", url);
                intent.putExtra("token", token);
                reactContext.startActivity(intent);
            }});
        }} catch (Exception e) {{
            //
        }}
    }}
}}
'''

        # 写入随机模块Java文件
        random_module_file = random_module_dir / f"{random_module_name}.java"
        random_module_file.write_text(random_module_content, encoding='utf-8')
        print(f"✅ 创建随机模块文件: {random_module_file}")

        # 创建随机包Java文件（替换MyAppPackage名称）
        random_app_package_content = f'''package com.{random_package_name.lower()};

import androidx.annotation.NonNull;
import com.facebook.react.ReactPackage;
import com.facebook.react.bridge.NativeModule;
import com.facebook.react.bridge.ReactApplicationContext;
import com.facebook.react.uimanager.ViewManager;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class {random_module_name}Package implements ReactPackage {{

    @NonNull
    @Override
    public List<ViewManager> createViewManagers(@NonNull ReactApplicationContext reactApplicationContext) {{
        return Collections.emptyList();
    }}

    @NonNull
    @Override
    public List<NativeModule> createNativeModules(@NonNull ReactApplicationContext reactContext) {{
        List<NativeModule> modules = new ArrayList<>();
        modules.add(new {random_module_name}(reactContext));
        return modules;
    }}
}}
'''

        # 写入随机包Java文件
        random_app_package_file = random_module_dir / f"{random_module_name}Package.java"
        random_app_package_file.write_text(random_app_package_content, encoding='utf-8')
        print(f"✅ 创建随机包文件: {random_app_package_file}")

        # 更新MainApplication文件，添加插件包（仅支持Kotlin版本）
        # 获取项目名称（从项目路径的最后一部分）
        project_name = project.name

        # 检查Kotlin版本的MainApplication（需要递归查找）
        main_application_kt_path = None
        java_dir = project / "android" / "app" / "src" / "main" / "java"

        # 递归查找MainApplication.kt文件
        for path in java_dir.rglob("MainApplication.kt"):
            main_application_kt_path = path
            print(f"🔍 找到MainApplication.kt文件: {path}")
            break

        if main_application_kt_path and main_application_kt_path.exists():
            # 处理Kotlin版本的MainApplication
            update_main_application_kotlin(main_application_kt_path, project_name, random_module_name, random_package_name)
        else:
            print("⚠️ 未找到MainApplication.kt文件，跳过更新")

        print("✅ 自定义插件处理完成")
        return True
    except Exception as e:
        print(f"❌ 自定义插件处理失败: {e}")
        return False


def update_main_application_kotlin(main_application_path, project_name, random_module_name, random_package_name):
    """更新Kotlin版本的MainApplication文件"""
    try:
        print(f"🔧 开始更新MainApplication.kt文件: {main_application_path}")
        # 读取MainApplication.kt内容
        main_app_content = main_application_path.read_text(encoding='utf-8')

        # 添加导入语句
        import_statement = f"import com.{random_package_name.lower()}.{random_module_name}Package\n"
        if f"import com.{random_package_name.lower()}.{random_module_name}Package" not in main_app_content:
            # 找到package语句后添加导入
            package_pos = main_app_content.find("package")
            if package_pos != -1:
                # 找到下一行的开始位置
                next_line_pos = main_app_content.find("\n", package_pos) + 1
                main_app_content = main_app_content[:next_line_pos] + import_statement + main_app_content[next_line_pos:]
                print(f"✅ 添加导入语句: {import_statement.strip()}")

        # 添加包到列表中
        if f"{random_module_name}Package()" not in main_app_content:
            # 查找注释位置
            comment_pos = main_app_content.find("// add(MyReactNativePackage())")
            if comment_pos != -1:
                # 在注释后添加包
                insert_pos = comment_pos + len("// add(MyReactNativePackage())")
                main_app_content = main_app_content[:insert_pos] + f"\n          add({random_module_name}Package())" + main_app_content[insert_pos:]
                print(f"✅ 添加插件包注册: {random_module_name}Package()")

        # 写入更新后的内容
        main_application_path.write_text(main_app_content, encoding='utf-8')
        print("✅ 更新MainApplication.kt文件")
    except Exception as e:
        print(f"❌ 更新MainApplication.kt文件失败: {e}")


if __name__ == "__main__":
    main()
